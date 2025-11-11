import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { refinedVoiceRecordingConfig } from '../config/refinedAudio';
import {
  DETECTION_TOKENS,
  DURATION_TOKENS,
  ERROR_TOKENS,
  LOG_TOKENS,
  AUDIO_ENGINE_TOKENS,
} from '../config/voiceTokens';
import { calculateRms } from '../utils/audioAnalysis';
import {
  VOICE_PROCESSING_ERRORS,
} from '../config/errorMessages';
import {
  useVoicePipeline,
  VoicePipelineState,
} from './useVoicePipeline';

type AudioSampleArray = Float32Array<ArrayBuffer>;

export type VoiceSessionState = VoicePipelineState;

type SessionMode = 'muted' | 'active';

type VoiceSessionControllerOptions = {
  sessionId: string;
  onError?: (message: string) => void;
  onResponseText?: (text: string) => void;
  onAutoplayBlocked?: () => void;
};

type VoiceSessionControllerReturn = {
  voiceState: VoiceSessionState;
  error: string | null;
  responseText: string;
  isSessionActive: boolean;
  toggleSession: () => Promise<void>;
  muteSession: () => Promise<void>;
  activateSession: () => Promise<void>;
  retryPlayback: () => Promise<void>;
  stopAudio: () => void;
  audioElement: HTMLAudioElement | null;
};

const resolveMimeType = () => {
  const { preferred, fallbacks } = refinedVoiceRecordingConfig.mimeType;
  const options = [preferred, ...fallbacks];
  for (const option of options) {
    if (MediaRecorder.isTypeSupported(option)) {
      return option;
    }
  }
  return preferred;
};

export const useVoiceSessionController = ({
  sessionId,
  onError,
  onResponseText,
  onAutoplayBlocked,
}: VoiceSessionControllerOptions): VoiceSessionControllerReturn => {
  const [voiceState, setVoiceState] = useState<VoiceSessionState>('idle');
  const [responseText, setResponseText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [sessionMode, setSessionMode] = useState<SessionMode>('muted');

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const analyserBufferRef = useRef<AudioSampleArray | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const activationTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const inactivityTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const utteranceChunksRef = useRef<Blob[]>([]);
  const utteranceStartTimeRef = useRef<number>(0);
  const processingQueueRef = useRef(Promise.resolve());
  const discardNextUtteranceRef = useRef(false);
  const activationFramesRef = useRef(0);
  const deactivationFramesRef = useRef(0);
  const sessionModeRef = useRef<SessionMode>('muted');
  const utteranceActiveRef = useRef(false);
  const muteSessionRef = useRef<() => Promise<void>>(async () => {});

  const propagateError = useCallback(
    (message: string) => {
      setError(message);
      onError?.(message);
    },
    [onError]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const stopDetectionLoop = useCallback(() => {
    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }
  }, []);

  const clearInactivityTimer = useCallback(() => {
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current);
      inactivityTimeoutRef.current = null;
    }
  }, []);

  const stopTimers = useCallback(() => {
    if (activationTimeoutRef.current) {
      clearTimeout(activationTimeoutRef.current);
      activationTimeoutRef.current = null;
    }
    clearInactivityTimer();
  }, [clearInactivityTimer]);

  const scheduleActivationTimeout = useCallback(() => {
    if (activationTimeoutRef.current) {
      clearTimeout(activationTimeoutRef.current);
    }
    activationTimeoutRef.current = setTimeout(() => {
      console.log(`${LOG_TOKENS.prefixMute} (timeout)`);
      const runMute = muteSessionRef.current;
      void runMute();
    }, DURATION_TOKENS.sessionActiveWindowMs);
  }, []);

  const scheduleInactivityTimeout = useCallback(() => {
    clearInactivityTimer();
    inactivityTimeoutRef.current = setTimeout(() => {
      console.log(`${LOG_TOKENS.prefixMute} (inactivity)`);
      const runMute = muteSessionRef.current;
      void runMute();
    }, DURATION_TOKENS.sessionInactivityGraceMs);
  }, [clearInactivityTimer]);

  const resetFrameCounters = useCallback(() => {
    activationFramesRef.current = 0;
    deactivationFramesRef.current = 0;
  }, []);

  const teardownStream = useCallback(async () => {
    stopDetectionLoop();
    stopTimers();

    if (mediaRecorderRef.current) {
      const recorder = mediaRecorderRef.current;
      if (recorder.state !== 'inactive') {
        discardNextUtteranceRef.current = true;
        recorder.stop();
      }
      mediaRecorderRef.current = null;
    }

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    if (audioContextRef.current) {
      await audioContextRef.current.close();
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    analyserBufferRef.current = null;
    utteranceChunksRef.current = [];
    utteranceActiveRef.current = false;
  }, [stopDetectionLoop, stopTimers]);

  const ensureRecorder = useCallback(async () => {
    if (mediaStreamRef.current && mediaRecorderRef.current) {
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: refinedVoiceRecordingConfig.audioConstraints,
      });
      mediaStreamRef.current = stream;

      const audioContext = new AudioContext();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = DETECTION_TOKENS.analyserFftSize;
      analyser.smoothingTimeConstant = 0.85;
    analyserRef.current = analyser;
    const buffer = new ArrayBuffer(analyser.fftSize * Float32Array.BYTES_PER_ELEMENT);
    analyserBufferRef.current = new Float32Array(buffer) as AudioSampleArray;
      source.connect(analyser);

      const mimeType = resolveMimeType();
      const recorder = new MediaRecorder(stream, {
        mimeType,
        bitsPerSecond: refinedVoiceRecordingConfig.audioConstraints.sampleRate * AUDIO_ENGINE_TOKENS.bitsPerSample,
      });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          utteranceChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const chunks = utteranceChunksRef.current;
        const startedAt = utteranceStartTimeRef.current;
        utteranceChunksRef.current = [];
        utteranceActiveRef.current = false;

        if (discardNextUtteranceRef.current) {
          discardNextUtteranceRef.current = false;
          return;
        }

        const duration = performance.now() - startedAt;
        if (duration < DURATION_TOKENS.minUtteranceMs) {
          console.log(`${LOG_TOKENS.prefixUtteranceDiscard} (too short)`, { duration });
          if (sessionModeRef.current === 'active') {
            scheduleInactivityTimeout();
          }
          return;
        }

        const audioBlob = new Blob(chunks, { type: recorder.mimeType });
        if (audioBlob.size < refinedVoiceRecordingConfig.minAudioSizeBytes) {
          console.log(`${LOG_TOKENS.prefixUtteranceDiscard} (byte threshold)`, {
            size: audioBlob.size,
          });
          if (sessionModeRef.current === 'active') {
            scheduleInactivityTimeout();
          }
          return;
        }

        console.log(LOG_TOKENS.prefixUtteranceQueue, {
          duration,
          size: audioBlob.size,
        });

        processingQueueRef.current = processingQueueRef.current
          .then(() => pipelineControls.processAudioBlob(audioBlob))
          .catch((err) => {
            const message = err instanceof Error ? err.message : VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED;
            propagateError(message);
          })
          .finally(() => {
            if (sessionModeRef.current === 'active') {
              setVoiceState('listening');
              scheduleInactivityTimeout();
            }
          });
      };
    } catch (err) {
      console.error('❌ Failed to ensure recorder', err);
      propagateError(ERROR_TOKENS.streamUnavailable);
      await teardownStream();
      throw err;
    }
  }, [propagateError, scheduleInactivityTimeout, teardownStream]);

  const beginUtterance = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== 'inactive') {
      return;
    }
    clearInactivityTimer();
    utteranceChunksRef.current = [];
    utteranceStartTimeRef.current = performance.now();
    utteranceActiveRef.current = true;
    recorder.start();
    console.log(LOG_TOKENS.prefixUtteranceStart, {
      mimeType: recorder.mimeType,
    });
  }, [clearInactivityTimer]);

  const endUtterance = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== 'recording') {
      return;
    }
    recorder.stop();
  }, []);

  const evaluateVoiceActivity = useCallback(() => {
    const analyser = analyserRef.current;
    const buffer = analyserBufferRef.current;
    if (!analyser || !buffer) {
      return;
    }

    analyser.getFloatTimeDomainData(buffer);
    const rms = calculateRms(buffer);

    if (rms >= DETECTION_TOKENS.rmsActivationThreshold) {
      activationFramesRef.current += 1;
      deactivationFramesRef.current = 0;
    } else if (rms <= DETECTION_TOKENS.rmsDeactivationThreshold) {
      deactivationFramesRef.current += 1;
      activationFramesRef.current = 0;
    } else {
      activationFramesRef.current = Math.max(activationFramesRef.current - 1, 0);
      deactivationFramesRef.current = Math.max(deactivationFramesRef.current - 1, 0);
    }

    const shouldStart = !utteranceActiveRef.current && activationFramesRef.current >= DETECTION_TOKENS.consecutiveActivationFrames;
    const shouldStop = utteranceActiveRef.current && deactivationFramesRef.current >= DETECTION_TOKENS.consecutiveDeactivationFrames;

    if (shouldStart) {
      resetFrameCounters();
      beginUtterance();
      setVoiceState('listening');
    } else if (shouldStop) {
      resetFrameCounters();
      endUtterance();
    }

    if (utteranceActiveRef.current) {
      const now = performance.now();
      const startedAt = utteranceStartTimeRef.current;
      if (now - startedAt > DURATION_TOKENS.maxUtteranceMs) {
        console.log(`${LOG_TOKENS.prefixUtteranceDiscard} (duration cap)`);
        endUtterance();
      }
    }

    rafIdRef.current = requestAnimationFrame(evaluateVoiceActivity);
  }, [beginUtterance, endUtterance, resetFrameCounters, scheduleInactivityTimeout]);

  const startDetectionLoop = useCallback(() => {
    stopDetectionLoop();
    rafIdRef.current = requestAnimationFrame(evaluateVoiceActivity);
  }, [evaluateVoiceActivity, stopDetectionLoop]);

  const handlePipelineStateChange = useCallback(
    (nextState: VoicePipelineState) => {
      if (sessionModeRef.current === 'active') {
        if (nextState === 'idle') {
          setVoiceState('listening');
        } else {
          setVoiceState(nextState);
        }
      } else {
        setVoiceState(nextState);
      }
    },
    []
  );

  const handlePipelineError = useCallback(
    (message: string) => {
      propagateError(message);
      if (sessionModeRef.current === 'active') {
        setVoiceState('listening');
      } else {
        setVoiceState('idle');
      }
    },
    [propagateError]
  );

  const pipelineControls = useVoicePipeline({
    sessionId,
    onError: handlePipelineError,
    onResponseText: (text) => {
      setResponseText(text);
      onResponseText?.(text);
    },
    onAutoplayBlocked,
    onStateChange: handlePipelineStateChange,
  });

  const activateSession = useCallback(async () => {
    if (sessionModeRef.current === 'active') {
      return;
    }

    if (!sessionId) {
      propagateError(ERROR_TOKENS.sessionMissing);
      return;
    }

    try {
      await ensureRecorder();
      scheduleActivationTimeout();
      scheduleInactivityTimeout();
      startDetectionLoop();
      clearError();
      setVoiceState('listening');
      setSessionMode('active');
      sessionModeRef.current = 'active';
      console.log(LOG_TOKENS.prefixActivate, { sessionId });
    } catch (err) {
      console.error('❌ Voice session activation failed', err);
      propagateError(ERROR_TOKENS.activationFailed);
    }
  }, [clearError, ensureRecorder, propagateError, scheduleActivationTimeout, scheduleInactivityTimeout, startDetectionLoop, sessionId]);

  const muteSession = useCallback(async () => {
    if (sessionModeRef.current === 'muted') {
      return;
    }

    console.log(LOG_TOKENS.prefixMute);
    sessionModeRef.current = 'muted';
    setSessionMode('muted');
    stopTimers();
    stopDetectionLoop();
    resetFrameCounters();
    await teardownStream();
    pipelineControls.stopAudio();
    setVoiceState('idle');
  }, [pipelineControls, resetFrameCounters, stopDetectionLoop, stopTimers, teardownStream]);

  const toggleSession = useCallback(async () => {
    if (sessionModeRef.current === 'active') {
      await muteSession();
    } else {
      await activateSession();
    }
  }, [activateSession, muteSession]);

  useEffect(() => {
    muteSessionRef.current = muteSession;
  }, [muteSession]);

  useEffect(() => {
    return () => {
      sessionModeRef.current = 'muted';
      void muteSession();
    };
  }, [muteSession]);

  return useMemo(() => ({
    voiceState,
    error,
    responseText,
    isSessionActive: sessionMode === 'active',
    toggleSession,
    muteSession,
    activateSession,
    retryPlayback: pipelineControls.retryPlayback,
    stopAudio: pipelineControls.stopAudio,
    audioElement: pipelineControls.audioElement,
  }), [activateSession, error, muteSession, pipelineControls, sessionMode, toggleSession, voiceState, responseText]);
};
