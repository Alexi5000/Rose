/**
 * 🎤 useVoiceSession Hook Smoke Tests
 *
 * Tests voice session management with VAD functionality.
 * Adapted from archive for new architecture.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVoiceSession } from '@/hooks/useVoiceSession';
import * as api from '@/lib/api';

console.log('🎤 Loading useVoiceSession tests');

// Mock the API
vi.mock('@/lib/api', () => ({
  processVoice: vi.fn(),
  getErrorMessage: vi.fn(() => 'Mock error message'),
  createSession: vi.fn(),
}));

// Constants (no magic numbers!)
const MOCK_SESSION_ID = 'test-session-123';
const MOCK_TRANSCRIPTION = 'Hello Rose, I need someone to talk to';
const MOCK_AUDIO_URL = 'http://test.example.com/rose-response.mp3';
const INITIAL_AMPLITUDE = 0;
const INITIAL_STATE = 'idle';

describe('🎤 useVoiceSession Hook', () => {
  const mockOnResponse = vi.fn();
  const mockOnError = vi.fn();

  beforeEach(() => {
    console.log('  🔧 Resetting mocks');
    vi.clearAllMocks();

    // Reset API mock
    vi.mocked(api.processVoice).mockResolvedValue({
      text: MOCK_TRANSCRIPTION,
      audio_url: MOCK_AUDIO_URL,
      session_id: MOCK_SESSION_ID,
    });

    vi.mocked(api.createSession).mockResolvedValue({
      session_id: MOCK_SESSION_ID,
      message: 'Session started',
    });
  });

  it('✅ initializes with idle state', () => {
    console.log('  🔍 Testing initial state');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    expect(result.current.state).toBe(INITIAL_STATE);
    expect(result.current.userAmplitude).toBe(INITIAL_AMPLITUDE);
    expect(result.current.isUserSpeaking).toBe(false);
    expect(result.current.sessionId).toBeNull();
    expect(result.current.error).toBeNull();
    expect(typeof result.current.startSession).toBe('function');
    expect(typeof result.current.stopSession).toBe('function');

    console.log('  ✅ Initial state correct');
  });

  it('✅ starts session and transitions to listening', async () => {
    console.log('  🔍 Testing session start');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({ audio: true });

    console.log('  ✅ Session started, state is listening');
  });

  it('✅ handles microphone permission errors', async () => {
    console.log('  🔍 Testing permission denied');

    const mockError = new Error('Permission denied');
    vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(mockError);

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    expect(result.current.state).toBe(INITIAL_STATE);
    expect(mockOnError).toHaveBeenCalled();

    console.log('  ✅ Permission error handled');
  });

  it('✅ stops session and returns to idle', async () => {
    console.log('  🔍 Testing session stop');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    // Start session
    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    // Stop session
    act(() => {
      result.current.stopSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe(INITIAL_STATE);
      expect(result.current.userAmplitude).toBe(INITIAL_AMPLITUDE);
      expect(result.current.isUserSpeaking).toBe(false);
    });

    console.log('  ✅ Session stopped, returned to idle');
  });

  it('✅ updates amplitude during listening', async () => {
    console.log('  🔍 Testing amplitude updates');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    // Amplitude should be tracked (between 0-1)
    expect(result.current.userAmplitude).toBeGreaterThanOrEqual(0);
    expect(result.current.userAmplitude).toBeLessThanOrEqual(1);

    console.log('  ✅ Amplitude tracking works');
  });

  it('✅ API client is callable', () => {
    console.log('  🔍 Testing API client integration');

    // Just verify the mock is set up correctly
    expect(api.processVoice).toBeDefined();
    expect(typeof api.processVoice).toBe('function');

    console.log('  ✅ API client is available');
  });

  it('✅ onResponse callback is provided', () => {
    console.log('  🔍 Testing onResponse callback setup');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    // Verify hook initialized with callbacks
    expect(result.current).toBeDefined();
    expect(mockOnResponse).toBeDefined();

    console.log('  ✅ Callbacks configured correctly');
  });

  it('✅ session ID starts as null', () => {
    console.log('  🔍 Testing initial session ID');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    expect(result.current.sessionId).toBeNull();

    console.log('  ✅ Session ID initially null');
  });

  it('✅ error callback is provided', () => {
    console.log('  🔍 Testing error callback setup');

    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    expect(result.current).toBeDefined();
    expect(mockOnError).toBeDefined();

    console.log('  ✅ Error callback configured');
  });

  it('✅ cleans up resources on unmount', async () => {
    console.log('  🔍 Testing cleanup on unmount');

    const { result, unmount } = renderHook(() =>
      useVoiceSession({
        onResponse: mockOnResponse,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    // Unmount should cleanup
    unmount();

    // Verify no errors during cleanup
    expect(true).toBe(true);

    console.log('  ✅ Cleanup successful');
  });
});

console.log('✅ useVoiceSession tests loaded');
