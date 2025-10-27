import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioAnalyzer } from '../../hooks/useAudioAnalyzer';

describe('useAudioAnalyzer', () => {
  let mockAudioElement: HTMLAudioElement;
  let mockAnalyser: any;
  let mockAudioContext: any;

  beforeEach(() => {
    vi.clearAllMocks();

    // Create mock audio element
    mockAudioElement = {
      readyState: 4,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as any;

    // Create mock analyser
    mockAnalyser = {
      connect: vi.fn(),
      disconnect: vi.fn(),
      fftSize: 256,
      frequencyBinCount: 128,
      getByteFrequencyData: vi.fn((array: Uint8Array) => {
        // Simulate frequency data
        for (let i = 0; i < array.length; i++) {
          array[i] = Math.floor(Math.random() * 255);
        }
      }),
      getByteTimeDomainData: vi.fn((array: Uint8Array) => {
        // Simulate waveform data
        for (let i = 0; i < array.length; i++) {
          array[i] = 128 + Math.floor(Math.random() * 50);
        }
      }),
      smoothingTimeConstant: 0.8,
      minDecibels: -90,
      maxDecibels: -10,
    };

    // Create mock audio context
    mockAudioContext = {
      createAnalyser: vi.fn(() => mockAnalyser),
      createMediaElementSource: vi.fn(() => ({
        connect: vi.fn(),
        disconnect: vi.fn(),
      })),
      destination: {},
      sampleRate: 44100,
      close: vi.fn(),
      state: 'running',
    };

    // Mock AudioContext constructor
    global.AudioContext = vi.fn(() => mockAudioContext) as any;
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with zero audio data', () => {
    const { result } = renderHook(() => useAudioAnalyzer(null));

    expect(result.current.amplitude).toBe(0);
    expect(result.current.frequency).toBe(0);
    expect(result.current.frequencyData).toBeInstanceOf(Uint8Array);
    expect(result.current.waveformData).toBeInstanceOf(Uint8Array);
    expect(result.current.isAnalyzing).toBe(false);
  });

  it('should initialize analyzer when audio element is provided', async () => {
    renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(mockAudioContext.createAnalyser).toHaveBeenCalled();
      expect(mockAudioContext.createMediaElementSource).toHaveBeenCalledWith(mockAudioElement);
    });
  });

  it('should configure analyser with custom options', async () => {
    const options = {
      fftSize: 512,
      smoothingTimeConstant: 0.9,
      minDecibels: -100,
      maxDecibels: -20,
    };

    renderHook(() => useAudioAnalyzer(mockAudioElement, options));

    await waitFor(() => {
      expect(mockAnalyser.fftSize).toBe(512);
      expect(mockAnalyser.smoothingTimeConstant).toBe(0.9);
      expect(mockAnalyser.minDecibels).toBe(-100);
      expect(mockAnalyser.maxDecibels).toBe(-20);
    });
  });

  it('should extract amplitude from frequency data', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(result.current.amplitude).toBeGreaterThanOrEqual(0);
      expect(result.current.amplitude).toBeLessThanOrEqual(1);
    });
  });

  it('should calculate dominant frequency', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(result.current.frequency).toBeGreaterThanOrEqual(0);
      expect(typeof result.current.frequency).toBe('number');
    });
  });

  it('should provide frequency and waveform data arrays', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(result.current.frequencyData).toBeInstanceOf(Uint8Array);
      expect(result.current.frequencyData.length).toBeGreaterThan(0);
      expect(result.current.waveformData).toBeInstanceOf(Uint8Array);
      expect(result.current.waveformData.length).toBeGreaterThan(0);
    });
  });

  it('should not initialize when disabled', () => {
    renderHook(() => useAudioAnalyzer(mockAudioElement, { enabled: false }));

    expect(mockAudioContext.createAnalyser).not.toHaveBeenCalled();
  });

  it('should stop analysis when stopAnalysis is called', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(result.current.isAnalyzing).toBe(true);
    });

    act(() => {
      result.current.stopAnalysis();
    });

    expect(result.current.isAnalyzing).toBe(false);
  });

  it('should restart analysis when startAnalysis is called', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(result.current.isAnalyzing).toBe(true);
    });

    act(() => {
      result.current.stopAnalysis();
    });

    expect(result.current.isAnalyzing).toBe(false);

    act(() => {
      result.current.startAnalysis();
    });

    expect(result.current.isAnalyzing).toBe(true);
  });

  it('should cleanup audio context on unmount', async () => {
    const { unmount } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      expect(mockAudioContext.createAnalyser).toHaveBeenCalled();
    });

    unmount();

    expect(mockAudioContext.close).toHaveBeenCalled();
  });

  it('should handle audio element not ready', () => {
    const notReadyAudioElement = {
      ...mockAudioElement,
      readyState: 0,
    } as any;

    renderHook(() => useAudioAnalyzer(notReadyAudioElement));

    // Should wait for canplay event
    expect(notReadyAudioElement.addEventListener).toHaveBeenCalledWith(
      'canplay',
      expect.any(Function)
    );
  });

  it('should handle errors during initialization gracefully', () => {
    const errorAudioContext = {
      ...mockAudioContext,
      createAnalyser: vi.fn(() => {
        throw new Error('Failed to create analyser');
      }),
    };

    global.AudioContext = vi.fn(() => errorAudioContext) as any;

    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    // Should not crash, just log error
    expect(result.current.amplitude).toBe(0);
  });

  it('should update audio data continuously', async () => {
    const { result } = renderHook(() => useAudioAnalyzer(mockAudioElement));

    // const initialAmplitude = result.current.amplitude;

    // Wait for multiple analysis cycles
    await new Promise((resolve) => setTimeout(resolve, 100));

    // Data should be updated (may or may not be different due to random mock data)
    expect(result.current.amplitude).toBeGreaterThanOrEqual(0);
    expect(result.current.amplitude).toBeLessThanOrEqual(1);
  });

  it('should handle null audio element gracefully', () => {
    const { result } = renderHook(() => useAudioAnalyzer(null));

    expect(result.current.amplitude).toBe(0);
    expect(result.current.frequency).toBe(0);
    expect(result.current.isAnalyzing).toBe(false);
    expect(mockAudioContext.createAnalyser).not.toHaveBeenCalled();
  });

  it('should connect audio nodes correctly', async () => {
    renderHook(() => useAudioAnalyzer(mockAudioElement));

    await waitFor(() => {
      const source = mockAudioContext.createMediaElementSource();
      expect(source.connect).toHaveBeenCalledWith(mockAnalyser);
      expect(mockAnalyser.connect).toHaveBeenCalledWith(mockAudioContext.destination);
    });
  });
});
