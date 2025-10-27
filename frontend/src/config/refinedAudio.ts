/**
 * Refined Audio Configuration
 * Task 22.3: Optimize audio experience
 * 
 * This file contains refined audio settings for ambient audio, voice interaction,
 * and audio analysis to ensure optimal quality and synchronization.
 */

/**
 * Ambient Audio Configuration
 * Settings for background atmospheric audio
 */
export const refinedAmbientAudioConfig = {
  // Default audio file
  defaultAudioUrl: '/assets/audio/ambient-ocean.mp3',
  
  // Volume settings (0-1 range)
  defaultVolume: 0.25,          // Reduced from 0.3 for less intrusive background
  duckingVolume: 0.08,          // Reduced from 0.1 for better voice clarity
  minVolume: 0.0,
  maxVolume: 0.5,               // Cap at 50% to prevent overwhelming
  
  // Fade transitions (milliseconds)
  fadeInDuration: 2500,         // Increased from 2000 for smoother entry
  fadeOutDuration: 1200,        // Increased from 1000 for smoother exit
  duckingFadeIn: 400,           // Reduced from 500 for quicker duck
  duckingFadeOut: 600,          // Increased from 500 for smoother unduck
  
  // Playback settings
  loop: true,
  preload: 'auto' as const,
  autoPlay: true,
  autoPlayDelay: 800,           // Increased from 500 for better initialization
  
  // Quality settings
  preferredFormat: 'mp3' as const,
  fallbackFormats: ['ogg', 'wav'] as const,
} as const;

/**
 * Voice Recording Configuration
 * Settings for microphone input and recording
 */
export const refinedVoiceRecordingConfig = {
  // MediaRecorder settings
  mimeType: {
    preferred: 'audio/webm',
    fallbacks: ['audio/mp4', 'audio/ogg'],
  },
  
  // Audio constraints for getUserMedia
  audioConstraints: {
    echoCancellation: true,
    noiseSuppression: true,
    autoGainControl: true,
    sampleRate: 48000,          // Increased from 44100 for better quality
    channelCount: 1,            // Mono for voice
    latency: 0.01,              // Low latency for responsive feel
  },
  
  // Recording settings
  timeslice: 100,               // Collect data every 100ms for smoother processing
  maxRecordingDuration: 60000,  // 60 seconds max
  minRecordingDuration: 500,    // 0.5 seconds min to avoid accidental taps
  
  // Error handling
  retryAttempts: 2,
  retryDelay: 1000,
  errorResetDelay: 3000,
} as const;

/**
 * Audio Playback Configuration
 * Settings for Rose's voice responses
 */
export const refinedAudioPlaybackConfig = {
  // Playback settings
  defaultVolume: 1.0,           // Full volume for voice
  preload: 'auto' as const,
  crossOrigin: 'anonymous' as const,
  
  // Buffering
  bufferAhead: 2,               // Seconds to buffer ahead
  
  // Error handling
  maxRetries: 3,
  retryDelay: 500,
  timeoutDuration: 10000,       // 10 second timeout for loading
  
  // Synchronization
  syncTolerance: 50,            // Milliseconds of acceptable sync drift
  syncCheckInterval: 100,       // Check sync every 100ms
} as const;

/**
 * Audio Analysis Configuration
 * Settings for Web Audio API analyzer
 */
export const refinedAudioAnalysisConfig = {
  // FFT settings
  fftSize: 512,                 // Increased from 256 for better frequency resolution
  smoothingTimeConstant: 0.85,  // Increased from 0.8 for smoother analysis
  minDecibels: -85,             // Adjusted from -90 for better sensitivity
  maxDecibels: -15,             // Adjusted from -10 for better range
  
  // Analysis parameters
  updateInterval: 16,           // ~60fps update rate (milliseconds)
  amplitudeSmoothing: 0.7,      // Smooth amplitude changes
  frequencySmoothing: 0.8,      // Smooth frequency changes
  
  // Amplitude calculation
  amplitudeMethod: 'rms' as const, // 'rms' or 'peak' or 'average'
  amplitudeRange: {
    min: 0.0,
    max: 1.0,
  },
  
  // Frequency detection
  frequencyRange: {
    min: 80,                    // Hz - human voice lower bound
    max: 3000,                  // Hz - human voice upper bound
  },
  
  // Noise gate (ignore very quiet sounds)
  noiseGate: 0.02,              // Amplitude threshold below which to ignore
  
  // Performance
  enableWaveform: false,        // Disable waveform data if not needed
  enableFrequencyBands: true,   // Enable frequency band analysis
} as const;

/**
 * Audio Ducking Configuration
 * Settings for volume ducking during conversation
 */
export const refinedAudioDuckingConfig = {
  // Ducking triggers
  duckOnListening: true,        // Duck when user is speaking
  duckOnProcessing: false,      // Don't duck during processing
  duckOnSpeaking: true,         // Duck when Rose is speaking
  
  // Ducking levels
  listeningDuckLevel: 0.15,     // 15% volume when listening
  speakingDuckLevel: 0.08,      // 8% volume when Rose speaks (better clarity)
  
  // Timing
  duckDelay: 100,               // Delay before ducking (ms)
  unduckDelay: 300,             // Delay before unducking (ms)
  duckDuration: 400,            // Duration of duck transition (ms)
  unduckDuration: 600,          // Duration of unduck transition (ms)
  
  // Smoothing
  useSmoothDucking: true,       // Use smooth transitions
  duckingCurve: 'exponential' as const, // 'linear' or 'exponential'
} as const;

/**
 * Audio Synchronization Configuration
 * Settings for audio-visual sync
 */
export const refinedAudioSyncConfig = {
  // Sync timing
  visualDelay: 0,               // Milliseconds to delay visuals (0 = no delay)
  audioDelay: 0,                // Milliseconds to delay audio (0 = no delay)
  
  // Sync tolerance
  maxDrift: 100,                // Maximum acceptable drift (ms)
  syncCheckInterval: 200,       // Check sync every 200ms
  
  // Correction
  autoCorrect: true,            // Automatically correct drift
  correctionThreshold: 50,      // Correct if drift exceeds this (ms)
  correctionSpeed: 0.1,         // Speed of correction (0-1)
  
  // Visual response timing
  rippleResponseDelay: 20,      // Delay ripple response slightly for natural feel
  glowResponseDelay: 10,        // Minimal delay for glow response
  auroraResponseDelay: 50,      // Longer delay for aurora (atmospheric)
} as const;

/**
 * Audio Quality Presets
 * Different quality levels for various devices
 */
export const audioQualityPresets = {
  high: {
    ambientAudio: {
      enabled: true,
      volume: refinedAmbientAudioConfig.defaultVolume,
      quality: 'high',
    },
    voiceRecording: {
      sampleRate: 48000,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
    audioAnalysis: {
      fftSize: 512,
      updateInterval: 16,
      enableWaveform: false,
    },
  },
  
  medium: {
    ambientAudio: {
      enabled: true,
      volume: refinedAmbientAudioConfig.defaultVolume,
      quality: 'medium',
    },
    voiceRecording: {
      sampleRate: 44100,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
    audioAnalysis: {
      fftSize: 256,
      updateInterval: 33,
      enableWaveform: false,
    },
  },
  
  low: {
    ambientAudio: {
      enabled: true,
      volume: refinedAmbientAudioConfig.defaultVolume * 0.8,
      quality: 'low',
    },
    voiceRecording: {
      sampleRate: 44100,
      echoCancellation: true,
      noiseSuppression: false,
      autoGainControl: true,
    },
    audioAnalysis: {
      fftSize: 128,
      updateInterval: 50,
      enableWaveform: false,
    },
  },
} as const;

/**
 * Audio Error Messages
 * User-friendly error messages for common audio issues
 */
export const audioErrorMessages = {
  microphonePermissionDenied: 
    "I need access to your microphone to hear you. Please allow microphone access in your browser settings.",
  microphoneNotFound: 
    "I couldn't find a microphone. Please check that your microphone is connected and try again.",
  microphoneInUse: 
    "Your microphone is being used by another application. Please close other apps and try again.",
  recordingFailed: 
    "I had trouble recording your voice. Please try again.",
  playbackFailed: 
    "I couldn't play my response. Please check your audio settings and try again.",
  audioLoadFailed: 
    "I had trouble loading the audio. Please check your connection and try again.",
  audioContextFailed: 
    "I had trouble initializing audio. Please refresh the page and try again.",
  ambientAudioFailed: 
    "I couldn't load the ambient audio. The experience will continue without background sounds.",
  networkError: 
    "I couldn't reach the server. Please check your internet connection and try again.",
  timeout: 
    "The request took too long. Please try again.",
  unknown: 
    "Something went wrong. Please try again.",
} as const;

/**
 * Audio Feature Flags
 * Enable/disable specific audio features
 */
export const audioFeatureFlags = {
  enableAmbientAudio: true,
  enableAudioDucking: true,
  enableAudioAnalysis: true,
  enableAudioVisualization: true,
  enableEchoCancellation: true,
  enableNoiseSuppression: true,
  enableAutoGainControl: true,
  enableSpatialAudio: false,      // Future feature
  enableAudioEffects: false,      // Future feature
} as const;
