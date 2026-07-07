/**
 * 🔊 Audio Analysis Utilities
 *
 * Functions for real-time audio analysis and voice activity detection (VAD).
 */

/**
 * Calculate Root Mean Square (RMS) amplitude from audio samples.
 * RMS gives us a measure of the "loudness" of the audio signal.
 *
 * @param samples - Float32Array of audio samples from AnalyserNode
 * @returns RMS value (0.0 to 1.0+)
 */
export function calculateRms(samples: Float32Array): number {
  if (samples.length === 0) return 0;

  let sum = 0;
  for (let i = 0; i < samples.length; i++) {
    sum += samples[i] * samples[i];
  }
  return Math.sqrt(sum / samples.length);
}

/**
 * Get the best supported audio MIME type for MediaRecorder.
 *
 * @param preferredType - Preferred MIME type
 * @param fallbacks - Array of fallback MIME types
 * @returns Supported MIME type or empty string if none supported
 */
export function getSupportedMimeType(
  preferredType: string,
  fallbacks: string[]
): string {
  if (MediaRecorder.isTypeSupported(preferredType)) {
    return preferredType;
  }

  for (const mimeType of fallbacks) {
    if (MediaRecorder.isTypeSupported(mimeType)) {
      return mimeType;
    }
  }

  console.warn('⚠️ No supported MIME types found for MediaRecorder');
  return '';
}

/**
 * Check if the browser supports the required Web Audio APIs.
 *
 * @returns Object with support status for each API
 */
export function checkAudioSupport() {
  const audioWindow = window as typeof window & { webkitAudioContext?: typeof AudioContext };

  return {
    mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
    audioContext: !!(window.AudioContext || audioWindow.webkitAudioContext),
    mediaRecorder: !!window.MediaRecorder,
  };
}

/**
 * Create an audio analyzer from a media stream.
 *
 * @param stream - MediaStream from getUserMedia
 * @param fftSize - FFT size for frequency analysis
 * @param smoothing - Smoothing time constant (0-1)
 * @returns Object with AudioContext and AnalyserNode
 */
export function createAudioAnalyzer(
  stream: MediaStream,
  fftSize: number,
  smoothing: number
) {
  const audioContext = new AudioContext();
  const source = audioContext.createMediaStreamSource(stream);
  const analyser = audioContext.createAnalyser();

  analyser.fftSize = fftSize;
  analyser.smoothingTimeConstant = smoothing;

  source.connect(analyser);
  // Don't connect to destination - we don't want audio feedback

  return { audioContext, analyser, source };
}

/**
 * Create an audio analyzer from an HTMLAudioElement for playback analysis.
 *
 * @param audioElement - HTMLAudioElement playing Rose's voice
 * @param fftSize - FFT size for frequency analysis
 * @param smoothing - Smoothing time constant (0-1)
 * @returns Object with AudioContext and AnalyserNode
 */
export function createPlaybackAnalyzer(
  audioElement: HTMLAudioElement,
  fftSize: number,
  smoothing: number
) {
  const audioContext = new AudioContext();
  const source = audioContext.createMediaElementSource(audioElement);
  const analyser = audioContext.createAnalyser();

  analyser.fftSize = fftSize;
  analyser.smoothingTimeConstant = smoothing;

  source.connect(analyser);
  analyser.connect(audioContext.destination); // Connect to destination for playback

  return { audioContext, analyser, source };
}
