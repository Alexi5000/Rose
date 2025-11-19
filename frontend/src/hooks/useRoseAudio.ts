/**
 * 🔊 Rose Audio Playback Hook
 *
 * Guarantees that Rose replies audibly by first trying streamed audio URLs and
 * falling back to the SpeechSynthesis API when needed. Adds emoji logs at every
 * critical step so failures are easy to trace.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  ANALYSER_FFT_SIZE,
  ANALYSER_SMOOTHING,
  AUDIO_DEFAULT_VOLUME,
  AUDIO_FETCH_TIMEOUT_MS,
  AUDIO_PLAYBACK_MAX_RETRIES,
  SPEECH_SYNTHESIS_LANGUAGE,
  SPEECH_SYNTHESIS_PITCH,
  SPEECH_SYNTHESIS_RATE,
} from '@/config/voice';
import { calculateRms, createPlaybackAnalyzer } from '@/lib/audio-utils';
import type { VoiceResponse } from '@/types/voice';

const SYNTHETIC_AMPLITUDE_BASE = 0.3;
const SYNTHETIC_AMPLITUDE_VARIATION = 0.2;
const SYNTHETIC_AMPLITUDE_PERIOD_MS = 160;
const PLAYBACK_TEXT_PREVIEW_CHARS = 24;
const AUDIO_FETCH_RETRY_DELAY_MS = 250;

const resolveAudioUrl = (audioUrl: string): string => {
  try {
    return new URL(audioUrl, window.location.origin).toString();
  } catch (error) {
    console.warn('⚠️ Failed to resolve audio URL, using raw value', audioUrl, error);
    return audioUrl;
  }
};

interface UseRoseAudioReturn {
  /** Whether Rose is currently speaking */
  isPlaying: boolean;
  /** Current Rose audio amplitude (0-1) */
  roseAmplitude: number;
  /** Play audio for Rose's latest response */
  playAudio: (response: VoiceResponse) => Promise<void>;
  /** Stop current audio playback */
  stopAudio: () => void;
  /** Current playback error */
  error: string | null;
}

interface UseRoseAudioProps {
  /** Callback when playback starts */
  onPlaybackStart?: () => void;
  /** Callback when playback ends */
  onPlaybackEnd?: () => void;
  /** Callback when error occurs */
  onError?: (error: string) => void;
}

export function useRoseAudio({
  onPlaybackStart,
  onPlaybackEnd,
  onError,
}: UseRoseAudioProps = {}): UseRoseAudioReturn {
  // 🎯 State
  const [isPlaying, setIsPlaying] = useState(false);
  const [roseAmplitude, setRoseAmplitude] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // 🔧 Refs
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const amplitudeModeRef = useRef<'idle' | 'analyser' | 'synthetic'>('idle');

  /**
   * 🔊 Analyze audio amplitude loop (runs at 60fps)
   */
  const analyzePlayback = useCallback(() => {
    if (amplitudeModeRef.current !== 'analyser' || !analyserRef.current) {
      return;
    }

    const analyser = analyserRef.current;
    const bufferLength = analyser.fftSize;
    const dataArray = new Float32Array(bufferLength);
    analyser.getFloatTimeDomainData(dataArray);

    // Calculate RMS amplitude
    const rms = calculateRms(dataArray);
    setRoseAmplitude(rms);

    // Continue loop
    animationFrameRef.current = requestAnimationFrame(analyzePlayback);
  }, []);

  /**
   * 🌊 Synthetic amplitude generator for SpeechSynthesis fallback
   */
  const runSyntheticAmplitude = useCallback(() => {
    if (amplitudeModeRef.current !== 'synthetic') {
      return;
    }

    const timeSeed = performance.now();
    const amplitude =
      SYNTHETIC_AMPLITUDE_BASE +
      SYNTHETIC_AMPLITUDE_VARIATION * Math.abs(Math.sin(timeSeed / SYNTHETIC_AMPLITUDE_PERIOD_MS));
    setRoseAmplitude(amplitude);
    animationFrameRef.current = requestAnimationFrame(runSyntheticAmplitude);
  }, []);

  const stopAmplitudeTracking = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    amplitudeModeRef.current = 'idle';
    setRoseAmplitude(0);
  }, []);

  const startAnalyserAmplitude = useCallback(() => {
    stopAmplitudeTracking();
    amplitudeModeRef.current = 'analyser';
    animationFrameRef.current = requestAnimationFrame(analyzePlayback);
  }, [analyzePlayback, stopAmplitudeTracking]);

  const startSyntheticAmplitude = useCallback(() => {
    stopAmplitudeTracking();
    amplitudeModeRef.current = 'synthetic';
    animationFrameRef.current = requestAnimationFrame(runSyntheticAmplitude);
  }, [runSyntheticAmplitude, stopAmplitudeTracking]);

  const stopSpeechSynthesis = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      console.log('🛑 SpeechSynthesis cancelled');
    }

    utteranceRef.current = null;
  }, []);

  const releaseAudioResources = useCallback(async () => {
    stopAmplitudeTracking();

    if (audioRef.current) {
      audioRef.current.onplay = null;
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }

    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }

    if (audioContextRef.current) {
      try {
        await audioContextRef.current.close();
      } catch (closeError) {
        console.warn('⚠️ Error while closing AudioContext:', closeError);
      }
      audioContextRef.current = null;
    }

    analyserRef.current = null;
  }, [stopAmplitudeTracking]);

  const waitForMetadata = useCallback((audio: HTMLAudioElement) => {
    return new Promise<void>((resolve, reject) => {
      const handleLoaded = () => {
        audio.removeEventListener('loadedmetadata', handleLoaded);
        audio.removeEventListener('error', handleError);
        console.log(`✅ Audio metadata loaded: duration=${audio.duration.toFixed(2)}s`);
        resolve();
      };

      const handleError = (event: Event) => {
        audio.removeEventListener('loadedmetadata', handleLoaded);
        audio.removeEventListener('error', handleError);
        console.error('❌ Failed to load Rose audio metadata', {
          event,
          currentSrc: audio.currentSrc,
        });
        reject(event);
      };

      audio.addEventListener('loadedmetadata', handleLoaded);
      audio.addEventListener('error', handleError);
      audio.load();
    });
  }, []);

  const fetchAudioBlob = useCallback(async (audioUrl: string): Promise<Blob> => {
    const resolvedUrl = resolveAudioUrl(audioUrl);
    console.log(`🌐 Fetching Rose audio from ${resolvedUrl}`);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), AUDIO_FETCH_TIMEOUT_MS);

    try {
      const response = await fetch(resolvedUrl, {
        signal: controller.signal,
        cache: 'no-store',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch audio (${response.status})`);
      }

      const contentType = response.headers.get('content-type');
      const blob = await response.blob();

      if (!blob.size) {
        throw new Error('Audio blob is empty');
      }

      let normalizedBlob = blob;
      if (!blob.type || blob.type === 'application/octet-stream') {
        console.warn('⚠️ Audio blob missing MIME type, forcing audio/mpeg', {
          reportedType: blob.type || 'unset',
          contentType,
        });
        normalizedBlob = blob.slice(0, blob.size, 'audio/mpeg');
      }

      console.log(`📥 Audio fetched ${(blob.size / 1024).toFixed(2)} KB`, {
        blobType: normalizedBlob.type || 'unknown',
        contentType,
      });
      return normalizedBlob;
    } finally {
      clearTimeout(timeoutId);
    }
  }, []);

  const playFromBlob = useCallback(
    async (blob: Blob): Promise<void> => {
      await releaseAudioResources();
      stopSpeechSynthesis();

      const objectUrl = URL.createObjectURL(blob);
      objectUrlRef.current = objectUrl;

      const audio = new Audio(objectUrl);
      audio.crossOrigin = 'anonymous';
      audio.preload = 'auto';
      audio.volume = AUDIO_DEFAULT_VOLUME;
      audioRef.current = audio;

      await waitForMetadata(audio);

      const { audioContext, analyser } = createPlaybackAnalyzer(
        audio,
        ANALYSER_FFT_SIZE,
        ANALYSER_SMOOTHING
      );

      if (audioContext.state === 'suspended') {
        console.log('⏯️ Resuming Rose AudioContext');
        await audioContext.resume();
      }

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      audio.onplay = () => {
        console.log('▶️ Rose audio playback started', {
          objectUrl,
          duration: audio.duration,
        });
        setIsPlaying(true);
        startAnalyserAmplitude();
        onPlaybackStart?.();
      };

      audio.onended = () => {
        console.log('🏁 Rose audio playback finished');
        setIsPlaying(false);
        stopAmplitudeTracking();
        onPlaybackEnd?.();
      };

      audio.onerror = (event) => {
        const mediaError = audio.error;
        console.error('❌ Audio element error', {
          event,
          code: mediaError?.code,
          message: mediaError?.message,
          currentSrc: audio.currentSrc,
          blobType: blob.type,
          blobSize: blob.size,
        });
        setError('Audio playback error');
        setIsPlaying(false);
        stopAmplitudeTracking();
        onError?.('Audio playback error');
      };

      await audio.play();
    },
    [
      ANALYSER_FFT_SIZE,
      ANALYSER_SMOOTHING,
      onError,
      onPlaybackEnd,
      onPlaybackStart,
      releaseAudioResources,
      startAnalyserAmplitude,
      stopAmplitudeTracking,
      stopSpeechSynthesis,
      waitForMetadata,
    ]
  );

  const speakWithSynthesis = useCallback(
    async (text: string) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
        throw new Error('Speech synthesis not supported');
      }

      stopSpeechSynthesis();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = SPEECH_SYNTHESIS_LANGUAGE;
      utterance.pitch = SPEECH_SYNTHESIS_PITCH;
      utterance.rate = SPEECH_SYNTHESIS_RATE;
      utteranceRef.current = utterance;

      startSyntheticAmplitude();
      setIsPlaying(true);
      onPlaybackStart?.();

      return await new Promise<void>((resolve, reject) => {
        utterance.onend = () => {
          console.log('🗣️ Speech synthesis finished');
          setIsPlaying(false);
          stopAmplitudeTracking();
          onPlaybackEnd?.();
          resolve();
        };

        utterance.onerror = (event) => {
          console.error('❌ Speech synthesis error', event);
          setIsPlaying(false);
          stopAmplitudeTracking();
          reject(new Error('Speech synthesis failed'));
        };

        console.log('🗣️ Speaking via SpeechSynthesis fallback');
        window.speechSynthesis.speak(utterance);
      });
    },
    [
      onPlaybackEnd,
      onPlaybackStart,
      startSyntheticAmplitude,
      stopAmplitudeTracking,
      stopSpeechSynthesis,
    ]
  );

  /**
   * ▶️ Play audio from backend or fall back to SpeechSynthesis
   */
  const playAudio = useCallback(
    async (response: VoiceResponse): Promise<void> => {
      const audioUrl = response.audio_url;
      console.log('🔊 Preparing Rose playback', {
        hasAudioUrl: Boolean(audioUrl),
        textPreview: response.text?.slice(0, PLAYBACK_TEXT_PREVIEW_CHARS) ?? '(no text)',
      });
      setError(null);

      if (!audioUrl && !response.text) {
        console.log('🤫 Rose returned empty response (silence/listening mode)');
        return;
      }

      let lastError: unknown = null;

      if (audioUrl) {
        for (let attempt = 1; attempt <= AUDIO_PLAYBACK_MAX_RETRIES; attempt += 1) {
          try {
            console.log(`🎯 Audio playback attempt ${attempt}/${AUDIO_PLAYBACK_MAX_RETRIES}`);
            const blob = await fetchAudioBlob(audioUrl);
            await playFromBlob(blob);
            return;
          } catch (attemptError) {
            console.error('⚠️ Audio playback attempt failed', attemptError);
            lastError = attemptError;
            if (attempt < AUDIO_PLAYBACK_MAX_RETRIES) {
              await new Promise((resolve) => setTimeout(resolve, AUDIO_FETCH_RETRY_DELAY_MS));
            }
          }
        }
      }

      if (response.text) {
        try {
          await speakWithSynthesis(response.text);
          return;
        } catch (synthError) {
          console.error('❌ Speech synthesis fallback failed', synthError);
          lastError = synthError;
        }
      }

      const errorMsg = 'Unable to play Rose response';
      setError(errorMsg);
      onError?.(errorMsg);
      throw lastError instanceof Error ? lastError : new Error(errorMsg);
    },
    [
      AUDIO_PLAYBACK_MAX_RETRIES,
      fetchAudioBlob,
      onError,
      playFromBlob,
      speakWithSynthesis,
    ]
  );

  /**
   * ⏹️ Stop audio playback
   */
  const stopAudio = useCallback(() => {
    console.log('⏹️ Stopping Rose audio');
    stopSpeechSynthesis();
    void releaseAudioResources();
    setIsPlaying(false);
    setRoseAmplitude(0);
  }, [releaseAudioResources, stopSpeechSynthesis]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [stopAudio]);

  return {
    isPlaying,
    roseAmplitude,
    playAudio,
    stopAudio,
    error,
  };
}
