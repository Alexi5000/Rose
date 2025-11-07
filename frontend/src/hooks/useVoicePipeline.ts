import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/apiClient';
import { refinedVoiceRecordingConfig } from '../config/refinedAudio';
import {
  VOICE_PROCESSING_ERRORS,
  PLAYBACK_ERRORS,
} from '../config/errorMessages';
import {
  DURATION_TOKENS,
  LOG_TOKENS,
  ERROR_TOKENS,
} from '../config/voiceTokens';

export type VoicePipelineState = 'idle' | 'listening' | 'processing' | 'speaking';

interface UseVoicePipelineOptions {
  sessionId: string;
  onError?: (error: string) => void;
  onResponseText?: (text: string) => void;
  onAutoplayBlocked?: () => void;
  onStateChange?: (state: VoicePipelineState) => void;
}

interface PipelineControls {
  processAudioBlob: (audioBlob: Blob) => Promise<void>;
  stopAudio: () => void;
  retryPlayback: () => Promise<void>;
  audioElement: HTMLAudioElement | null;
  error: string | null;
  responseText: string;
}

export const useVoicePipeline = ({
  sessionId,
  onError,
  onResponseText,
  onAutoplayBlocked,
  onStateChange,
}: UseVoicePipelineOptions): PipelineControls => {
  const [error, setError] = useState<string | null>(null);
  const [responseText, setResponseText] = useState('');

  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const playbackTokenRef = useRef(0);
  const objectURLRef = useRef<string | null>(null);

  const propagateState = useCallback(
    (next: VoicePipelineState) => {
      onStateChange?.(next);
      if (next === 'idle') {
        setError(null);
      }
    },
    [onStateChange]
  );

  const cleanupAudioElement = useCallback(() => {
    if (audioElementRef.current) {
      const audio = audioElementRef.current;
      audio.oncanplaythrough = null;
      audio.oncanplay = null;
      audio.onplay = null;
      audio.onended = null;
      audio.onerror = null;
      audio.onstalled = null;
      audio.onsuspend = null;
      audio.pause();
      audio.src = '';
      audio.load();
      audioElementRef.current = null;
    }

    if (objectURLRef.current) {
      URL.revokeObjectURL(objectURLRef.current);
      objectURLRef.current = null;
    }
  }, []);

  const playAudioResponse = useCallback(
    async (audioUrl: string): Promise<void> => {
      return new Promise(async (resolve, reject) => {
        try {
          const currentToken = ++playbackTokenRef.current;
          console.log(`${LOG_TOKENS.prefixSpeaking} #${currentToken}`, { audioUrl });

          cleanupAudioElement();

          const audio = new Audio();
          audio.preload = 'auto';
          if (audioUrl.startsWith('http') && !audioUrl.includes(window.location.hostname)) {
            audio.crossOrigin = 'anonymous';
          }
          audioElementRef.current = audio;

          let stallRetryCount = 0;
          let readinessTimeout: NodeJS.Timeout | null = null;

          const isCurrentPlayback = () => currentToken === playbackTokenRef.current;

          const setupReadinessHandlers = () => {
            return new Promise<void>((resolveReady, rejectReady) => {
              let canplayFallbackFired = false;

              audio.oncanplaythrough = () => {
                if (!isCurrentPlayback()) return;
                if (readinessTimeout) clearTimeout(readinessTimeout);
                resolveReady();
              };

              audio.oncanplay = () => {
                if (!isCurrentPlayback()) return;
                if (canplayFallbackFired) return;
              };

              readinessTimeout = setTimeout(() => {
                if (!isCurrentPlayback()) return;
                canplayFallbackFired = true;
                if (audio.readyState >= HTMLMediaElement.HAVE_FUTURE_DATA) {
                  resolveReady();
                } else {
                  rejectReady(new Error(PLAYBACK_ERRORS.AUDIO_LOAD_TIMEOUT));
                }
              }, DURATION_TOKENS.voiceBurstWindowMs);
            });
          };

          audio.onstalled = () => {
            if (!isCurrentPlayback()) return;
            if (stallRetryCount < 2) {
              stallRetryCount += 1;
              setError(PLAYBACK_ERRORS.AUDIO_STALLED);
              audio.load();
            } else {
              setError(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED);
              propagateState('idle');
              cleanupAudioElement();
              if (onError) onError(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED);
              reject(new Error(PLAYBACK_ERRORS.AUDIO_LOAD_FAILED));
            }
          };

          audio.onsuspend = audio.onstalled;

          audio.onplay = () => {
            if (!isCurrentPlayback()) return;
            propagateState('speaking');
          };

          audio.onended = () => {
            if (!isCurrentPlayback()) return;
            propagateState('idle');
            cleanupAudioElement();
            resolve();
          };

          audio.onerror = () => {
            if (!isCurrentPlayback()) return;
            const mediaError = audio.error;
            let errorMessage: string = PLAYBACK_ERRORS.PLAYBACK_FAILED;

            if (mediaError) {
              switch (mediaError.code) {
                case MediaError.MEDIA_ERR_NETWORK:
                  errorMessage = PLAYBACK_ERRORS.AUDIO_LOAD_FAILED;
                  break;
                case MediaError.MEDIA_ERR_DECODE:
                  errorMessage = PLAYBACK_ERRORS.AUDIO_DECODE_FAILED;
                  break;
                case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                  errorMessage = PLAYBACK_ERRORS.AUDIO_NOT_SUPPORTED;
                  break;
                case MediaError.MEDIA_ERR_ABORTED:
                  return;
                default:
                  break;
              }
            }

            setError(errorMessage);
            propagateState('idle');
            cleanupAudioElement();
            if (onError) onError(errorMessage);
            reject(new Error(errorMessage));
          };

          audio.src = audioUrl;
          await setupReadinessHandlers();

          try {
            await audio.play();
          } catch (playError) {
            if (!isCurrentPlayback()) return;

            if (playError instanceof Error && playError.name === 'NotAllowedError') {
              setError(PLAYBACK_ERRORS.PLAYBACK_BLOCKED);
              propagateState('idle');
              if (onAutoplayBlocked) onAutoplayBlocked();
              if (onError) onError(PLAYBACK_ERRORS.PLAYBACK_BLOCKED);
              reject(new Error(PLAYBACK_ERRORS.PLAYBACK_BLOCKED));
              return;
            }

            throw playError;
          }
        } catch (err) {
          const errorMessage = err instanceof Error ? err.message : PLAYBACK_ERRORS.PLAYBACK_FAILED;
          setError(errorMessage);
          propagateState('idle');
          cleanupAudioElement();
          if (onError) onError(errorMessage);
          reject(err);
        }
      });
    },
    [cleanupAudioElement, onAutoplayBlocked, onError, propagateState]
  );

  const processAudioBlob = useCallback(
    async (audioBlob: Blob) => {
      if (!sessionId) {
        const message = ERROR_TOKENS.sessionMissing;
        setError(message);
        if (onError) onError(message);
        throw new Error(message);
      }

      if (audioBlob.size < refinedVoiceRecordingConfig.minAudioSizeBytes) {
        console.warn(`${LOG_TOKENS.prefixUtteranceDiscard} (too small)`, {
          size: audioBlob.size,
        });
        return;
      }

      console.log(LOG_TOKENS.prefixProcessing, {
        sessionId,
        size: audioBlob.size,
      });

      try {
        propagateState('processing');
        const response = await apiClient.processVoice(audioBlob, sessionId);
        setResponseText(response.text);
        if (onResponseText) onResponseText(response.text);
        await playAudioResponse(response.audio_url);
      } catch (err) {
        console.error('❌ Voice pipeline error:', err);
        const errorMessage = err instanceof Error ? err.message : VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED;
        setError(errorMessage);
        propagateState('idle');
        if (onError) onError(errorMessage);
      }
    },
    [sessionId, onError, onResponseText, playAudioResponse, propagateState]
  );

  const retryPlayback = useCallback(async () => {
    if (!audioElementRef.current) {
      return;
    }

    try {
      await audioElementRef.current.play();
      setError(null);
      propagateState('speaking');
    } catch (err) {
      const errorMessage = PLAYBACK_ERRORS.PLAYBACK_FAILED;
      setError(errorMessage);
      if (onError) onError(errorMessage);
    }
  }, [onError, propagateState]);

  const stopAudio = useCallback(() => {
    cleanupAudioElement();
    propagateState('idle');
  }, [cleanupAudioElement, propagateState]);

  useEffect(() => {
    return () => {
      cleanupAudioElement();
    };
  }, [cleanupAudioElement]);

  return {
    processAudioBlob,
    stopAudio,
    retryPlayback,
    audioElement: audioElementRef.current,
    error,
    responseText,
  };
};
