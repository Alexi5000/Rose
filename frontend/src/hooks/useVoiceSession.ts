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
import { processVoice, createSession, sanitizeApiUrlForLog } from '@/lib/api';
import { WebSocketAudioJitterBuffer } from '@/lib/ws-audio-jitter-buffer';
import type { VoiceState, VoiceResponse, WebSocketVoiceTimings } from '@/types/voice';

const STATUS_LOG_FRAME_INTERVAL = Math.max(
  1,
  Math.round(1000 / VAD_LOOP_INTERVAL_MS)
);

const createBufferedAudioUrl = (chunks: Uint8Array[]): string => {
  const totalLen = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const combined = new Uint8Array(totalLen);
  let offset = 0;
  for (const chunk of chunks) {
    combined.set(chunk, offset);
    offset += chunk.length;
  }
  const audioBytes = new Uint8Array(combined.byteLength);
  audioBytes.set(combined);
  const blob = new Blob([audioBytes.buffer], { type: 'audio/mpeg' });
  return URL.createObjectURL(blob);
};

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
  /**
   * Resume listening immediately after barge-in.
   * Unlike startSession(), this does NOT re-initialize the mic/session ,
   * it simply resets VAD state and moves to 'listening' when a stream is
   * already active. Safe to call while state === 'speaking'.
   */
  resumeListening: () => void;
  /** Inform the hook that Rose started speaking (pause VAD) */
  notifyPlaybackStart: () => void;
  /** Inform the hook that Rose finished speaking (resume VAD) */
  notifyPlaybackEnd: () => void;
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
  // P5: Initialise from localStorage so conversation context survives page reloads
  const [sessionId, setSessionId] = useState<string | null>(() => {
    try { return localStorage.getItem('rose_session_id'); } catch { return null; }
  });
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

  // 🔌 P4: WebSocket transport refs
  const wsRef = useRef<WebSocket | null>(null);
  const wsAudioChunksRef = useRef<Uint8Array[]>([]);
  const wsAudioBufferRef = useRef<WebSocketAudioJitterBuffer | null>(null);
  const wsResponseTextRef = useRef<string>('');
  const wsUserTextRef = useRef<string>('');
  const wsBlobUrlRef = useRef<string | null>(null);
  const wsAudioUnavailableRef = useRef<boolean>(false);
  const wsTurnIncompleteReasonRef = useRef<string | undefined>(undefined);
  // Stable callback refs to avoid stale closures in the WS message handler
  const onResponseRef = useRef(onResponse);
  const onErrorRef = useRef(onError);

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

  // Keep callback refs current so the WS message handler always calls the latest version
  useEffect(() => {
    onResponseRef.current = onResponse;
    onErrorRef.current = onError;
  }, [onResponse, onError]);

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
        console.error('No session ID available for voice turn');
        onError('Session error. Please refresh and try again.');
        setVoiceState('listening');
        return;
      }

      setVoiceState('processing');
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        // 🔌 WebSocket path , streaming TTS (P4)
        try {
          wsAudioChunksRef.current = [];
          wsAudioBufferRef.current?.reset();
          wsAudioBufferRef.current = new WebSocketAudioJitterBuffer();
          wsAudioBufferRef.current.start();
          wsAudioUnavailableRef.current = false;
          wsTurnIncompleteReasonRef.current = undefined;
          wsResponseTextRef.current = '';
          wsUserTextRef.current = '';
          console.log(`Sending audio via WebSocket (${audioBlob.size} bytes)`);
          const audioBytes = await audioBlob.arrayBuffer();
          ws.send(JSON.stringify({ type: 'start_listening' }));
          ws.send(audioBytes);
          ws.send(JSON.stringify({ type: 'stop_listening' }));
          // Response arrives asynchronously via ws.onmessage , no await here
        } catch (wsErr) {
          console.warn('⚠️ WebSocket send failed, trying HTTP fallback:', wsErr);
          try {
            const response = await processVoice(audioBlob, currentSessionId);
            onResponse(response);
          } catch (httpErr) {
            console.error('❌ HTTP fallback error:', httpErr);
            onError('Failed to process your voice. Please try again.');
            if (stateRef.current !== 'idle') setVoiceState('listening');
          }
        }
      } else {
        // 🌐 HTTP path , batch request (WS not ready)
        try {
          console.log('Sending audio via HTTP fallback');
          const response = await processVoice(audioBlob, currentSessionId);
          console.log(`✅ Response received from Rose`);
          onResponse(response);
        } catch (err) {
          console.error('❌ Voice processing error:', err);
          onError('Failed to process your voice. Please try again.');
          if (stateRef.current !== 'idle') setVoiceState('listening');
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

    // Throttle state updates to ~15fps (every 4th frame) to reduce re-renders.
    // The shader still gets smooth-enough animation at 15fps.
    frameCountRef.current += 1;
    if (frameCountRef.current % 4 === 0) {
      setUserAmplitude(rms);
    }
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
      // Step 1: Create or reuse session (P5: activeSessionId may be pre-loaded from localStorage)
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        console.log('🎫 No existing session - creating new one...');
        try {
          const sessionResponse = await retryWithBackoff(() => createSession());
          activeSessionId = sessionResponse.session_id;
          setSessionId(activeSessionId);
          localStorage.setItem('rose_session_id', activeSessionId); // P5: persist across reloads
          console.log('Session established');
        } catch (sessionError) {
          console.error('❌ Failed to create session after retries:', sessionError);
          onError('Unable to connect to Rose. Please check your connection and try again.');
          return;
        }
      } else {
        console.log('Reusing existing session');
      }

      // Step 2: Request microphone access
      console.log('🎙️ Requesting microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000,
        },
      });
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

      // Step 4: Connect WebSocket for streaming TTS (P4)
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/voice/ws?session_id=${activeSessionId}`;
      console.log(`Connecting WebSocket: ${sanitizeApiUrlForLog(wsUrl)}`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => console.log('🔌 WebSocket connected');
      ws.onerror = () => console.warn('⚠️ WebSocket error , falling back to HTTP');
      ws.onclose = (ev) => console.log(`🔌 WebSocket closed (code=${ev.code})`);
      ws.onmessage = async (event) => {
        const data = event.data;
        // Binary audio chunk
        if (data instanceof ArrayBuffer) {
          const chunk = new Uint8Array(data);
          wsAudioChunksRef.current.push(chunk);
          wsAudioBufferRef.current?.push(chunk);
          return;
        }
        if (data instanceof Blob) {
          data.arrayBuffer().then((buf) => {
            const chunk = new Uint8Array(buf);
            wsAudioChunksRef.current.push(chunk);
            wsAudioBufferRef.current?.push(chunk);
          });
          return;
        }
        // JSON control message
        let msg: {
          type: string;
          text?: string;
          reason?: string;
          interrupted?: boolean;
          timings?: WebSocketVoiceTimings;
        };
        try { msg = JSON.parse(data as string); } catch { return; }
        switch (msg.type) {
          case 'transcription':
            wsUserTextRef.current = msg.text || '';
            break;
          case 'turn_incomplete':
            wsTurnIncompleteReasonRef.current = msg.reason;
            break;
          case 'response':
            wsResponseTextRef.current = msg.text || '';
            break;
          case 'audio_start':
            if (!wsAudioBufferRef.current) {
              wsAudioBufferRef.current = new WebSocketAudioJitterBuffer();
              wsAudioBufferRef.current.start();
            }
            if (stateRef.current !== 'idle') {
              setVoiceState('speaking');
            }
            break;
          case 'audio_unavailable':
            wsResponseTextRef.current = msg.text || wsResponseTextRef.current;
            wsAudioUnavailableRef.current = true;
            wsAudioChunksRef.current = [];
            wsAudioBufferRef.current?.reset();
            wsAudioBufferRef.current = null;
            break;
          case 'audio_end': {
            const chunks = wsAudioChunksRef.current;
            if (msg.interrupted) {
              wsAudioChunksRef.current = [];
              wsResponseTextRef.current = '';
              wsAudioBufferRef.current?.reset();
              wsAudioBufferRef.current = null;
              wsAudioUnavailableRef.current = false;
              wsTurnIncompleteReasonRef.current = undefined;
              if (stateRef.current !== 'idle') {
                setVoiceState('listening');
                resetInactivityTimer();
              }
              break;
            }
            if (chunks.length > 0 && !wsAudioUnavailableRef.current) {
              const bufferedAudio = await wsAudioBufferRef.current?.finish();
              if (wsBlobUrlRef.current) URL.revokeObjectURL(wsBlobUrlRef.current);
              wsBlobUrlRef.current = bufferedAudio?.audioUrl || createBufferedAudioUrl(chunks);
              onResponseRef.current({
                text: wsResponseTextRef.current,
                user_text: wsUserTextRef.current,
                audio_url: wsBlobUrlRef.current,
                audio_streamed: bufferedAudio?.streamed ?? false,
                turn_incomplete_reason: wsTurnIncompleteReasonRef.current,
                session_id: sessionIdRef.current || '',
                timings: msg.timings,
              });
            } else {
              onResponseRef.current({
                text: wsResponseTextRef.current,
                user_text: wsUserTextRef.current,
                audio_url: '',
                turn_incomplete_reason: wsTurnIncompleteReasonRef.current,
                session_id: sessionIdRef.current || '',
                timings: msg.timings,
              });
            }
            wsAudioChunksRef.current = [];
            if (!wsAudioBufferRef.current?.isStreaming) {
              wsAudioBufferRef.current = null;
            }
            wsAudioUnavailableRef.current = false;
            wsTurnIncompleteReasonRef.current = undefined;
            if (stateRef.current !== 'idle') {
              setVoiceState('listening');
              resetInactivityTimer();
            }
            break;
          }
          case 'error':
            wsAudioBufferRef.current?.reset();
            wsAudioBufferRef.current = null;
            wsAudioUnavailableRef.current = false;
            wsTurnIncompleteReasonRef.current = undefined;
            onErrorRef.current(msg.text || 'Processing failed');
            if (stateRef.current !== 'idle') setVoiceState('listening');
            break;
        }
      };

      setVoiceState('listening');

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

    // Close WebSocket and clean up blob URLs (P4)
    if (wsRef.current) {
      wsRef.current.close(1000, 'session_stopped');
      wsRef.current = null;
    }
    if (wsBlobUrlRef.current) {
      URL.revokeObjectURL(wsBlobUrlRef.current);
      wsBlobUrlRef.current = null;
    }
    wsAudioBufferRef.current?.reset();
    wsAudioBufferRef.current = null;
    wsAudioChunksRef.current = [];
    wsResponseTextRef.current = '';
    wsAudioUnavailableRef.current = false;
    wsTurnIncompleteReasonRef.current = undefined;

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

  const notifyPlaybackStart = useCallback(() => {
    // Pause VAD while Rose is speaking
    if (stateRef.current !== 'idle') {
      setVoiceState('speaking');
    }
  }, [setVoiceState]);

  const notifyPlaybackEnd = useCallback(() => {
    // Resume VAD after Rose finishes
    if (stateRef.current !== 'idle') {
      setVoiceState('listening');
      resetInactivityTimer();
    }
  }, [resetInactivityTimer, setVoiceState]);

  /**
   * 🔄 Resume listening immediately (barge-in path).
   *
   * Called when the user interrupts Rose mid-speech. The mic stream and
   * AudioContext are already open; we only need to reset VAD counters and
   * flip back to 'listening' so the RAF loop re-activates.
   */
  const resumeListening = useCallback(() => {
    if (!streamRef.current || !analyserRef.current) {
      // Fallback: full session restart if the stream was somehow closed
      console.warn('⚠️ resumeListening: no active stream, falling back to startSession()');
      startSession();
      return;
    }

    // Signal interrupt to server so it stops streaming audio (P4)
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'interrupt' }));
    }
    wsAudioBufferRef.current?.reset();
    wsAudioBufferRef.current = null;
    wsAudioUnavailableRef.current = false;
    wsTurnIncompleteReasonRef.current = undefined;

    console.info('🔄 resumeListening: resetting VAD and resuming listening after barge-in');

    // Discard any in-flight recording
    if (utteranceActiveRef.current) {
      clearDeferredStopTimeout();
      clearMaxRecordingTimeout();
      if (mediaRecorderRef.current?.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      utteranceActiveRef.current = false;
    }

    // Reset VAD counters
    activationFramesRef.current = 0;
    deactivationFramesRef.current = 0;
    recorderStartingRef.current = false;
    setIsUserSpeaking(false);
    audioChunksRef.current = [];

    // Resume the state machine
    setVoiceState('listening');
    resetInactivityTimer();
  }, [
    startSession,
    clearDeferredStopTimeout,
    clearMaxRecordingTimeout,
    setVoiceState,
    resetInactivityTimer,
  ]);

  return {
    state,
    userAmplitude,
    isUserSpeaking,
    startSession,
    stopSession,
    resumeListening,
    notifyPlaybackStart,
    notifyPlaybackEnd,
    sessionId,
    error,
  };
}
