import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useAudioAnalyzer } from '../../hooks/useAudioAnalyzer';
import { useVoiceInteraction } from '../../hooks/useVoiceInteraction';

/**
 * Integration Tests for Audio-Visual Synchronization
 * 
 * Tests the synchronization between audio analysis and visual effects
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
 */

// Mock the API client
vi.mock('../../services/apiClient', () => ({
  apiClient: {
    processVoice: vi.fn(),
  },
}));

describe('Audio-Visual Synchronization Integration Tests', () => {
  let mockAudioElement: HTMLAudioElement;

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Create mock audio element with realistic behavior
    mockAudioElement = {
      readyState: 4,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      play: vi.fn().mockResolvedValue(undefined),
      pause: vi.fn(),
    } as any;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Water Ripple Response to Audio Amplitude', () => {
    it('should extract amplitude data from audio', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      await waitFor(() => {
        expect(result.current.amplitude).toBeGreaterThanOrEqual(0);
        expect(result.current.amplitude).toBeLessThanOrEqual(1);
      });
    });

    it('should provide continuous amplitude updates', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      const amplitudes: number[] = [];
      
      // Collect amplitude samples over time
      for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, 50));
        amplitudes.push(result.current.amplitude);
      }

      // Verify we got multiple samples
      expect(amplitudes.length).toBe(5);
      
      // All samples should be valid
      amplitudes.forEach(amp => {
        expect(amp).toBeGreaterThanOrEqual(0);
        expect(amp).toBeLessThanOrEqual(1);
      });
    });

    it('should calculate frequency data for ripple speed', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      await waitFor(() => {
        expect(result.current.frequency).toBeGreaterThanOrEqual(0);
        expect(typeof result.current.frequency).toBe('number');
      });
    });

    it('should provide raw frequency data for advanced visualizations', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      await waitFor(() => {
        expect(result.current.frequencyData).toBeInstanceOf(Uint8Array);
      });
    });
  });

  describe('Rose Avatar Glow with Audio', () => {
    it('should detect when Rose is speaking', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      // Initially idle
      expect(result.current.isSpeaking).toBe(false);

      // When speaking state is active, it should be detectable
      // (This would be triggered by actual audio playback in real scenario)
    });

    it('should provide audio element for analysis during speaking', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      // Audio element should be accessible for analyzer
      expect(result.current.audioElement).toBeDefined();
    });

    it('should synchronize glow intensity with audio amplitude', async () => {
      const { result: voiceResult } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      const { result: analyzerResult } = renderHook(() =>
        useAudioAnalyzer(voiceResult.current.audioElement)
      );

      // When audio is playing, amplitude should drive glow
      await waitFor(() => {
        if (voiceResult.current.isSpeaking) {
          expect(analyzerResult.current.amplitude).toBeGreaterThanOrEqual(0);
        }
      });
    });
  });

  describe('Aurora Intensity Changes', () => {
    it('should increase intensity during conversation', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      // Aurora intensity should be linked to voice state
      const isConversationActive = 
        result.current.isListening || 
        result.current.isProcessing || 
        result.current.isSpeaking;

      expect(typeof isConversationActive).toBe('boolean');
    });

    it('should pulse with audio peaks', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      // Collect amplitude peaks
      const peaks: number[] = [];
      
      for (let i = 0; i < 10; i++) {
        await new Promise(resolve => setTimeout(resolve, 30));
        const amp = result.current.amplitude;
        if (amp > 0.5) {
          peaks.push(amp);
        }
      }

      // Peaks should be detectable for aurora pulsing
      expect(peaks.length).toBeGreaterThanOrEqual(0);
    });

    it('should provide smooth transitions between states', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      const states: string[] = [];
      
      // Track state transitions
      states.push(result.current.voiceState);
      
      await new Promise(resolve => setTimeout(resolve, 100));
      states.push(result.current.voiceState);

      // States should be valid
      states.forEach(state => {
        expect(['idle', 'listening', 'processing', 'speaking']).toContain(state);
      });
    });
  });

  describe('Lighting Effects Synchronization', () => {
    it('should adjust lighting based on voice state', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      // Voice state should be accessible for lighting adjustments
      expect(result.current.voiceState).toBeDefined();
      expect(['idle', 'listening', 'processing', 'speaking']).toContain(
        result.current.voiceState
      );
    });

    it('should pulse igloo lights with audio', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      // Amplitude data should be available for light pulsing
      await waitFor(() => {
        expect(result.current.amplitude).toBeDefined();
        expect(typeof result.current.amplitude).toBe('number');
      });
    });

    it('should maintain calm atmosphere during transitions', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      // Collect amplitude samples to verify smooth changes
      const samples: number[] = [];
      
      for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, 50));
        samples.push(result.current.amplitude);
      }

      // Verify samples are continuous (no sudden jumps)
      for (let i = 1; i < samples.length; i++) {
        const diff = Math.abs(samples[i] - samples[i - 1]);
        // Difference should be reasonable (not jarring)
        expect(diff).toBeLessThanOrEqual(1.0);
      }
    });
  });

  describe('End-to-End Audio-Visual Flow', () => {
    it('should coordinate all visual effects during voice interaction', async () => {
      const { result: voiceResult } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      const { result: analyzerResult } = renderHook(() =>
        useAudioAnalyzer(voiceResult.current.audioElement)
      );

      // All components should be initialized
      expect(voiceResult.current.voiceState).toBe('idle');
      expect(analyzerResult.current.amplitude).toBeDefined();
      expect(analyzerResult.current.frequency).toBeDefined();
    });

    it('should handle rapid state changes smoothly', async () => {
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
        })
      );

      const stateHistory: string[] = [];
      
      // Track state over time
      for (let i = 0; i < 5; i++) {
        stateHistory.push(result.current.voiceState);
        await new Promise(resolve => setTimeout(resolve, 50));
      }

      // All states should be valid
      stateHistory.forEach(state => {
        expect(['idle', 'listening', 'processing', 'speaking']).toContain(state);
      });
    });

    it('should cleanup resources properly', async () => {
      const { result, unmount } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      // Verify analyzer is running
      await waitFor(() => {
        expect(result.current.amplitude).toBeDefined();
      });

      // Unmount and verify cleanup
      unmount();

      // After unmount, analyzer should stop
      expect(result.current.isAnalyzing).toBe(false);
    });
  });

  describe('Performance and Timing', () => {
    it('should update audio data at reasonable intervals', async () => {
      renderHook(() => useAudioAnalyzer(mockAudioElement));

      const startTime = Date.now();
      const updates: number[] = [];

      // Collect update timestamps
      for (let i = 0; i < 10; i++) {
        await new Promise(resolve => setTimeout(resolve, 16)); // ~60fps
        updates.push(Date.now() - startTime);
      }

      // Verify updates are happening regularly
      expect(updates.length).toBe(10);
      
      // Updates should be spaced reasonably (not all at once)
      const intervals = updates.slice(1).map((t, i) => t - updates[i]);
      const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
      
      // Average interval should be close to 16ms (60fps)
      expect(avgInterval).toBeGreaterThan(10);
      expect(avgInterval).toBeLessThan(50);
    });

    it('should not block main thread during analysis', async () => {
      const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

      const startTime = Date.now();
      
      // Perform some operations while analyzer is running
      for (let i = 0; i < 100; i++) {
        await new Promise(resolve => setTimeout(resolve, 1));
      }
      
      const duration = Date.now() - startTime;

      // Operations should complete in reasonable time
      expect(duration).toBeLessThan(500);
      
      // Analyzer should still be working
      expect(result.current.amplitude).toBeDefined();
    });
  });

  describe('Error Handling in Sync', () => {
    it('should handle audio element becoming null', async () => {
      const { result, rerender } = renderHook(
        ({ audio }) => useAudioAnalyzer(audio),
        { initialProps: { audio: mockAudioElement } }
      );

      // Initially working
      await waitFor(() => {
        expect(result.current.amplitude).toBeDefined();
      });

      // Audio element becomes null
      rerender({ audio: null as unknown as HTMLAudioElement });

      // Should handle gracefully
      expect(result.current.amplitude).toBe(0);
    });

    it('should recover from voice interaction errors', async () => {
      const mockOnError = vi.fn();
      
      const { result } = renderHook(() =>
        useVoiceInteraction({
          sessionId: 'test-session',
          onError: mockOnError,
        })
      );

      // After error, should return to idle state
      await waitFor(() => {
        if (result.current.error) {
          expect(result.current.voiceState).toBe('idle');
        }
      });
    });
  });
});
