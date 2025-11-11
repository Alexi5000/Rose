import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '../services/apiClient';
import { refinedVoiceRecordingConfig } from '../config/refinedAudio';
import {
  VOICE_PROCESSING_ERRORS,
  PLAYBACK_ERRORS,
  RATE_LIMIT_ERRORS,
} from '../config/errorMessages';
import {
  LOG_TOKENS,
  ERROR_TOKENS,
  PLAYBACK_TOKENS,
  PIPELINE_TOKENS,
} from '../config/voiceTokens';

const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

let API_BASE_ORIGIN: string | undefined;
let API_BASE_PATH = '/api/v1';

try {
  const parsedBase = new URL(RAW_API_BASE_URL);
  API_BASE_ORIGIN = parsedBase.origin;
  API_BASE_PATH = parsedBase.pathname || '/';
} catch {
  API_BASE_PATH = RAW_API_BASE_URL || '/api/v1';
}

if (!API_BASE_PATH.startsWith('/')) {
  API_BASE_PATH = `/${API_BASE_PATH}`;
}

const normaliseApiBasePath = (path: string) => {
  if (!path) {
    return '/';
  }

  if (path.length > 1 && path.endsWith('/')) {
    return path.slice(0, -1);
  }

  return path;
};

API_BASE_PATH = normaliseApiBasePath(API_BASE_PATH);

type AudioPlaybackSource = {
  src: string;
  revokeOnCleanup: boolean;
};

const resolveAudioUrl = (audioUrl: string): string => {
  if (!audioUrl) {
    return audioUrl;
  }

  if (/^https?:\/\//i.test(audioUrl) || audioUrl.startsWith('blob:')) {
    return audioUrl;
  }

  const normalized = audioUrl.startsWith('/') ? audioUrl : `/${audioUrl}`;

  if (API_BASE_ORIGIN) {
    return `${API_BASE_ORIGIN}${normalized}`;
  }

  const basePath = normaliseApiBasePath(API_BASE_PATH);

  if (basePath !== '/' && !normalized.startsWith(basePath)) {
    return `${basePath}${normalized}`;
  }

  return normalized;
};

const RATE_LIMIT_MESSAGE_VALUES = Object.values(RATE_LIMIT_ERRORS) as ReadonlyArray<
  (typeof RATE_LIMIT_ERRORS)[keyof typeof RATE_LIMIT_ERRORS]
>;

const isRateLimitMessage = (
  message: string
): message is (typeof RATE_LIMIT_ERRORS)[keyof typeof RATE_LIMIT_ERRORS] => {
  return RATE_LIMIT_MESSAGE_VALUES.includes(
    message as (typeof RATE_LIMIT_ERRORS)[keyof typeof RATE_LIMIT_ERRORS]
  );
};

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
  const rateLimitUntilRef = useRef<number>(0);
  const rateLimitNotifiedRef = useRef(false);


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
    async (playbackSource: AudioPlaybackSource): Promise<void> => {
      return new Promise(async (resolve, reject) => {
        try {
          const currentToken = ++playbackTokenRef.current;
          console.log(`${LOG_TOKENS.prefixSpeaking} #${currentToken}`, { audioUrl: playbackSource.src });

          cleanupAudioElement();

          const audio = new Audio();
          audio.preload = 'auto';

          if (typeof window !== 'undefined') {
            try {
              const resolved = new URL(playbackSource.src, window.location.origin);
              if (resolved.protocol.startsWith('http') && resolved.hostname !== window.location.hostname) {
                audio.crossOrigin = 'anonymous';
              }
            } catch {
              if (playbackSource.src.startsWith('http') && !playbackSource.src.includes(window.location.hostname)) {
                audio.crossOrigin = 'anonymous';
              }
            }
          }

          audioElementRef.current = audio;
          objectURLRef.current = playbackSource.revokeOnCleanup ? playbackSource.src : null;

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
              }, PLAYBACK_TOKENS.readinessTimeoutMs);
            });
          };

          audio.onstalled = () => {
            if (!isCurrentPlayback()) return;
            if (stallRetryCount < PLAYBACK_TOKENS.stallRetryLimit) {
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

          const readinessPromise = setupReadinessHandlers();

          audio.src = playbackSource.src;
          audio.load();

          await readinessPromise;

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

  const prepareAudioSource = useCallback(async (audioUrl: string): Promise<AudioPlaybackSource> => {
    const resolvedUrl = resolveAudioUrl(audioUrl);

    if (typeof window === 'undefined') {
      return {
        src: resolvedUrl,
        revokeOnCleanup: false,
      };
    }

    let shouldPrefetch = false;

    try {
      const resolved = new URL(resolvedUrl, window.location.origin);
      shouldPrefetch = resolved.origin !== window.location.origin;
    } catch {
      shouldPrefetch = false;
    }

    if (!shouldPrefetch) {
      return {
        src: resolvedUrl,
        revokeOnCleanup: false,
      };
    }

    try {
      const response = await fetch(resolvedUrl, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`Audio fetch failed with status ${response.status}`);
      }

      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);

      return {
        src: objectUrl,
        revokeOnCleanup: true,
      };
    } catch (downloadError) {
      console.warn('⚠️ Audio prefetch failed, falling back to direct URL', downloadError);
      return {
        src: resolvedUrl,
        revokeOnCleanup: false,
      };
    }
  }, []);

  const processAudioBlob = useCallback(
    async (audioBlob: Blob) => {
      if (!sessionId) {
        const message = ERROR_TOKENS.sessionMissing;
        setError(message);
        if (onError) onError(message);
        throw new Error(message);
      }

      const now = Date.now();
      const cooldownUntil = rateLimitUntilRef.current;
      if (cooldownUntil && now < cooldownUntil) {
        if (!rateLimitNotifiedRef.current) {
          setError(RATE_LIMIT_ERRORS.TOO_MANY_REQUESTS);
          if (onError) onError(RATE_LIMIT_ERRORS.TOO_MANY_REQUESTS);
          rateLimitNotifiedRef.current = true;
        }
        return;
      }

      if (cooldownUntil && now >= cooldownUntil) {
        rateLimitUntilRef.current = 0;
        rateLimitNotifiedRef.current = false;
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
        const playbackSource = await prepareAudioSource(response.audio_url);
        await playAudioResponse(playbackSource);
      } catch (err) {
        console.error('❌ Voice pipeline error:', err);
        const errorMessage = err instanceof Error ? err.message : VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED;
        setError(errorMessage);
        propagateState('idle');
        if (onError) onError(errorMessage);

        if (isRateLimitMessage(errorMessage)) {
          rateLimitUntilRef.current = Date.now() + PIPELINE_TOKENS.rateLimitCooldownMs;
          rateLimitNotifiedRef.current = false;
        }
      }
    },
    [prepareAudioSource, sessionId, onError, onResponseText, playAudioResponse, propagateState]
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
