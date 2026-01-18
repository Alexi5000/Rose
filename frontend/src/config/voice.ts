/**
 * 🎙️ Voice Configuration Constants
 *
 * These values control the voice activity detection (VAD) and session behavior.
 * Tuned for therapeutic conversations with comfortable pacing.
 */

// 🔊 Voice Activity Detection (VAD) Thresholds
export const RMS_ACTIVATION_THRESHOLD = 0.002; // Min amplitude to consider as speech (lowered for sensitivity)
export const RMS_DEACTIVATION_THRESHOLD = 0.001; // Max amplitude to consider as silence (lowered for sensitivity)

// 🎯 Frame-Based Detection (prevents false positives)
export const ACTIVATION_FRAMES_REQUIRED = 1; // Consecutive frames above threshold to start recording (reduced for faster response)
export const DEACTIVATION_FRAMES_REQUIRED = 15; // Consecutive frames below threshold to stop recording (~250ms at 60fps - Phase 1 optimization)

// ⏱️ Recording Duration Limits
export const MIN_RECORDING_DURATION_MS = 300; // Discard recordings shorter than this (filters coughs, clicks)
export const MAX_RECORDING_DURATION_MS = 30000; // Auto-stop after 30 seconds

// ⏰ Session Timeouts
export const INACTIVITY_TIMEOUT_MS = 30000; // 30 seconds - stop listening if no speech detected (increased to give users more time)
export const SESSION_MAX_DURATION_MS = 300000; // 5 minutes - absolute max session time

// 🎚️ Audio Analysis Settings
export const ANALYSER_FFT_SIZE = 2048; // FFT size for frequency analysis
export const ANALYSER_SMOOTHING = 0.85; // Smoothing time constant (0-1, higher = smoother)

// 🎤 Audio Recording Settings
export const PREFERRED_MIME_TYPE = 'audio/webm;codecs=opus';
export const FALLBACK_MIME_TYPES = ['audio/webm', 'audio/mp4', 'audio/ogg'];
export const AUDIO_BITS_PER_SECOND = 256000; // 256kbps for good quality
export const AUDIO_SAMPLE_RATE = 16000; // 16kHz optimized for speech recognition

// 🔈 Playback + Fetch Settings
export const AUDIO_DEFAULT_VOLUME = 1.0; // Ensure Rose responses always play at full volume
export const AUDIO_FETCH_TIMEOUT_MS = 15000; // Abort audio downloads if Rose takes too long (fallback to TTS)
export const AUDIO_PLAYBACK_MAX_RETRIES = 2; // Retry count before falling back to speech synthesis

// 🗣️ Speech Synthesis Fallback (keeps the convo voice-first even if audio URLs fail)
export const SPEECH_SYNTHESIS_LANGUAGE = 'en-US';
export const SPEECH_SYNTHESIS_PITCH = 1.0;
export const SPEECH_SYNTHESIS_RATE = 0.95;

// 🎨 Visual Feedback Constants
export const ANIMATION_FRAME_RATE = 60; // fps for real-time amplitude updates
export const VAD_LOOP_INTERVAL_MS = 1000 / ANIMATION_FRAME_RATE; // ~16.67ms cadence for RAF loop diagnostics

// 🌐 API Configuration
export const API_BASE_URL = '/api/v1';
export const SESSION_START_ENDPOINT = `${API_BASE_URL}/session/start`;
export const VOICE_PROCESS_ENDPOINT = `${API_BASE_URL}/voice/process`;
export const VOICE_STREAM_TTS_ENDPOINT = `${API_BASE_URL}/voice/stream-tts`; // Phase 2: Streaming TTS
export const API_TIMEOUT_MS = 60000; // 60 seconds for voice processing
export const SESSION_RETRY_ATTEMPTS = 3; // Number of retries for session creation
export const SESSION_RETRY_DELAY_MS = 1000; // Delay between retries

// 🎛️ Feature Flags
export const ENABLE_STREAMING_TTS = true; // Phase 2: Enable streaming TTS for lower latency
