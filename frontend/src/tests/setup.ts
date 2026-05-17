/**
 * 🧪 Test Setup and Mocks
 *
 * Comprehensive Web API mocks for testing voice interaction features.
 * Copied from archive and enhanced for new architecture.
 */

import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom';

console.log('🧪 Test setup loaded');

// Cleanup after each test
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Mock Web Audio API
class MockAnalyserNode {
  fftSize = 2048;
  frequencyBinCount = 1024;
  smoothingTimeConstant = 0.85;
  minDecibels = -90;
  maxDecibels = -10;

  connect = vi.fn();
  disconnect = vi.fn();
  getByteFrequencyData = vi.fn();
  getByteTimeDomainData = vi.fn();

  // For VAD - returns mock audio data
  getFloatTimeDomainData = vi.fn((array: Float32Array) => {
    // Fill with silence by default
    for (let i = 0; i < array.length; i++) {
      array[i] = 0;
    }
  });
}

class MockAudioContext {
  sampleRate = 44100;
  destination = { connect: vi.fn(), disconnect: vi.fn() };
  state = 'running';

  createAnalyser() {
    return new MockAnalyserNode();
  }

  createMediaStreamSource(stream: MediaStream) {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      mediaStream: stream,
    };
  }

  createMediaElementSource(element: HTMLAudioElement) {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      mediaElement: element,
    };
  }

  createGain() {
    return {
      connect: vi.fn(),
      disconnect: vi.fn(),
      gain: { value: 1 },
    };
  }

  close = vi.fn().mockResolvedValue(undefined);
  resume = vi.fn().mockResolvedValue(undefined);
  suspend = vi.fn().mockResolvedValue(undefined);
}

global.AudioContext = MockAudioContext as any;
(global as any).webkitAudioContext = MockAudioContext;

// Mock MediaRecorder
class MockMediaRecorder {
  state: 'inactive' | 'recording' | 'paused' = 'inactive';
  stream: MediaStream | null = null;
  ondataavailable: ((event: any) => void) | null = null;
  onstop: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onstart: (() => void) | null = null;

  constructor(stream: MediaStream, options?: any) {
    this.stream = stream;
  }

  start = vi.fn(() => {
    this.state = 'recording';
    if (this.onstart) {
      this.onstart();
    }
  });

  stop = vi.fn(() => {
    this.state = 'inactive';

    // Simulate data available event
    if (this.ondataavailable) {
      const mockBlob = new Blob(['mock audio data'], { type: 'audio/webm' });
      this.ondataavailable({ data: mockBlob });
    }

    // Simulate stop event
    if (this.onstop) {
      setTimeout(() => {
        this.onstop!();
      }, 0);
    }
  });

  pause = vi.fn(() => {
    this.state = 'paused';
  });

  resume = vi.fn(() => {
    this.state = 'recording';
  });

  static isTypeSupported(type: string) {
    return type.includes('audio/webm') || type.includes('audio/mp4') || type.includes('audio/ogg');
  }
}

global.MediaRecorder = MockMediaRecorder as any;

// Mock navigator.mediaDevices
Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      id: 'mock-stream-id',
      active: true,
      getTracks: vi.fn(() => [
        {
          id: 'mock-track-id',
          kind: 'audio',
          label: 'Mock Microphone',
          enabled: true,
          muted: false,
          readyState: 'live',
          stop: vi.fn(),
        },
      ]),
      getAudioTracks: vi.fn(() => [
        {
          id: 'mock-track-id',
          kind: 'audio',
          label: 'Mock Microphone',
          enabled: true,
          muted: false,
          readyState: 'live',
          stop: vi.fn(),
        },
      ]),
      getVideoTracks: vi.fn(() => []),
      addTrack: vi.fn(),
      removeTrack: vi.fn(),
    }),
    enumerateDevices: vi.fn().mockResolvedValue([
      {
        deviceId: 'mock-mic-id',
        kind: 'audioinput',
        label: 'Mock Microphone',
        groupId: 'mock-group',
      },
    ]),
  },
});

// Mock HTMLAudioElement
class MockAudio {
  readyState = 4; // HAVE_ENOUGH_DATA
  currentTime = 0;
  duration = 100;
  volume = 1;
  muted = false;
  paused = true;
  ended = false;
  src = '';

  onplay: (() => void) | null = null;
  onended: (() => void) | null = null;
  onerror: ((event: any) => void) | null = null;
  onloadedmetadata: (() => void) | null = null;

  constructor(src?: string) {
    if (src) {
      this.src = src;
    }
  }

  play = vi.fn().mockImplementation(() => {
    this.paused = false;
    if (this.onplay) {
      setTimeout(() => this.onplay!(), 0);
    }
    return Promise.resolve();
  });

  pause = vi.fn(() => {
    this.paused = true;
  });

  load = vi.fn(() => {
    if (this.onloadedmetadata) {
      setTimeout(() => this.onloadedmetadata!(), 0);
    }
  });

  addEventListener = vi.fn((event: string, handler: any) => {
    if (event === 'play') this.onplay = handler;
    if (event === 'ended') this.onended = handler;
    if (event === 'error') this.onerror = handler;
    if (event === 'loadedmetadata') this.onloadedmetadata = handler;
  });

  removeEventListener = vi.fn();
}

global.Audio = MockAudio as any;

// Mock requestAnimationFrame (for VAD loop and shader)
let rafId = 1;
global.requestAnimationFrame = vi.fn((cb: FrameRequestCallback) => {
  const id = rafId++;
  // Execute callback asynchronously to simulate browser behavior
  setTimeout(() => cb(performance.now()), 0);
  return id;
}) as any;

global.cancelAnimationFrame = vi.fn();

// Mock performance.now() for consistent timing
let mockTime = 0;
global.performance = {
  ...global.performance,
  now: vi.fn(() => {
    mockTime += 16; // Simulate 60fps
    return mockTime;
  }),
} as any;

// Mock window.matchMedia (for responsive design)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
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

// Mock Blob constructor for audio recording
global.Blob = class MockBlob extends Blob {
  constructor(parts?: BlobPart[], options?: BlobPropertyBag) {
    super(parts, options);
  }
} as any;

// Mock URL.createObjectURL (for audio playback)
global.URL.createObjectURL = vi.fn((blob: Blob) => {
  return `mock-url://${Math.random().toString(36)}`;
});

global.URL.revokeObjectURL = vi.fn();

console.log('✅ Test mocks initialized');
