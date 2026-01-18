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
 * Response from voice processing API
 */
export interface VoiceResponse {
  /** Transcribed text from user's speech */
  text: string;
  /** URL to Rose's audio response (MP3) */
  audio_url: string;
  /** Session ID for conversation continuity */
  session_id: string;
  /** Pipeline timing metrics (optional, only when FEATURE_TIMING_METRICS is enabled) */
  timings?: PipelineTimings;
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
