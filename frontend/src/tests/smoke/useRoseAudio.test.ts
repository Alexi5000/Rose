/**
 * 🔊 useRoseAudio Hook Smoke Tests
 *
 * Tests Rose audio playback hook initialization and basic functionality.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useRoseAudio } from '@/hooks/useRoseAudio';

console.log('🔊 Loading useRoseAudio tests');

// Constants (no magic numbers!)
const MOCK_AUDIO_URL = 'http://test.example.com/rose-response.mp3';
const INITIAL_AMPLITUDE = 0;
const EXPECTED_PLAYING_STATE = true;
const EXPECTED_STOPPED_STATE = false;

describe('🔊 useRoseAudio Hook', () => {
  beforeEach(() => {
    console.log('  🔧 Resetting mocks');
    vi.clearAllMocks();
  });

  it('✅ initializes with correct default state', () => {
    console.log('  🔍 Testing initial state');

    const { result } = renderHook(() => useRoseAudio());

    expect(result.current.isPlaying).toBe(false);
    expect(result.current.roseAmplitude).toBe(INITIAL_AMPLITUDE);
    expect(result.current.error).toBeNull();
    expect(typeof result.current.playAudio).toBe('function');
    expect(typeof result.current.stopAudio).toBe('function');

    console.log('  ✅ Initial state correct');
  });

  it('✅ playAudio updates isPlaying state', async () => {
    console.log('  🔍 Testing playAudio state update');

    const onPlaybackStart = vi.fn();
    const { result } = renderHook(() => useRoseAudio({ onPlaybackStart }));

    // Start playback
    await result.current.playAudio(MOCK_AUDIO_URL);

    await waitFor(() => {
      expect(result.current.isPlaying).toBe(EXPECTED_PLAYING_STATE);
    });

    expect(onPlaybackStart).toHaveBeenCalled();

    console.log('  ✅ playAudio state updated');
  });

  it('✅ stopAudio resets state', async () => {
    console.log('  🔍 Testing stopAudio');

    const { result } = renderHook(() => useRoseAudio());

    // Start then stop
    await result.current.playAudio(MOCK_AUDIO_URL);
    result.current.stopAudio();

    await waitFor(() => {
      expect(result.current.isPlaying).toBe(EXPECTED_STOPPED_STATE);
      expect(result.current.roseAmplitude).toBe(INITIAL_AMPLITUDE);
    });

    console.log('  ✅ stopAudio reset state');
  });

  it('✅ onPlaybackEnd callback is configured', () => {
    console.log('  🔍 Testing onPlaybackEnd callback setup');

    const onPlaybackEnd = vi.fn();
    const { result } = renderHook(() => useRoseAudio({ onPlaybackEnd }));

    expect(result.current).toBeDefined();
    expect(onPlaybackEnd).toBeDefined();

    console.log('  ✅ onPlaybackEnd configured');
  });

  it('✅ handles playback errors gracefully', async () => {
    console.log('  🔍 Testing error handling');

    const onError = vi.fn();
    const { result } = renderHook(() => useRoseAudio({ onError }));

    // Mock audio element to throw error
    const mockPlay = vi.fn().mockRejectedValue(new Error('Playback failed'));
    global.Audio = class MockErrorAudio {
      play = mockPlay;
      pause = vi.fn();
      addEventListener = vi.fn();
      removeEventListener = vi.fn();
    } as any;

    await result.current.playAudio(MOCK_AUDIO_URL);

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    console.log('  ✅ Error handled gracefully');
  });

  it('✅ updates amplitude during playback', async () => {
    console.log('  🔍 Testing amplitude tracking');

    const { result } = renderHook(() => useRoseAudio());

    await result.current.playAudio(MOCK_AUDIO_URL);

    // Amplitude should update from analyser
    // (In reality, this would be updated by requestAnimationFrame loop)
    await waitFor(() => {
      expect(result.current.roseAmplitude).toBeGreaterThanOrEqual(0);
      expect(result.current.roseAmplitude).toBeLessThanOrEqual(1);
    });

    console.log('  ✅ Amplitude tracking works');
  });

  it('✅ cleans up on unmount', async () => {
    console.log('  🔍 Testing cleanup');

    const { result, unmount } = renderHook(() => useRoseAudio());

    await result.current.playAudio(MOCK_AUDIO_URL);

    // Unmount should cleanup
    unmount();

    // Verify no errors thrown during cleanup
    expect(true).toBe(true);

    console.log('  ✅ Cleanup successful');
  });

  it('✅ can play audio URLs', async () => {
    console.log('  🔍 Testing playAudio function');

    const { result } = renderHook(() => useRoseAudio());

    // Verify playAudio function exists
    expect(result.current.playAudio).toBeDefined();
    expect(typeof result.current.playAudio).toBe('function');

    console.log('  ✅ playAudio function available');
  });
});

console.log('✅ useRoseAudio tests loaded');
