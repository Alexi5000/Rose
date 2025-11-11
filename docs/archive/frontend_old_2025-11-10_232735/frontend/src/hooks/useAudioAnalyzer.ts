import { useState, useEffect, useRef, useCallback } from 'react';
import { refinedAudioAnalysisConfig } from '../config/refinedAudio';

/**
 * useAudioAnalyzer Hook
 * 
 * Sets up Web Audio API analyzer to extract amplitude and frequency data
 * Provides real-time audio data for visual effects synchronization
 * 
 * Task 22.3: Enhanced with refined analysis settings for better quality
 * 
 * Optimized for performance with configurable analysis parameters
 * 
 * Requirements: 4.1, 4.2
 */

interface AudioAnalyzerData {
  amplitude: number; // 0-1, overall volume level
  frequency: number; // Dominant frequency in Hz
  frequencyData: Uint8Array; // Raw frequency data for advanced visualizations
  waveformData: Uint8Array; // Raw waveform data
}

interface UseAudioAnalyzerOptions {
  fftSize?: number; // FFT size for frequency analysis
  smoothingTimeConstant?: number; // Smoothing for frequency data
  minDecibels?: number; // Minimum decibels
  maxDecibels?: number; // Maximum decibels
  enabled?: boolean; // Enable/disable analyzer
}

export const useAudioAnalyzer = (
  audioElement: HTMLAudioElement | null,
  options: UseAudioAnalyzerOptions = {}
) => {
  const {
    fftSize = refinedAudioAnalysisConfig.fftSize,
    smoothingTimeConstant = refinedAudioAnalysisConfig.smoothingTimeConstant,
    minDecibels = refinedAudioAnalysisConfig.minDecibels,
    maxDecibels = refinedAudioAnalysisConfig.maxDecibels,
    enabled = true,
  } = options;

  const [audioData, setAudioData] = useState<AudioAnalyzerData>({
    amplitude: 0,
    frequency: 0,
    frequencyData: new Uint8Array(0),
    waveformData: new Uint8Array(0),
  });

  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * Initialize Web Audio API analyzer
   */
  const initializeAnalyzer = useCallback(() => {
    if (!audioElement || !enabled || isInitializedRef.current) return;

    try {
      // Create audio context
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;

      // Create analyser node
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = fftSize;
      analyser.smoothingTimeConstant = smoothingTimeConstant;
      analyser.minDecibels = minDecibels;
      analyser.maxDecibels = maxDecibels;
      analyserRef.current = analyser;

      // Create source from audio element
      const source = audioContext.createMediaElementSource(audioElement);
      sourceRef.current = source;

      // Connect: source → analyser → destination
      source.connect(analyser);
      analyser.connect(audioContext.destination);

      isInitializedRef.current = true;

      // Start analysis loop
      startAnalysis();
    } catch (err) {
      console.error('Error initializing audio analyzer:', err);
    }
  }, [audioElement, enabled, fftSize, smoothingTimeConstant, minDecibels, maxDecibels]);

  /**
   * Analyze audio data in animation frame loop
   */
  const analyze = useCallback(() => {
    if (!analyserRef.current || !enabled) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const frequencyData = new Uint8Array(bufferLength);
    const waveformData = new Uint8Array(bufferLength);

    // Get frequency data
    analyser.getByteFrequencyData(frequencyData);
    
    // Get waveform data
    analyser.getByteTimeDomainData(waveformData);

    // Calculate amplitude (average of all frequency bins, normalized to 0-1)
    // Apply noise gate to filter out very quiet sounds
    const sum = frequencyData.reduce((acc, val) => acc + val, 0);
    let amplitude = sum / bufferLength / 255;
    
    // Apply noise gate
    if (amplitude < refinedAudioAnalysisConfig.noiseGate) {
      amplitude = 0;
    }

    // Calculate dominant frequency
    let maxValue = 0;
    let maxIndex = 0;
    for (let i = 0; i < bufferLength; i++) {
      if (frequencyData[i] > maxValue) {
        maxValue = frequencyData[i];
        maxIndex = i;
      }
    }
    
    // Convert index to frequency (Hz)
    const nyquist = (audioContextRef.current?.sampleRate || 44100) / 2;
    const frequency = (maxIndex / bufferLength) * nyquist;

    setAudioData({
      amplitude,
      frequency,
      frequencyData,
      waveformData,
    });

    // Continue analysis loop
    animationFrameRef.current = requestAnimationFrame(analyze);
  }, [enabled]);

  /**
   * Start analysis loop
   */
  const startAnalysis = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    animationFrameRef.current = requestAnimationFrame(analyze);
    setIsAnalyzing(true);
  }, [analyze]);

  /**
   * Stop analysis loop
   */
  const stopAnalysis = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    setIsAnalyzing(false);
  }, []);

  /**
   * Initialize analyzer when audio element is available
   */
  useEffect(() => {
    if (audioElement && enabled && !isInitializedRef.current) {
      // Wait for audio to be ready
      const handleCanPlay = () => {
        initializeAnalyzer();
      };

      if (audioElement.readyState >= 2) {
        // Audio is already ready
        initializeAnalyzer();
      } else {
        audioElement.addEventListener('canplay', handleCanPlay);
        return () => {
          audioElement.removeEventListener('canplay', handleCanPlay);
        };
      }
    }
  }, [audioElement, enabled, initializeAnalyzer]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stopAnalysis();
      
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      
      isInitializedRef.current = false;
    };
  }, [stopAnalysis]);

  return {
    // Audio data
    amplitude: audioData.amplitude,
    frequency: audioData.frequency,
    frequencyData: audioData.frequencyData,
    waveformData: audioData.waveformData,

    // Controls
    startAnalysis,
    stopAnalysis,

    // Status
    isAnalyzing,
  };
};
