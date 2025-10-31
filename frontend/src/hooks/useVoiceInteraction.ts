import { useState, useRef, useCallback, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { refinedVoiceRecordingConfig } from '../config/refinedAudio';
import {
  MICROPHONE_ERRORS,
  VOICE_PROCESSING_ERRORS,
  PLAYBACK_ERRORS,
  SESSION_ERRORS,
} from '../config/errorMessages';

/**
 * useVoiceInteraction Hook
 *
 * Production-grade voice interaction management with comprehensive error handling,
 * codec negotiation, autoplay policy handling, and race-condition safety.
 *
 * Features:
 * - Robust MIME type selection with explicit codecs
 * - Codec probing before playback
 * - Readiness checks with timeout fallbacks
 * - Autoplay policy handling with user gesture retry
 * - Playback token for race-safety
 * - Comprehensive error taxonomy and logging
 * - Proper resource cleanup
 *
 * Requirements: 3.2, 3.3, 3.4, 11.7
 */

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

interface UseVoiceInteractionOptions {
  sessionId: string;
  onError?: (error: string) => void;
  onResponseText?: (text: string) => void;
  onAutoplayBlocked?: () => void; // Callback when autoplay is blocked
}

// Audio configuration constants
const AUDIO_CONFIG = {
  READINESS_TIMEOUT_MS: 8000, // Wait 8s for canplaythrough
  STALL_RETRY_LIMIT: 1,
  CODEC_PREFERENCES: [
    'audio/webm;codecs=opus',
    'audio/ogg;codecs=opus',
    'audio/mp4',
  ] as const,
  BITS_PER_SECOND: 96000, // 96kbps for good quality/size balance
  MAX_RECORDING_DURATION_MS: 60000, // 60 seconds max
} as const;

export const useVoiceInteraction = (options: UseVoiceInteractionOptions) => {
  const { sessionId, onError, onResponseText, onAutoplayBlocked } = options;

  // State management
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [responseText, setResponseText] = useState<string>('');

  // Refs for media handling
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const playbackTokenRef = useRef<number>(0); // Monotonically increasing token
  const objectURLRef = useRef<string | null>(null); // Track blob URLs for cleanup
  const recordingStartTimeRef = useRef<number>(0);

  /**
   * Select best supported MIME type with explicit codec
   */
  const selectMimeType = useCallback((): { mimeType: string | undefined; extension: string } => {
    for (const type of AUDIO_CONFIG.CODEC_PREFERENCES) {
      if (MediaRecorder.isTypeSupported(type)) {
        console.log(`✅ Selected MIME type: ${type}`);
        const extension = type.startsWith('audio/webm') ? 'webm' : type.startsWith('audio/ogg') ? 'ogg' : 'mp4';
        return { mimeType: type, extension };
      }
    }

    // Fallback: let browser choose
    console.warn('⚠️ No preferred MIME types supported, using browser default');
    return { mimeType: undefined, extension: 'webm' };
  }, []);

  /**
   * Probe codec support for audio playback
   */
  const probeCodecSupport = useCallback((): Record<string, boolean> => {
    const audio = document.createElement('audio');
    return {
      mp3: audio.canPlayType('audio/mpeg') !== '',
      webm_opus: audio.canPlayType('audio/webm; codecs="opus"') !== '',
      ogg_opus: audio.canPlayType('audio/ogg; codecs="opus"') !== '',
      mp4: audio.canPlayType('audio/mp4') !== '',
      wav: audio.canPlayType('audio/wav') !== '',
    };
  }, []);

  /**
   * Start recording audio from microphone with robust MIME selection
   */
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      recordingStartTimeRef.current = Date.now();

      // Request microphone access with optimal settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: refinedVoiceRecordingConfig.audioConstraints,
      });

      streamRef.current = stream;

      // Select best MIME type
      const { mimeType } = selectMimeType();

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType,
        bitsPerSecond: AUDIO_CONFIG.BITS_PER_SECOND,
      });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const duration = Date.now() - recordingStartTimeRef.current;

        // Clean up stream first
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        // Build blob with selected MIME type
        const finalMimeType = mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: finalMimeType });

        // Clear recorder ref
        mediaRecorderRef.current = null;

        // Validate minimum size
        if (audioBlob.size < refinedVoiceRecordingConfig.minAudioSizeBytes) {
          console.warn(
            `⚠️ Audio too short: ${audioBlob.size} bytes (minimum ${refinedVoiceRecordingConfig.minAudioSizeBytes} bytes)`
          );
          const errorMessage = '🎤 Recording too short. Please hold the button longer and speak clearly.';
          setError(errorMessage);
          setVoiceState('idle');
          if (onError) onError(errorMessage);
          return;
        }

        // Validate maximum duration
        if (duration > AUDIO_CONFIG.MAX_RECORDING_DURATION_MS) {
          console.warn(`⚠️ Recording too long: ${duration}ms (max ${AUDIO_CONFIG.MAX_RECORDING_DURATION_MS}ms)`);
          const errorMessage = '🎤 Recording too long. Please keep messages under 60 seconds.';
          setError(errorMessage);
          setVoiceState('idle');
          if (onError) onError(errorMessage);
          return;
        }

        console.log(`✅ Audio recorded: ${audioBlob.size} bytes, ${duration}ms, type: ${finalMimeType}`);

        // Process the recorded audio
        await processVoiceInput(audioBlob);
      };

      mediaRecorder.start();
      setVoiceState('listening');

    } catch (err) {
      console.error('❌ Error starting recording:', err);

      // Map browser errors to user-friendly messages
      let errorMessage: string = MICROPHONE_ERRORS.GENERIC_ERROR;
      if (err instanceof Error) {
        if (err.name === 'NotFoundError') {
          errorMessage = MICROPHONE_ERRORS.NOT_FOUND;
        } else if (err.name === 'NotAllowedError') {
          errorMessage = MICROPHONE_ERRORS.PERMISSION_DENIED;
        } else if (err.name === 'NotReadableError') {
          errorMessage = MICROPHONE_ERRORS.IN_USE;
        }
      }

      setError(errorMessage);
      setVoiceState('idle');
      if (onError) onError(errorMessage);
    }
  }, [sessionId, onError, selectMimeType]);

  /**
   * Stop recording audio
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'listening') {
      mediaRecorderRef.current.stop();
      // State will transition to 'processing' in processVoiceInput
    }
  }, [voiceState]);

  /**
   * Process recorded audio through backend API
   */
  const processVoiceInput = useCallback(
    async (audioBlob: Blob) => {
      if (!sessionId) {
        const errorMessage = SESSION_ERRORS.SESSION_NOT_FOUND;
        setError(errorMessage);
        setVoiceState('idle');
        if (onError) onError(errorMessage);
        return;
      }

      setVoiceState('processing');
      setError(null);

      try {
        console.log('🎤 Processing voice input...');
        const response = await apiClient.processVoice(audioBlob, sessionId);
        console.log('✅ Voice processing successful');
        setResponseText(response.text);
        if (onResponseText) onResponseText(response.text);

        // Play audio response
        await playAudioResponse(response.audio_url);
      } catch (err) {
        console.error('❌ Voice processing error:', err);

        const errorMessage =
          err instanceof Error ? err.message : VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED;

        setError(errorMessage);
        setVoiceState('idle');
        if (onError) onError(errorMessage);
      }
    },
    [sessionId, onError, onResponseText]
  );

  /**
   * Cleanup previous audio element and revoke blob URLs
   */
  const cleanupAudioElement = useCallback(() => {
    if (audioElementRef.current) {
      const audio = audioElementRef.current;

      // Remove all event listeners
      audio.oncanplaythrough = null;
      audio.oncanplay = null;
      audio.onplay = null;
      audio.onended = null;
      audio.onerror = null;
      audio.onstalled = null;
      audio.onsuspend = null;

      // Stop playback and clear source
      audio.pause();
      audio.src = '';
      audio.load(); // Reset element
      audioElementRef.current = null;
    }

    // Revoke object URL if exists
    if (objectURLRef.current) {
      URL.revokeObjectURL(objectURLRef.current);
      objectURLRef.current = null;
    }
  }, []);

  /**
   * Play audio response with comprehensive error handling and codec negotiation
   */
  const playAudioResponse = useCallback(async (audioUrl: string): Promise<void> => {
    return new Promise(async (resolve, reject) => {
      try {
        // Increment playback token for race-safety
        const currentToken = ++playbackTokenRef.current;
        console.log(`🔊 Starting playback #${currentToken} for URL: ${audioUrl}`);

        // Cleanup previous playback
        cleanupAudioElement();

        // Probe codec support
        const codecSupport = probeCodecSupport();
        console.log('🎵 Codec support:', codecSupport);

        // Create new audio element with optimal settings
        const audio = new Audio();
        audio.preload = 'auto';
        // Only set crossOrigin for cross-origin URLs to avoid CORS issues with same-origin
        if (audioUrl.startsWith('http') && !audioUrl.includes(window.location.hostname)) {
          audio.crossOrigin = 'anonymous';
        }
        audioElementRef.current = audio;

        let readinessTimeout: NodeJS.Timeout | null = null;
        let stallRetryCount = 0;

        // Guard: only process events for current playback token
        const isCurrentPlayback = () => currentToken === playbackTokenRef.current;

        // Readiness handler with timeout
        const setupReadinessHandlers = () => {
          return new Promise<void>((resolveReady, rejectReady) => {
            // Prefer canplaythrough, but fall back to canplay after timeout
            let canplayFallbackFired = false;

            audio.oncanplaythrough = () => {
              if (!isCurrentPlayback()) return;
              if (readinessTimeout) clearTimeout(readinessTimeout);
              console.log('✅ Audio ready (canplaythrough)');
              resolveReady();
            };

            audio.oncanplay = () => {
              if (!isCurrentPlayback()) return;
              if (canplayFallbackFired) return; // Already handled by timeout

              // This fires before canplaythrough, so don't resolve immediately
              console.log('ℹ️ Audio partially ready (canplay)');
            };

            // Timeout fallback to canplay
            readinessTimeout = setTimeout(() => {
              if (!isCurrentPlayback()) return;
              canplayFallbackFired = true;
              console.warn('⏱️ Readiness timeout, falling back to canplay');
              if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
                resolveReady();
              } else {
                rejectReady(new Error(PLAYBACK_ERRORS.AUDIO_LOAD_TIMEOUT));
              }
            }, AUDIO_CONFIG.READINESS_TIMEOUT_MS);
          });
        };

        // Stall/suspend handler with retry
        audio.onstalled = () => {
          if (!isCurrentPlayback()) return;
          console.warn('⚠️ Audio stalled, attempting recovery...');

          if (stallRetryCount < AUDIO_CONFIG.STALL_RETRY_LIMIT) {
            stallRetryCount++;
            setError(PLAYBACK_ERRORS.AUDIO_STALLED);
            audio.load(); // Retry loading
          } else {
            console.error('❌ Audio stalled after retry');
            setError(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED);
            setVoiceState('idle');
            cleanupAudioElement();
            if (onError) onError(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED);
            reject(new Error(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED));
          }
        };

        audio.onsuspend = audio.onstalled; // Same handling

        // Playback event handlers
        audio.onplay = () => {
          if (!isCurrentPlayback()) return;
          console.log('✅ Audio playback started');
          setVoiceState('speaking');
          setError(null); // Clear any stall warnings
        };

        audio.onended = () => {
          if (!isCurrentPlayback()) return;
          console.log('✅ Audio playback completed');
          setVoiceState('idle');
          cleanupAudioElement();
          resolve();
        };

        // Error handler with detailed taxonomy
        audio.onerror = () => {
          if (!isCurrentPlayback()) return;

          const mediaError = audio.error;
          let errorMessage: string = PLAYBACK_ERRORS.PLAYBACK_FAILED;

          if (mediaError) {
            switch (mediaError.code) {
              case MediaError.MEDIA_ERR_NETWORK:
                errorMessage = PLAYBACK_ERRORS.AUDIO_LOAD_FAILED;
                console.error('❌ Network error loading audio:', mediaError.message);
                break;
              case MediaError.MEDIA_ERR_DECODE:
                errorMessage = PLAYBACK_ERRORS.AUDIO_DECODE_FAILED;
                console.error('❌ Decoding error:', mediaError.message);
                break;
              case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                errorMessage = PLAYBACK_ERRORS.AUDIO_NOT_SUPPORTED;
                console.error('❌ Format not supported:', mediaError.message);
                break;
              case MediaError.MEDIA_ERR_ABORTED:
                console.warn('ℹ️ Playback aborted');
                return; // Don't treat abort as error
              default:
                console.error('❌ Unknown audio error:', mediaError.message);
            }
          }

          setError(errorMessage);
          setVoiceState('idle');
          cleanupAudioElement();
          if (onError) onError(errorMessage);
          reject(new Error(errorMessage));
        };

        // Set source and wait for readiness
        audio.src = audioUrl;
        await setupReadinessHandlers();

        // Attempt playback with autoplay policy handling
        try {
          await audio.play();
        } catch (playError) {
          if (!isCurrentPlayback()) return;

          // Handle autoplay blocking
          if (playError instanceof Error && playError.name === 'NotAllowedError') {
            console.warn('⚠️ Autoplay blocked by browser policy');
            const errorMessage = PLAYBACK_ERRORS.PLAYBACK_BLOCKED;
            setError(errorMessage);
            setVoiceState('idle');

            // Notify parent component to show "tap to play" UI
            if (onAutoplayBlocked) onAutoplayBlocked();
            if (onError) onError(errorMessage);

            reject(new Error(errorMessage));
            return;
          }

          throw playError;
        }

      } catch (err) {
        console.error('❌ Error in playAudioResponse:', err);
        const errorMessage = err instanceof Error ? err.message : PLAYBACK_ERRORS.PLAYBACK_FAILED;
        setError(errorMessage);
        setVoiceState('idle');
        cleanupAudioElement();
        if (onError) onError(errorMessage);
        reject(err);
      }
    });
  }, [onError, cleanupAudioElement, probeCodecSupport, onAutoplayBlocked]);

  /**
   * Retry playback (for autoplay recovery after user gesture)
   */
  const retryPlayback = useCallback(async () => {
    if (audioElementRef.current) {
      try {
        await audioElementRef.current.play();
        setError(null);
        setVoiceState('speaking');
      } catch (err) {
        console.error('❌ Retry playback failed:', err);
        const errorMessage = PLAYBACK_ERRORS.PLAYBACK_FAILED;
        setError(errorMessage);
        if (onError) onError(errorMessage);
      }
    }
  }, [onError]);

  /**
   * Stop any ongoing audio playback
   */
  const stopAudio = useCallback(() => {
    cleanupAudioElement();
    setVoiceState('idle');
  }, [cleanupAudioElement]);

  /**
   * Cancel recording if in progress
   */
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'listening') {
      // Stop recording without processing
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
      audioChunksRef.current = [];

      // Clean up stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      setVoiceState('idle');
    }
  }, [voiceState]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Clean up media stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      // Clean up audio playback
      cleanupAudioElement();
    };
  }, [cleanupAudioElement]);

  return {
    // State
    voiceState,
    error,
    responseText,

    // Controls
    startRecording,
    stopRecording,
    cancelRecording,
    stopAudio,
    retryPlayback, // New: for autoplay recovery

    // Status checks
    isListening: voiceState === 'listening',
    isProcessing: voiceState === 'processing',
    isSpeaking: voiceState === 'speaking',
    isIdle: voiceState === 'idle',

    // Audio element ref (for audio analysis)
    audioElement: audioElementRef.current,
  };
};
