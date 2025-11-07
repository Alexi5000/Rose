const MILLISECONDS_PER_SECOND = 1000;
const SECONDS_PER_MINUTE = 60;

export const DURATION_TOKENS = Object.freeze({
  unitMs: MILLISECONDS_PER_SECOND,
  voiceBurstWindowMs: 3.5 * MILLISECONDS_PER_SECOND,
  silenceHangoverMs: 1.2 * MILLISECONDS_PER_SECOND,
  minUtteranceMs: 0.7 * MILLISECONDS_PER_SECOND,
  maxUtteranceMs: 45 * MILLISECONDS_PER_SECOND,
  sessionActiveWindowMs: 5 * SECONDS_PER_MINUTE * MILLISECONDS_PER_SECOND,
  sessionInactivityGraceMs: 15 * MILLISECONDS_PER_SECOND,
  playbackAutoplayRetryMs: 2 * MILLISECONDS_PER_SECOND,
} as const);

export const DETECTION_TOKENS = Object.freeze({
  analyserFftSize: 2048,
  rmsActivationThreshold: 0.015,
  rmsDeactivationThreshold: 0.007,
  consecutiveActivationFrames: 4,
  consecutiveDeactivationFrames: 6,
} as const);

export const LOG_TOKENS = Object.freeze({
  prefixActivate: '🚀 Voice session activated',
  prefixMute: '🛑 Voice session muted',
  prefixUtteranceStart: '🎤 Capturing utterance',
  prefixUtteranceDiscard: '🗑️ Ignored utterance',
  prefixUtteranceQueue: '📬 Queued utterance',
  prefixProcessing: '🧠 Processing utterance',
  prefixSpeaking: '🗣️ Playing response',
  prefixRecovery: '🔁 Playback recovery',
} as const);

export const ERROR_TOKENS = Object.freeze({
  sessionMissing: '🆘 Session unavailable. Please refresh.',
  streamUnavailable: '🎙️ Microphone unavailable. Check permissions.',
  activationFailed: '⚠️ Could not start voice session. Please retry.',
} as const);

export const AUDIO_NAMING_TOKENS = Object.freeze({
  utteranceBlobName: 'utterance.webm',
});

export const AUDIO_ENGINE_TOKENS = Object.freeze({
  bitsPerSample: 16,
  monoChannels: 1,
} as const);
