/**
 * 🔊 Rose Audio Playback Hook
 *
 * Manages playback of Rose's voice responses with real-time amplitude analysis
 * for visual feedback (shader reactivity).
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  ANALYSER_FFT_SIZE,
  ANALYSER_SMOOTHING,
} from '@/config/voice';
import { calculateRms, createPlaybackAnalyzer } from '@/lib/audio-utils';

interface UseRoseAudioReturn {
  /** Whether Rose is currently speaking */
  isPlaying: boolean;
  /** Current Rose audio amplitude (0-1) */
  roseAmplitude: number;
  /** Play audio from URL */
  playAudio: (audioUrl: string) => Promise<void>;
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

  /**
   * 🔊 Analyze audio amplitude loop (runs at 60fps)
   */
  const analyzePlayback = useCallback(() => {
    if (!analyserRef.current || !isPlaying) {
      setRoseAmplitude(0);
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
  }, [isPlaying]);

  /**
   * ▶️ Play audio from URL
   */
  const playAudio = useCallback(
    async (audioUrl: string): Promise<void> => {
      console.log(`🔊 Playing Rose's response: ${audioUrl}`);
      setError(null);

      try {
        // Stop any currently playing audio
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }

        // Stop analysis loop
        if (animationFrameRef.current) {
          cancelAnimationFrame(animationFrameRef.current);
          animationFrameRef.current = null;
        }

        // Close previous audio context
        if (audioContextRef.current) {
          await audioContextRef.current.close();
          audioContextRef.current = null;
          analyserRef.current = null;
        }

        // Create new audio element
        const audio = new Audio(audioUrl);
        audio.volume = 1.0; // Ensure volume is max
        audioRef.current = audio;

        console.log(`🔊 Audio element created, volume: ${audio.volume}`);

        // Wait for metadata to load before setting up Web Audio API
        // This ensures the browser knows the audio format before we route it
        await new Promise<void>((resolve, reject) => {
          audio.addEventListener('loadedmetadata', () => {
            console.log(`✅ Audio metadata loaded: duration=${audio.duration.toFixed(2)}s`);
            resolve();
          }, { once: true });

          audio.addEventListener('error', (e) => {
            console.error('❌ Audio metadata load error:', e);
            reject(new Error('Failed to load audio metadata'));
          }, { once: true });

          // Start loading by setting load explicitly
          audio.load();
        });

        // Now set up audio analyzer (after metadata is loaded)
        const { audioContext, analyser } = createPlaybackAnalyzer(
          audio,
          ANALYSER_FFT_SIZE,
          ANALYSER_SMOOTHING
        );

        audioContextRef.current = audioContext;
        analyserRef.current = analyser;

        // Resume AudioContext if suspended (browser autoplay policy)
        if (audioContext.state === 'suspended') {
          console.log('⏸️ AudioContext suspended, resuming...');
          await audioContext.resume();
          console.log(`✅ AudioContext resumed, state: ${audioContext.state}`);
        } else {
          console.log(`✅ AudioContext state: ${audioContext.state}`);
        }

        // Event handlers
        audio.onplay = () => {
          console.log('▶️ Rose started speaking');
          setIsPlaying(true);
          onPlaybackStart?.();

          // Start amplitude analysis
          animationFrameRef.current = requestAnimationFrame(analyzePlayback);
        };

        audio.onended = () => {
          console.log('⏹️ Rose finished speaking');
          setIsPlaying(false);
          setRoseAmplitude(0);
          onPlaybackEnd?.();

          // Stop analysis loop
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
          }
        };

        audio.onerror = (e) => {
          console.error('❌ Audio playback error:', e);
          const errorMsg = 'Failed to play audio response';
          setError(errorMsg);
          setIsPlaying(false);
          setRoseAmplitude(0);
          onError?.(errorMsg);

          // Stop analysis loop
          if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
          }
        };

        // Start playback
        await audio.play();
      } catch (err) {
        console.error('❌ Failed to play audio:', err);
        const errorMsg = 'Failed to start audio playback';
        setError(errorMsg);
        onError?.(errorMsg);
      }
    },
    [analyzePlayback, onPlaybackStart, onPlaybackEnd, onError]
  );

  /**
   * ⏹️ Stop audio playback
   */
  const stopAudio = useCallback(() => {
    console.log('⏹️ Stopping Rose audio');

    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
      analyserRef.current = null;
    }

    setIsPlaying(false);
    setRoseAmplitude(0);
  }, []);

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
