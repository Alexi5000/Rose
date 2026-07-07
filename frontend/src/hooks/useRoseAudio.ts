/**
 * 🔊 Rose Audio Playback Hook
 *
 * Guarantees that Rose replies audibly by first trying streamed audio URLs and
 * falling back to the SpeechSynthesis API when needed.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  AUDIO_DEFAULT_VOLUME,
  AUDIO_PLAYBACK_MAX_RETRIES,
  SPEECH_SYNTHESIS_LANGUAGE,
  SPEECH_SYNTHESIS_PITCH,
  SPEECH_SYNTHESIS_RATE,
} from '@/config/voice';
import type { VoiceResponse } from '@/types/voice';

const SYNTHETIC_AMPLITUDE_BASE = 0.3;
const SYNTHETIC_AMPLITUDE_VARIATION = 0.2;
const SYNTHETIC_AMPLITUDE_PERIOD_MS = 160;
const AUDIO_FETCH_RETRY_DELAY_MS = 500;

const resolveAudioUrl = (audioUrl: string): string => {
  try {
    return new URL(audioUrl, window.location.origin).toString();
  } catch (error) {
    console.warn('Failed to resolve audio URL, using raw value', error);
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
  const animationFrameRef = useRef<number | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const amplitudeModeRef = useRef<'idle' | 'synthetic'>('idle');
  // Tracks the current inline blob URL so it can be revoked when audio is released.
  const inlineBlobUrlRef = useRef<string | null>(null);

  const stopAmplitudeTracking = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    amplitudeModeRef.current = 'idle';
    setRoseAmplitude(0);
  }, []);

  const startSyntheticAmplitude = useCallback(() => {
    stopAmplitudeTracking();
    amplitudeModeRef.current = 'synthetic';

    const tick = () => {
      if (amplitudeModeRef.current !== 'synthetic') {
        return;
      }

      const timeSeed = performance.now();
      const amplitude =
        SYNTHETIC_AMPLITUDE_BASE +
        SYNTHETIC_AMPLITUDE_VARIATION * Math.abs(Math.sin(timeSeed / SYNTHETIC_AMPLITUDE_PERIOD_MS));
      setRoseAmplitude(amplitude);
      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);
  }, [stopAmplitudeTracking]);

  const stopSpeechSynthesis = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      console.log('SpeechSynthesis cancelled');
    }

    utteranceRef.current = null;
  }, []);

  const releaseAudioResources = useCallback(() => {
    stopAmplitudeTracking();

    if (audioRef.current) {
      audioRef.current.onplay = null;
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }

    // Revoke any outstanding inline blob URL to free memory.
    if (inlineBlobUrlRef.current) {
      URL.revokeObjectURL(inlineBlobUrlRef.current);
      inlineBlobUrlRef.current = null;
    }
  }, [stopAmplitudeTracking]);

  /**
   * 🌐 Play audio directly from a URL.
   *
   * Sets audio.src directly so the browser can start playing as soon as the
   * first bytes arrive , no full-download wait, no objectURL round-trip.
   * This shaves 200,500 ms off time-to-first-audio compared to blob-fetch.
   */
  const playFromUrl = useCallback(
    async (audioUrl: string): Promise<void> => {
      releaseAudioResources();
      stopSpeechSynthesis();

      const resolvedUrl = resolveAudioUrl(audioUrl);
      console.log('Playing Rose audio');

      const audio = new Audio(resolvedUrl);
      audio.preload = 'auto';
      audio.volume = AUDIO_DEFAULT_VOLUME;
      audioRef.current = audio;

      // Wait for enough metadata to confirm the file is valid before calling play()
      await new Promise<void>((resolve, reject) => {
        const onLoaded = () => {
          audio.removeEventListener('loadedmetadata', onLoaded);
          audio.removeEventListener('error', onError_);
          console.log(`Audio metadata loaded: duration=${audio.duration.toFixed(2)}s`);
          resolve();
        };
        const onError_ = (event: Event) => {
          audio.removeEventListener('loadedmetadata', onLoaded);
          audio.removeEventListener('error', onError_);
          const mediaError = (event.target as HTMLAudioElement).error;
          console.error('Failed to load Rose audio', {
            code: mediaError?.code,
            message: mediaError?.message,
          });
          reject(new Error(`Audio load failed: code=${mediaError?.code}`));
        };
        audio.addEventListener('loadedmetadata', onLoaded);
        audio.addEventListener('error', onError_);
        audio.load();
      });

      audio.onplay = () => {
        console.log('Rose audio playback started', { duration: audio.duration });
        setIsPlaying(true);
        startSyntheticAmplitude();
        onPlaybackStart?.();
      };

      audio.onended = () => {
        console.log('Rose audio playback finished');
        setIsPlaying(false);
        stopAmplitudeTracking();
        onPlaybackEnd?.();
      };

      audio.onerror = (event) => {
        const mediaError = audio.error;
        console.error('Audio element error during playback', {
          event,
          code: mediaError?.code,
          message: mediaError?.message,
        });
        setError('Audio playback error');
        setIsPlaying(false);
        stopAmplitudeTracking();
        onError?.('Audio playback error');
      };

      await audio.play();
    },
    [
      onError,
      onPlaybackEnd,
      onPlaybackStart,
      releaseAudioResources,
      startSyntheticAmplitude,
      stopAmplitudeTracking,
      stopSpeechSynthesis,
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
          console.log('Speech synthesis finished');
          setIsPlaying(false);
          stopAmplitudeTracking();
          onPlaybackEnd?.();
          resolve();
        };

        utterance.onerror = (event) => {
          console.error('Speech synthesis error', event);
          setIsPlaying(false);
          stopAmplitudeTracking();
          reject(new Error('Speech synthesis failed'));
        };

        console.log('Speaking via SpeechSynthesis fallback');
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
      console.log('Preparing Rose playback', {
        hasAudioUrl: Boolean(audioUrl),
        hasInlineAudio: Boolean(response.audio_data),
        audioStreamed: Boolean(response.audio_streamed),
        responseTextLength: response.text?.length ?? 0,
      });
      setError(null);

      if (response.audio_streamed) {
        console.log('Rose response already streamed over WebSocket');
        return;
      }

      if (!audioUrl && !response.audio_data && !response.text) {
        console.log('Rose returned empty response (silence/listening mode)');
        return;
      }

      let lastError: unknown = null;

      // Prefer inline base64 audio , avoids extra HTTP round-trip
      if (response.audio_data) {
        try {
          console.log('Playing inline audio');
          const binary = atob(response.audio_data);
          const bytes = new Uint8Array(binary.length);
          for (let i = 0; i < binary.length; i++) {
            bytes[i] = binary.charCodeAt(i);
          }
          const blob = new Blob([bytes], { type: 'audio/mpeg' });
          const inlineUrl = URL.createObjectURL(blob);
          inlineBlobUrlRef.current = inlineUrl; // tracked for revocation in releaseAudioResources
          await playFromUrl(inlineUrl);
          return;
        } catch (inlineError) {
          console.error('Inline audio playback failed, falling back to URL', inlineError);
          lastError = inlineError;
        }
      }

      if (audioUrl) {
        for (let attempt = 1; attempt <= AUDIO_PLAYBACK_MAX_RETRIES; attempt += 1) {
          try {
            console.log(`Audio playback attempt ${attempt}/${AUDIO_PLAYBACK_MAX_RETRIES}`);
            await playFromUrl(audioUrl);
            return;
          } catch (attemptError) {
            console.error('Audio playback attempt failed', attemptError);
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
          console.error('Speech synthesis fallback failed', synthError);
          lastError = synthError;
        }
      }

      const errorMsg = 'Unable to play Rose response';
      setError(errorMsg);
      onError?.(errorMsg);
      throw lastError instanceof Error ? lastError : new Error(errorMsg);
    },
    [
      onError,
      playFromUrl,
      speakWithSynthesis,
    ]
  );

  /**
   * ⏹️ Stop audio playback
   *
   * Explicitly firing onPlaybackEnd here ensures the voice session state
   * machine resets even when audio is interrupted (barge-in), not just
   * when it ends naturally via the audio.onended event.
   */
  const stopAudio = useCallback(() => {
    console.log('Stopping Rose audio');
    stopSpeechSynthesis();
    releaseAudioResources();
    setIsPlaying(false);
    setRoseAmplitude(0);
    // Notify voice session so it can reset from 'speaking' state
    onPlaybackEnd?.();
  }, [releaseAudioResources, stopSpeechSynthesis, onPlaybackEnd]);

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
