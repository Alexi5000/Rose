/**
 * 🎤 Voice Session Hook with Voice Activity Detection (VAD)
 *
 * Manages the complete voice interaction lifecycle:
 * 1. Tap to start → Initialize mic stream
 * 2. Auto-detect speech via VAD
 * 3. Auto-record when user speaks
 * 4. Auto-stop when silence detected
 * 5. Send to backend for processing
 * 6. 20s inactivity timeout OR tap to manually stop
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  RMS_ACTIVATION_THRESHOLD,
  RMS_DEACTIVATION_THRESHOLD,
  ACTIVATION_FRAMES_REQUIRED,
  DEACTIVATION_FRAMES_REQUIRED,
  MIN_RECORDING_DURATION_MS,
  MAX_RECORDING_DURATION_MS,
  INACTIVITY_TIMEOUT_MS,
  ANALYSER_FFT_SIZE,
  ANALYSER_SMOOTHING,
  PREFERRED_MIME_TYPE,
  FALLBACK_MIME_TYPES,
  SESSION_RETRY_ATTEMPTS,
  SESSION_RETRY_DELAY_MS,
  VAD_LOOP_INTERVAL_MS,
} from '@/config/voice';
import {
  calculateRms,
  getSupportedMimeType,
  createAudioAnalyzer,
} from '@/lib/audio-utils';
import { processVoice, createSession } from '@/lib/api';
import type { VoiceState, VoiceResponse } from '@/types/voice';

const STATUS_LOG_FRAME_INTERVAL = Math.max(
  1,
  Math.round(1000 / VAD_LOOP_INTERVAL_MS)
);

interface UseVoiceSessionReturn {
  /** Current state of voice session */
  state: VoiceState;
  /** Current user audio amplitude (0-1) */
  userAmplitude: number;
  /** Whether user is currently speaking */
  isUserSpeaking: boolean;
  /** Start listening session */
  startSession: () => Promise<void>;
  /** Stop listening session */
  stopSession: () => void;
  /** Current session ID */
  sessionId: string | null;
  /** Current error message */
  error: string | null;
  /** Callback when Rose responds */
  onResponse?: (response: VoiceResponse) => void;
}

interface UseVoiceSessionProps {
  /** Callback when Rose's response is ready */
  onResponse: (response: VoiceResponse) => void;
  /** Callback when error occurs */
  onError: (error: string) => void;
}

export function useVoiceSession({
  onResponse,
  onError,
}: UseVoiceSessionProps): UseVoiceSessionReturn {
  // 🎯 State
  const [state, setState] = useState<VoiceState>('idle');
  const [userAmplitude, setUserAmplitude] = useState(0);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Ref to always have current sessionId in callbacks
  const sessionIdRef = useRef<string | null>(sessionId);

  // 🔧 Refs (persist across renders)
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const inactivityTimeoutRef = useRef<number | null>(null);
  const recordingStartTimeRef = useRef<number | null>(null);
  const recorderStartingRef = useRef(false);
  const deferredStopTimeoutRef = useRef<number | null>(null);
  const maxRecordingTimeoutRef = useRef<number | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // VAD state (frame-based detection)
  const activationFramesRef = useRef(0);
  const deactivationFramesRef = useRef(0);
  const utteranceActiveRef = useRef(false);
  const frameCountRef = useRef(0); // For periodic logging
  const stateRef = useRef<VoiceState>(state); // Ref for animation frame loop
  const vadStatusRef = useRef<'idle' | 'active' | 'paused'>('idle');

  const setVoiceState = useCallback((next: VoiceState) => {
    if (stateRef.current === next) {
      return;
    }
    console.info(`🧠 State transition: ${stateRef.current} → ${next}`);
    stateRef.current = next;
    setState(next);
  }, []);

  const clearDeferredStopTimeout = useCallback(() => {
    if (deferredStopTimeoutRef.current !== null) {
      clearTimeout(deferredStopTimeoutRef.current);
      deferredStopTimeoutRef.current = null;
    }
  }, []);

  const clearMaxRecordingTimeout = useCallback(() => {
    if (maxRecordingTimeoutRef.current !== null) {
      clearTimeout(maxRecordingTimeoutRef.current);
      maxRecordingTimeoutRef.current = null;
    }
  }, []);

  // Keep stateRef in sync with state
  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  // Keep sessionIdRef in sync with sessionId
  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  /**
   * 🔁 Retry helper with exponential backoff
   */
  const retryWithBackoff = async <T,>(
    fn: () => Promise<T>,
    attempts: number = SESSION_RETRY_ATTEMPTS,
    delay: number = SESSION_RETRY_DELAY_MS
  ): Promise<T> => {
    for (let i = 0; i < attempts; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === attempts - 1) throw error;
        const backoffDelay = delay * Math.pow(2, i);
        console.log(`⏳ Retry attempt ${i + 1}/${attempts} after ${backoffDelay}ms...`);
        await new Promise((resolve) => setTimeout(resolve, backoffDelay));
      }
    }
    throw new Error('Retry exhausted');
  };

  /**
   * 🔄 Reset inactivity timer
   */
  const resetInactivityTimer = useCallback(() => {
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current);
    }

    inactivityTimeoutRef.current = setTimeout(() => {
      console.log('⏰ Inactivity timeout reached - stopping session');
      stopSession();
    }, INACTIVITY_TIMEOUT_MS);
  }, []);

  /**
   * 🎙️ Start recording audio
   */
  const startRecording = useCallback(() => {
    if (!streamRef.current || utteranceActiveRef.current || recorderStartingRef.current) {
      return;
    }

    const mimeType = getSupportedMimeType(PREFERRED_MIME_TYPE, FALLBACK_MIME_TYPES);
    if (!mimeType) {
      onError('Your browser does not support audio recording');
      return;
    }

    console.log('🔴 Starting recording');
    setIsUserSpeaking(true);
    utteranceActiveRef.current = true;
    recorderStartingRef.current = true;
    recordingStartTimeRef.current = Date.now();
    audioChunksRef.current = [];
    clearDeferredStopTimeout();
    clearMaxRecordingTimeout();

    const mediaRecorder = new MediaRecorder(streamRef.current, { mimeType });
    mediaRecorderRef.current = mediaRecorder;

    mediaRecorder.onstart = () => {
      console.log('🎬 Recorder armed');
      recorderStartingRef.current = false;
    };

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      clearMaxRecordingTimeout();
      clearDeferredStopTimeout();
      recorderStartingRef.current = false;
      const duration = Date.now() - (recordingStartTimeRef.current || 0);
      console.log(`⏹️ Recording stopped - Duration: ${duration}ms`);
      setIsUserSpeaking(false);
      utteranceActiveRef.current = false;
      console.log('🧹 Recorder teardown complete');

      // Validate recording duration
      if (duration < MIN_RECORDING_DURATION_MS) {
        console.log('⚠️ Recording too short - discarding');
        return;
      }

      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      console.log(`📦 Audio blob created: ${(audioBlob.size / 1024).toFixed(2)} KB`);

      // Send to backend (use ref to get current sessionId)
      const currentSessionId = sessionIdRef.current;
      if (!currentSessionId) {
        console.error('❌ No session ID - this should never happen!');
        console.error(`   sessionId state: ${sessionId}, sessionIdRef: ${sessionIdRef.current}`);
        onError('Session error. Please refresh and try again.');
        setVoiceState('listening');
        return;
      }

      setVoiceState('processing');
      try {
        console.log(`📤 Sending to backend with session: ${currentSessionId.slice(0, 8)}...`);
        const response = await processVoice(audioBlob, currentSessionId);
        console.log(`✅ Response received from Rose`);
        onResponse(response);
      } catch (err) {
        console.error('❌ Voice processing error:', err);
        onError('Failed to process your voice. Please try again.');
      } finally {
        if (stateRef.current !== 'idle') {
          setVoiceState('listening');
        } else {
          console.info('🧠 Skipping listening resume - session already idle');
        }
      }
    };

    mediaRecorder.start();

    // Auto-stop after max duration
    maxRecordingTimeoutRef.current = window.setTimeout(() => {
      if (mediaRecorder.state === 'recording') {
        console.log('⏱️ Max recording duration reached - stopping');
        stopRecording();
      }
    }, MAX_RECORDING_DURATION_MS);
  }, [
    onResponse,
    onError,
    clearDeferredStopTimeout,
    clearMaxRecordingTimeout,
    setVoiceState,
    sessionId,
  ]);

  /**
   * 🛑 Stop recording audio
   */
  const stopRecording = useCallback(() => {
    if (!utteranceActiveRef.current || !mediaRecorderRef.current) return;

    const duration = Date.now() - (recordingStartTimeRef.current || 0);
    if (duration < MIN_RECORDING_DURATION_MS) {
      const remaining = MIN_RECORDING_DURATION_MS - duration;
      if (deferredStopTimeoutRef.current === null) {
        console.log(
          `⏳ Recording needs ${remaining}ms more before stopping (elapsed ${duration}ms)`
        );
        deferredStopTimeoutRef.current = window.setTimeout(() => {
          deferredStopTimeoutRef.current = null;
          stopRecording();
        }, remaining);
      }
      return;
    }

    console.log('🛑 Stopping recording');
    clearMaxRecordingTimeout();
    clearDeferredStopTimeout();

    if (mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, [clearMaxRecordingTimeout, clearDeferredStopTimeout]);

  /**
   * 🔊 VAD analysis loop (runs at 60fps)
   */
  const analyzeAudio = useCallback(() => {
    // Early exit check with logging
    if (!analyserRef.current || stateRef.current !== 'listening') {
      if (vadStatusRef.current === 'active') {
        console.info(`🟡 VAD paused (state: ${stateRef.current})`);
        vadStatusRef.current = 'paused';
      }
      animationFrameRef.current = null;
      return;
    }

    if (vadStatusRef.current !== 'active') {
      console.info('🟢 VAD resumed');
      vadStatusRef.current = 'active';
    }

    const analyser = analyserRef.current;
    const bufferLength = analyser.fftSize;
    const dataArray = new Float32Array(bufferLength);
    analyser.getFloatTimeDomainData(dataArray);

    // Calculate RMS amplitude
    const rms = calculateRms(dataArray);
    setUserAmplitude(rms);

    // Periodic diagnostic logging (every 60 frames = 1 second at 60fps)
    frameCountRef.current += 1;
    if (frameCountRef.current >= STATUS_LOG_FRAME_INTERVAL) {
      console.log(
        `🔊 VAD Status: RMS=${rms.toFixed(4)} | ` +
        `Threshold=${RMS_ACTIVATION_THRESHOLD} | ` +
        `ActivationFrames=${activationFramesRef.current} | ` +
        `IsRecording=${utteranceActiveRef.current} | ` +
        `State=${stateRef.current}`
      );
      frameCountRef.current = 0;
    }

    // Log first frame to confirm loop is working
    if (frameCountRef.current === 1) {
      console.log(`✅ VAD Loop active! First RMS reading: ${rms.toFixed(4)}`);
    }

    // Frame-based VAD with hysteresis
    if (rms >= RMS_ACTIVATION_THRESHOLD) {
      activationFramesRef.current += 1;
      deactivationFramesRef.current = 0;

      // Log when we're detecting potential speech
      if (activationFramesRef.current === 1 && !utteranceActiveRef.current) {
        console.log(`📈 Speech detected! RMS=${rms.toFixed(4)}, need ${ACTIVATION_FRAMES_REQUIRED} frames to start`);
      }
    } else if (rms <= RMS_DEACTIVATION_THRESHOLD) {
      deactivationFramesRef.current += 1;
      activationFramesRef.current = 0;
    } else {
      // Hysteresis: decay both counters in middle range
      activationFramesRef.current = Math.max(activationFramesRef.current - 1, 0);
      deactivationFramesRef.current = Math.max(deactivationFramesRef.current - 1, 0);
    }

    // Trigger recording start/stop
    const shouldStart =
      !utteranceActiveRef.current &&
      activationFramesRef.current >= ACTIVATION_FRAMES_REQUIRED;

    const shouldStop =
      utteranceActiveRef.current &&
      deactivationFramesRef.current >= DEACTIVATION_FRAMES_REQUIRED;

    if (shouldStart) {
      resetInactivityTimer();
      startRecording();
    } else if (shouldStop) {
      stopRecording();
    }

    // Continue loop
    animationFrameRef.current = requestAnimationFrame(analyzeAudio);
  }, [startRecording, stopRecording, resetInactivityTimer]);

  const startVadLoop = useCallback(() => {
    if (animationFrameRef.current !== null) return;
    console.info('▶️ VAD loop scheduled');
    animationFrameRef.current = requestAnimationFrame(analyzeAudio);
  }, [analyzeAudio]);

  const stopVadLoop = useCallback(() => {
    if (animationFrameRef.current === null) return;
    cancelAnimationFrame(animationFrameRef.current);
    animationFrameRef.current = null;
    if (vadStatusRef.current !== 'idle') {
      console.info(`⏹️ VAD loop halted (state: ${stateRef.current})`);
    }
    vadStatusRef.current = 'idle';
    frameCountRef.current = 0;
  }, []);

  useEffect(() => {
    if (state === 'listening') {
      startVadLoop();
    } else {
      stopVadLoop();
    }
  }, [state, startVadLoop, stopVadLoop]);

  /**
   * ▶️ Start voice session
   */
  const startSession = useCallback(async () => {
    if (state !== 'idle') return;

    console.log('🎤 Starting voice session');
    setError(null);

    try {
      // Step 1: Create session with retry logic (if not already exists)
      if (!sessionId) {
        console.log('🎫 No existing session - creating new one...');
        try {
          const sessionResponse = await retryWithBackoff(() => createSession());
          const newSessionId = sessionResponse.session_id;
          setSessionId(newSessionId);
          console.log(`✅ Session established: ${newSessionId.slice(0, 8)}...`);
          console.log(`   sessionIdRef will be: ${newSessionId.slice(0, 8)}...`);
        } catch (sessionError) {
          console.error('❌ Failed to create session after retries:', sessionError);
          onError('Unable to connect to Rose. Please check your connection and try again.');
          return;
        }
      } else {
        console.log(`♻️ Reusing existing session: ${sessionId.slice(0, 8)}...`);
      }

      // Step 2: Request microphone access
      console.log('🎙️ Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      console.log('✅ Microphone access granted');

      // Step 3: Create audio analyzer for VAD
      const { audioContext, analyser } = createAudioAnalyzer(
        stream,
        ANALYSER_FFT_SIZE,
        ANALYSER_SMOOTHING
      );

      if (audioContext.state === 'suspended') {
        console.log('⏯️ Resuming microphone AudioContext');
        try {
          await audioContext.resume();
        } catch (resumeError) {
          console.error('❌ Failed to resume AudioContext', resumeError);
          throw resumeError;
        }
      }

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      setVoiceState('listening');

      // Step 4: Start VAD loop
      // Step 5: Start inactivity timer
      resetInactivityTimer();

      console.log('✅ Voice session fully initialized and ready');
    } catch (err) {
      console.error('❌ Failed to start voice session:', err);
      onError('Failed to access microphone. Please check permissions.');
    }
  }, [state, sessionId, resetInactivityTimer, onError, setVoiceState]);

  /**
   * ⏹️ Stop voice session
   */
  const stopSession = useCallback(() => {
    console.log('⏹️ Stopping voice session');

    // Stop recording if active
    if (utteranceActiveRef.current) {
      stopRecording();
    }

    // Stop VAD loop
    stopVadLoop();

    // Clear inactivity timer
    if (inactivityTimeoutRef.current) {
      clearTimeout(inactivityTimeoutRef.current);
      inactivityTimeoutRef.current = null;
    }

    clearDeferredStopTimeout();
    clearMaxRecordingTimeout();

    // Stop stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Reset state
    analyserRef.current = null;
    mediaRecorderRef.current = null;
    activationFramesRef.current = 0;
    deactivationFramesRef.current = 0;
    utteranceActiveRef.current = false;
    setUserAmplitude(0);
    setIsUserSpeaking(false);
    setVoiceState('idle');

    console.log('✅ Voice session stopped');
  }, [
    stopRecording,
    stopVadLoop,
    clearDeferredStopTimeout,
    clearMaxRecordingTimeout,
    setVoiceState,
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopSession();
    };
  }, [stopSession]);

  return {
    state,
    userAmplitude,
    isUserSpeaking,
    startSession,
    stopSession,
    sessionId,
    error,
  };
}
