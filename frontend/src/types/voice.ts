/**
 * 🎙️ Voice Interface Types
 */

/**
 * Voice session state machine
 */
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

/**
 * Pipeline timing metrics for performance analysis
 * All values are in milliseconds
 */
export interface PipelineTimings {
  /** Time to validate audio input */
  audio_validation_ms: number;
  /** Speech-to-text transcription time */
  stt_ms: number;
  /** LangGraph workflow execution time */
  workflow_ms: number;
  /** Text-to-speech synthesis time */
  tts_ms: number;
  /** Time to save audio file */
  audio_save_ms: number;
  /** Total end-to-end processing time */
  total_ms: number;
  /** Long-term memory retrieval time */
  memory_retrieval_ms: number;
  /** LLM response generation time */
  llm_generation_ms: number;
  /** Memory extraction time */
  memory_extraction_ms: number;
}

/**
 * WebSocket voice turn timing metrics from the streaming voice path.
 * All values are in milliseconds except audio_bytes and tts_phrase_count.
 */
export interface WebSocketVoiceTimings {
  stt_provider: string;
  stt_streaming: boolean;
  stt_batch_fallback: boolean;
  audio_bytes: number;
  stt_ms: number | null;
  workflow_ms: number | null;
  tts_ms: number | null;
  tts_phrase_count: number;
  mic_to_first_audio_ms: number | null;
  turn_total_ms: number;
}

/**
 * Response from voice processing API
 */
export interface VoiceResponse {
  /** Transcribed text from user's speech */
  text: string;
  /** The user's own transcribed speech (for UI display) */
  user_text?: string;
  /** URL to Rose's audio response (MP3) */
  audio_url: string;
  /** Base64-encoded MP3 audio for inline playback (avoids extra HTTP round-trip) */
  audio_data?: string;
  /** True when WebSocket playback already streamed this response to the user */
  audio_streamed?: boolean;
  /** Reason the backend asked for more speech before normal generation */
  turn_incomplete_reason?: string;
  /** Session ID for conversation continuity */
  session_id: string;
  /** Pipeline timing metrics (optional, only when FEATURE_TIMING_METRICS is enabled) */
  timings?: PipelineTimings | WebSocketVoiceTimings;
}

export type MemoryMode = 'enabled' | 'session_only';

export interface SessionMemoryPreferences {
  session_id: string;
  memory_mode: MemoryMode;
  long_term_memory_enabled: boolean;
  message: string;
}

export interface SessionMemoryExport {
  session_id: string;
  memories: Array<Record<string, unknown>>;
  message: string;
}

export interface SessionMemoryForget {
  session_id: string;
  deleted: boolean;
  message: string;
}

/**
 * Error response from API
 */
export interface ApiError {
  /** Error message */
  detail: string;
}

/**
 * Voice session configuration
 */
export interface VoiceSessionConfig {
  /** RMS threshold for speech activation */
  activationThreshold?: number;
  /** RMS threshold for speech deactivation */
  deactivationThreshold?: number;
  /** Consecutive frames required to activate */
  activationFrames?: number;
  /** Consecutive frames required to deactivate */
  deactivationFrames?: number;
  /** Minimum recording duration in milliseconds */
  minRecordingDuration?: number;
  /** Maximum recording duration in milliseconds */
  maxRecordingDuration?: number;
  /** Inactivity timeout in milliseconds */
  inactivityTimeout?: number;
}
