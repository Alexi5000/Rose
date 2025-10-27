/**
 * Error Message Constants
 * 
 * Centralized user-facing error messages with emoji indicators
 * for consistent error handling across the application.
 * 
 * Requirements: 6.1, 6.4, 7.1, 7.2, 7.3, 7.4
 */

// 🔌 Connection and Network Errors
export const CONNECTION_ERRORS = {
  NO_INTERNET: '🔌 No internet connection. Please check your network and try again.',
  BACKEND_UNREACHABLE: '🔌 Cannot connect to Rose. Please ensure the server is running.',
  TIMEOUT: '⏱️ Request timed out. The server is taking too long to respond. Please try again.',
  SERVER_ERROR: '❌ Server error occurred. Please try again in a moment.',
  NETWORK_ERROR: '🔌 Network error. Please check your connection and try again.',
} as const

// 🎤 Microphone and Recording Errors
export const MICROPHONE_ERRORS = {
  PERMISSION_DENIED: '🎤 Microphone access denied. Please allow microphone access in your browser settings.',
  NOT_FOUND: '🎤 No microphone found. Please connect a microphone and try again.',
  IN_USE: '🎤 Microphone is already in use by another application.',
  NOT_READABLE: '🎤 Cannot access microphone. Please check your device settings.',
  GENERIC_ERROR: '🎤 Microphone error. Please check your device and try again.',
} as const

// 🎙️ Voice Processing Errors
export const VOICE_PROCESSING_ERRORS = {
  TRANSCRIPTION_FAILED: '🎤 I couldn\'t hear that clearly. Could you try again?',
  AUDIO_TOO_SHORT: '🎤 Recording too short. Please speak for at least 1 second.',
  AUDIO_TOO_LARGE: '🎤 Audio file is too large. Please record a shorter message.',
  PROCESSING_FAILED: '🎤 Failed to process your voice. Please try again.',
  INVALID_AUDIO: '🎤 Invalid audio format. Please try recording again.',
} as const

// 🔊 Audio Playback Errors
export const PLAYBACK_ERRORS = {
  PLAYBACK_FAILED: '🔊 Failed to play audio response. Please check your speakers.',
  AUDIO_LOAD_FAILED: '🔊 Failed to load audio. Please try again.',
  AUDIO_DECODE_FAILED: '🔊 Failed to decode audio. The audio format may not be supported.',
  AUDIO_NOT_SUPPORTED: '🔊 Your browser doesn\'t support this audio format.',
} as const

// ⏱️ Session and Authentication Errors
export const SESSION_ERRORS = {
  SESSION_EXPIRED: '⏱️ Your session has expired. Please refresh the page.',
  SESSION_INVALID: '⏱️ Invalid session. Please refresh the page.',
  SESSION_NOT_FOUND: '⏱️ Session not found. Please refresh the page.',
  SESSION_CREATION_FAILED: '⏱️ Failed to create session. Please refresh the page.',
  UNAUTHORIZED: '🔒 Unauthorized. Please refresh the page.',
} as const

// 🚫 Rate Limiting and Quota Errors
export const RATE_LIMIT_ERRORS = {
  TOO_MANY_REQUESTS: '⏱️ Too many requests. Please wait a moment and try again.',
  QUOTA_EXCEEDED: '⏱️ Usage quota exceeded. Please try again later.',
  RATE_LIMITED: '⏱️ You\'re sending requests too quickly. Please slow down.',
} as const

// 🎨 Asset Loading Errors
export const ASSET_ERRORS = {
  LOAD_FAILED: '🎨 Failed to load scene assets. Please refresh the page.',
  MODEL_LOAD_FAILED: '🎭 Failed to load 3D model. Please refresh the page.',
  TEXTURE_LOAD_FAILED: '🎨 Failed to load textures. Please refresh the page.',
  AUDIO_ASSET_LOAD_FAILED: '🎵 Failed to load audio assets. Please refresh the page.',
  CRITICAL_ASSET_FAILED: '❌ Failed to load critical assets. Please refresh the page.',
} as const

// 🏥 Health Check Errors
export const HEALTH_CHECK_ERRORS = {
  HEALTH_CHECK_FAILED: '🏥 Health check failed. The server may be down.',
  SERVICE_UNAVAILABLE: '🏥 Service temporarily unavailable. Please try again later.',
  BACKEND_NOT_READY: '🏥 Backend is starting up. Please wait a moment.',
} as const

// 🌐 WebGL and Browser Compatibility Errors
export const COMPATIBILITY_ERRORS = {
  WEBGL_NOT_SUPPORTED: '🌐 WebGL is not supported in your browser. Please use a modern browser.',
  WEBGL_DISABLED: '🌐 WebGL is disabled. Please enable it in your browser settings.',
  BROWSER_NOT_SUPPORTED: '🌐 Your browser is not supported. Please use Chrome, Firefox, or Safari.',
  FEATURE_NOT_SUPPORTED: '🌐 This feature is not supported in your browser.',
} as const

// ❓ Generic and Unknown Errors
export const GENERIC_ERRORS = {
  UNKNOWN_ERROR: '❌ An unexpected error occurred. Please try again.',
  SOMETHING_WENT_WRONG: '❌ Something went wrong. Please refresh the page.',
  OPERATION_FAILED: '❌ Operation failed. Please try again.',
  INVALID_REQUEST: '❌ Invalid request. Please try again.',
} as const

// 📋 All error messages combined for easy access
export const ERROR_MESSAGES = {
  ...CONNECTION_ERRORS,
  ...MICROPHONE_ERRORS,
  ...VOICE_PROCESSING_ERRORS,
  ...PLAYBACK_ERRORS,
  ...SESSION_ERRORS,
  ...RATE_LIMIT_ERRORS,
  ...ASSET_ERRORS,
  ...HEALTH_CHECK_ERRORS,
  ...COMPATIBILITY_ERRORS,
  ...GENERIC_ERRORS,
} as const

// 🏷️ Error categories for classification
export enum ErrorCategory {
  CONNECTION = 'connection',
  MICROPHONE = 'microphone',
  VOICE_PROCESSING = 'voice_processing',
  PLAYBACK = 'playback',
  SESSION = 'session',
  RATE_LIMIT = 'rate_limit',
  ASSET = 'asset',
  HEALTH_CHECK = 'health_check',
  COMPATIBILITY = 'compatibility',
  GENERIC = 'generic',
}

// 🔍 Error severity levels
export enum ErrorSeverity {
  INFO = 'info',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical',
}

// 📊 Error metadata for enhanced error handling
export interface ErrorMetadata {
  category: ErrorCategory
  severity: ErrorSeverity
  isTransient: boolean // Should auto-dismiss after timeout
  isDismissible: boolean // Can user manually dismiss
  retryable: boolean // Can user retry the operation
  requiresRefresh: boolean // Requires page refresh to fix
}

// 🗺️ Error message to metadata mapping
export const ERROR_METADATA_MAP: Record<string, ErrorMetadata> = {
  // Connection errors - transient, retryable
  [CONNECTION_ERRORS.NO_INTERNET]: {
    category: ErrorCategory.CONNECTION,
    severity: ErrorSeverity.ERROR,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  [CONNECTION_ERRORS.BACKEND_UNREACHABLE]: {
    category: ErrorCategory.CONNECTION,
    severity: ErrorSeverity.CRITICAL,
    isTransient: false,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  [CONNECTION_ERRORS.TIMEOUT]: {
    category: ErrorCategory.CONNECTION,
    severity: ErrorSeverity.WARNING,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  
  // Microphone errors - not transient, not retryable (requires user action)
  [MICROPHONE_ERRORS.PERMISSION_DENIED]: {
    category: ErrorCategory.MICROPHONE,
    severity: ErrorSeverity.ERROR,
    isTransient: false,
    isDismissible: true,
    retryable: false,
    requiresRefresh: false,
  },
  [MICROPHONE_ERRORS.NOT_FOUND]: {
    category: ErrorCategory.MICROPHONE,
    severity: ErrorSeverity.ERROR,
    isTransient: false,
    isDismissible: true,
    retryable: false,
    requiresRefresh: false,
  },
  
  // Voice processing errors - transient, retryable
  [VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED]: {
    category: ErrorCategory.VOICE_PROCESSING,
    severity: ErrorSeverity.WARNING,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  [VOICE_PROCESSING_ERRORS.AUDIO_TOO_LARGE]: {
    category: ErrorCategory.VOICE_PROCESSING,
    severity: ErrorSeverity.WARNING,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  
  // Playback errors - transient, retryable
  [PLAYBACK_ERRORS.PLAYBACK_FAILED]: {
    category: ErrorCategory.PLAYBACK,
    severity: ErrorSeverity.ERROR,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  
  // Session errors - requires refresh
  [SESSION_ERRORS.SESSION_EXPIRED]: {
    category: ErrorCategory.SESSION,
    severity: ErrorSeverity.ERROR,
    isTransient: false,
    isDismissible: true,
    retryable: false,
    requiresRefresh: true,
  },
  
  // Rate limit errors - transient, retryable after delay
  [RATE_LIMIT_ERRORS.TOO_MANY_REQUESTS]: {
    category: ErrorCategory.RATE_LIMIT,
    severity: ErrorSeverity.WARNING,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  },
  
  // Asset errors - requires refresh
  [ASSET_ERRORS.CRITICAL_ASSET_FAILED]: {
    category: ErrorCategory.ASSET,
    severity: ErrorSeverity.CRITICAL,
    isTransient: false,
    isDismissible: true,
    retryable: false,
    requiresRefresh: true,
  },
}

/**
 * Get error metadata for a given error message
 * Returns default metadata if message not found in map
 */
export function getErrorMetadata(errorMessage: string): ErrorMetadata {
  return ERROR_METADATA_MAP[errorMessage] || {
    category: ErrorCategory.GENERIC,
    severity: ErrorSeverity.ERROR,
    isTransient: true,
    isDismissible: true,
    retryable: true,
    requiresRefresh: false,
  }
}

/**
 * Check if an error should auto-dismiss
 */
export function shouldAutoDismiss(errorMessage: string): boolean {
  const metadata = getErrorMetadata(errorMessage)
  return metadata.isTransient
}

/**
 * Get auto-dismiss timeout in milliseconds
 * Returns 5000ms (5 seconds) for transient errors, null for persistent errors
 */
export function getAutoDismissTimeout(errorMessage: string): number | null {
  return shouldAutoDismiss(errorMessage) ? 5000 : null
}
