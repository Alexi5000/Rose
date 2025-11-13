/**
 * 🎙️ Voice Interface Types
 */

/**
 * Voice session state machine
 */
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

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
