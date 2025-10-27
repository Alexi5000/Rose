import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock Web Audio API
class MockAudioContext {
  sampleRate = 44100;
  destination = {};
  state = 'running';
  
  createAnalyser() {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      fftSize: 256,
      frequencyBinCount: 128,
      getByteFrequencyData: vi.fn(),
      getByteTimeDomainData: vi.fn(),
      smoothingTimeConstant: 0.8,
      minDecibels: -90,
      maxDecibels: -10,
    };
  }
  
  createMediaElementSource() {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
    };
  }
  
  createGain() {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      gain: { value: 1 },
    };
  }
  
  close = vi.fn();
  resume = vi.fn();
  suspend = vi.fn();
}

global.AudioContext = MockAudioContext as any;
(global as any).webkitAudioContext = MockAudioContext;

// Mock MediaRecorder
class MockMediaRecorder {
  state = 'inactive';
  stream = null;
  ondataavailable: ((event: any) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  
  start = vi.fn();
  stop = vi.fn();
  pause = vi.fn();
  resume = vi.fn();
  
  static isTypeSupported(type: string) {
    return type === 'audio/webm' || type === 'audio/mp4';
  }
}

global.MediaRecorder = MockMediaRecorder as any;

// Mock navigator.mediaDevices
Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: vi.fn(() => [
        {
          stop: vi.fn(),
          kind: 'audio',
          enabled: true,
        },
      ]),
    }),
    enumerateDevices: vi.fn().mockResolvedValue([]),
  },
});

// Mock HTMLAudioElement
class MockAudio {
  readyState = 4;
  currentTime = 0;
  duration = 0;
  volume = 1;
  muted = false;
  onplay: (() => void) | null = null;
  onended: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  
  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn();
  load = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
}

global.Audio = MockAudio as any;

// Mock requestAnimationFrame
global.requestAnimationFrame = vi.fn((cb) => {
  setTimeout(cb, 16);
  return 1;
}) as any;

global.cancelAnimationFrame = vi.fn();

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});
