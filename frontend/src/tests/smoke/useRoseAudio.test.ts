/**
 * 🔊 useRoseAudio Hook Smoke Tests
 *
 * Tests Rose audio playback hook initialization and basic functionality.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import { useRoseAudio } from '@/hooks/useRoseAudio';
import type { VoiceResponse } from '@/types/voice';

console.log('🔊 Loading useRoseAudio tests');

vi.mock('@/lib/audio-utils', () => {
  const analyser = {
    fftSize: 32,
    getFloatTimeDomainData: (array: Float32Array) => {
      array.fill(0.2);
    },
  } as unknown as AnalyserNode;

  const audioContext = {
    state: 'running',
    close: vi.fn().mockResolvedValue(undefined),
    resume: vi.fn().mockResolvedValue(undefined),
  } as unknown as AudioContext;

  return {
    calculateRms: (samples: Float32Array) => samples[0] ?? 0,
    createPlaybackAnalyzer: vi.fn(() => ({
      audioContext,
      analyser,
    })),
  };
});

const INITIAL_AMPLITUDE = 0;
const EXPECTED_STOPPED_STATE = false;
const MOCK_RESPONSE: VoiceResponse = {
  text: 'Test response audio',
  audio_url: 'https://rose.test/audio.mp3',
  session_id: 'test-session-1234',
};

let audioInstances: MockAudio[] = [];
let shouldFailAudioLoad = false;

class MockAudio {
  public src = '';
  public volume = 1;
  public crossOrigin: string | null = null;
  public preload = 'auto';
  public duration = 1;
  public currentTime = 0;
  public readyState = 0;
  public onplay: (() => void) | null = null;
  public onended: (() => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;
  private listeners: Record<string, Set<(event: Event) => void>> = {};

  constructor(src?: string) {
    if (src) {
      this.src = src;
    }
    audioInstances.push(this);
  }

  addEventListener(eventName: string, callback: (event: Event) => void) {
    if (!this.listeners[eventName]) {
      this.listeners[eventName] = new Set();
    }
    this.listeners[eventName]?.add(callback);
  }

  removeEventListener(eventName: string, callback: (event: Event) => void) {
    this.listeners[eventName]?.delete(callback);
  }

  private emit(eventName: string) {
    this.listeners[eventName]?.forEach((listener) =>
      listener({ type: eventName, target: this } as unknown as Event)
    );
  }

  load() {
    if (shouldFailAudioLoad) {
      this.emit('error');
      return;
    }

    this.readyState = 4;
    this.emit('loadedmetadata');
  }

  pause() {
    // noop for tests
  }

  async play() {
    this.onplay?.();
    queueMicrotask(() => {
      this.onended?.();
    });
    return Promise.resolve();
  }
}

class MockSpeechSynthesisUtterance {
  public text: string;
  public lang = 'en-US';
  public pitch = 1;
  public rate = 1;
  public onend: ((event: Event) => void) | null = null;
  public onerror: ((event: Event) => void) | null = null;

  constructor(text: string) {
    this.text = text;
  }
}

const createMockSpeechSynthesis = () => {
  return {
    speaking: false,
    pending: false,
    paused: false,
    cancel: vi.fn(function cancel(this: SpeechSynthesis) {
      this.speaking = false;
    }),
    speak: vi.fn(function speak(this: SpeechSynthesis, utterance: SpeechSynthesisUtterance) {
      this.speaking = true;
      queueMicrotask(() => {
        this.speaking = false;
        utterance.onend?.(new Event('end'));
      });
    }),
    getVoices: () => [],
    pause: vi.fn(),
    resume: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  } as unknown as SpeechSynthesis;
};

describe('🔊 useRoseAudio Hook', () => {
  beforeEach(() => {
    console.log('  🔧 Resetting mocks');
    vi.clearAllMocks();
    audioInstances = [];
    shouldFailAudioLoad = false;

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: async () => new Blob(['test'], { type: 'audio/mpeg' }),
    }) as unknown as typeof fetch;

    global.Audio = MockAudio as unknown as typeof Audio;
    global.SpeechSynthesisUtterance = MockSpeechSynthesisUtterance as unknown as typeof SpeechSynthesisUtterance;
    Object.assign(window, {
      speechSynthesis: createMockSpeechSynthesis(),
    });
  });

  it('✅ initializes with correct default state', () => {
    const { result } = renderHook(() => useRoseAudio());

    expect(result.current.isPlaying).toBe(false);
    expect(result.current.roseAmplitude).toBe(INITIAL_AMPLITUDE);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.playAudio).toBe('function');
    expect(typeof result.current.stopAudio).toBe('function');
  });

  it('✅ playAudio triggers playback callbacks', async () => {
    const onPlaybackStart = vi.fn();
    const onPlaybackEnd = vi.fn();
    const { result } = renderHook(() => useRoseAudio({ onPlaybackStart, onPlaybackEnd }));

    await act(async () => {
      await result.current.playAudio(MOCK_RESPONSE);
    });

    expect(onPlaybackStart).toHaveBeenCalled();
    expect(onPlaybackEnd).toHaveBeenCalled();
  });

  it('✅ stopAudio resets state', async () => {
    const { result } = renderHook(() => useRoseAudio());

    await act(async () => {
      await result.current.playAudio(MOCK_RESPONSE);
    });

    await act(async () => {
      result.current.stopAudio();
    });

    await waitFor(() => {
      expect(result.current.isPlaying).toBe(EXPECTED_STOPPED_STATE);
      expect(result.current.roseAmplitude).toBe(INITIAL_AMPLITUDE);
    });
  });

  it('✅ falls back to speech synthesis when no audio URL is available', async () => {
    const { result } = renderHook(() => useRoseAudio());

    await act(async () => {
      await result.current.playAudio({ ...MOCK_RESPONSE, audio_url: '' });
    });

    await waitFor(() => {
      expect(window.speechSynthesis.speak).toHaveBeenCalled();
    });
  });

  it('✅ surfaces errors when playback fails', async () => {
    const onError = vi.fn();
    shouldFailAudioLoad = true;

    const { result } = renderHook(() => useRoseAudio({ onError }));

    await expect(
      act(async () => {
        await result.current.playAudio({ ...MOCK_RESPONSE, text: '' });
      })
    ).rejects.toThrow();

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith('Unable to play Rose response');
    });
  });

  it('✅ resolves relative audio URLs against window origin', async () => {
    const relativeResponse: VoiceResponse = {
      ...MOCK_RESPONSE,
      audio_url: '/api/v1/voice/audio/test-file',
    };

    const { result } = renderHook(() => useRoseAudio());

    await act(async () => {
      await result.current.playAudio(relativeResponse);
    });

    expect(audioInstances[0]?.src).toBe(`${window.location.origin}/api/v1/voice/audio/test-file`);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('skips duplicate playback when WebSocket audio already streamed', async () => {
    const onPlaybackStart = vi.fn();
    const { result } = renderHook(() => useRoseAudio({ onPlaybackStart }));

    await act(async () => {
      await result.current.playAudio({ ...MOCK_RESPONSE, audio_streamed: true });
    });

    expect(audioInstances).toHaveLength(0);
    expect(window.speechSynthesis.speak).not.toHaveBeenCalled();
    expect(onPlaybackStart).not.toHaveBeenCalled();
  });
});

console.log('✅ useRoseAudio tests loaded');
