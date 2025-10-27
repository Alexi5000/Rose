import { useState, useEffect, useRef, useCallback } from 'react';
import { refinedAmbientAudioConfig, refinedAudioDuckingConfig } from '../config/refinedAudio';

/**
 * useAmbientAudio Hook
 * 
 * Manages ambient background audio (ocean waves, wind, etc.)
 * 
 * Task 22.3: Enhanced with refined audio settings for optimal experience
 * 
 * Features:
 * - Seamless audio looping
 * - Volume ducking during conversation
 * - User-controllable volume
 * - Fade in/out transitions
 * - Improved quality and timing
 * 
 * Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
 */

interface UseAmbientAudioOptions {
  audioUrl?: string; // URL to ambient audio file
  defaultVolume?: number; // Default volume (0-1)
  duckingVolume?: number; // Volume during conversation (0-1)
  fadeInDuration?: number; // Fade in duration in ms
  fadeOutDuration?: number; // Fade out duration in ms
  enabled?: boolean; // Enable/disable ambient audio
}

export const useAmbientAudio = (options: UseAmbientAudioOptions = {}) => {
  const {
    audioUrl = refinedAmbientAudioConfig.defaultAudioUrl,
    defaultVolume = refinedAmbientAudioConfig.defaultVolume,
    duckingVolume = refinedAmbientAudioConfig.duckingVolume,
    fadeInDuration = refinedAmbientAudioConfig.fadeInDuration,
    fadeOutDuration = refinedAmbientAudioConfig.fadeOutDuration,
    enabled = true,
  } = options;

  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(defaultVolume);
  const [isDucking, setIsDucking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fadeIntervalRef = useRef<number | null>(null);

  /**
   * Initialize ambient audio
   */
  const initializeAudio = useCallback(() => {
    if (!enabled || audioRef.current) return;

    try {
      const audio = new Audio(audioUrl);
      audio.loop = true; // Enable seamless looping
      audio.volume = 0; // Start at 0 for fade in
      audio.preload = 'auto';
      
      audioRef.current = audio;

      audio.onerror = (e) => {
        console.error('Ambient audio error:', e);
        setError('Failed to load ambient audio');
      };

      audio.oncanplaythrough = () => {
        setError(null);
      };
    } catch (err) {
      console.error('Error initializing ambient audio:', err);
      setError('Failed to initialize ambient audio');
    }
  }, [enabled, audioUrl]);

  /**
   * Fade audio volume
   */
  const fadeVolume = useCallback(
    (targetVolume: number, duration: number) => {
      if (!audioRef.current) return;

      // Clear any existing fade
      if (fadeIntervalRef.current) {
        clearInterval(fadeIntervalRef.current);
      }

      const audio = audioRef.current;
      const startVolume = audio.volume;
      const volumeDelta = targetVolume - startVolume;
      const steps = 50; // Number of steps in fade
      const stepDuration = duration / steps;
      const stepSize = volumeDelta / steps;

      let currentStep = 0;

      fadeIntervalRef.current = window.setInterval(() => {
        currentStep++;
        
        if (currentStep >= steps) {
          audio.volume = targetVolume;
          if (fadeIntervalRef.current) {
            clearInterval(fadeIntervalRef.current);
            fadeIntervalRef.current = null;
          }
        } else {
          audio.volume = startVolume + stepSize * currentStep;
        }
      }, stepDuration);
    },
    []
  );

  /**
   * Start playing ambient audio
   */
  const play = useCallback(() => {
    if (!audioRef.current || !enabled) return;

    audioRef.current
      .play()
      .then(() => {
        setIsPlaying(true);
        fadeVolume(volume, fadeInDuration);
      })
      .catch((err) => {
        console.error('Error playing ambient audio:', err);
        setError('Failed to play ambient audio');
      });
  }, [enabled, volume, fadeInDuration, fadeVolume]);

  /**
   * Stop playing ambient audio
   */
  const stop = useCallback(() => {
    if (!audioRef.current) return;

    fadeVolume(0, fadeOutDuration);
    
    setTimeout(() => {
      if (audioRef.current) {
        audioRef.current.pause();
        setIsPlaying(false);
      }
    }, fadeOutDuration);
  }, [fadeOutDuration, fadeVolume]);

  /**
   * Set volume (0-1)
   */
  const setAmbientVolume = useCallback(
    (newVolume: number) => {
      const clampedVolume = Math.max(0, Math.min(1, newVolume));
      setVolume(clampedVolume);
      
      if (audioRef.current && isPlaying && !isDucking) {
        fadeVolume(clampedVolume, 300);
      }
    },
    [isPlaying, isDucking, fadeVolume]
  );

  /**
   * Duck volume during conversation - refined timing
   */
  const duck = useCallback(() => {
    if (!audioRef.current || !isPlaying) return;
    
    setIsDucking(true);
    fadeVolume(duckingVolume, refinedAudioDuckingConfig.duckDuration);
  }, [isPlaying, duckingVolume, fadeVolume]);

  /**
   * Restore volume after conversation - refined timing
   */
  const unduck = useCallback(() => {
    if (!audioRef.current || !isPlaying) return;
    
    setIsDucking(false);
    fadeVolume(volume, refinedAudioDuckingConfig.unduckDuration);
  }, [isPlaying, volume, fadeVolume]);

  /**
   * Toggle play/pause
   */
  const toggle = useCallback(() => {
    if (isPlaying) {
      stop();
    } else {
      play();
    }
  }, [isPlaying, play, stop]);

  /**
   * Initialize audio on mount
   */
  useEffect(() => {
    if (enabled) {
      initializeAudio();
    }
  }, [enabled, initializeAudio]);

  /**
   * Auto-play on mount if enabled - refined delay
   */
  useEffect(() => {
    if (enabled && audioRef.current && !isPlaying) {
      // Refined delay to ensure audio is loaded and scene is ready
      const timer = setTimeout(() => {
        play();
      }, refinedAmbientAudioConfig.autoPlayDelay);

      return () => clearTimeout(timer);
    }
  }, [enabled, play, isPlaying]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (fadeIntervalRef.current) {
        clearInterval(fadeIntervalRef.current);
      }
      
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return {
    // State
    isPlaying,
    volume,
    isDucking,
    error,
    
    // Controls
    play,
    stop,
    toggle,
    setVolume: setAmbientVolume,
    duck,
    unduck,
    
    // Audio element ref
    audioElement: audioRef.current,
  };
};
