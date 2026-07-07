import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { useVoiceSession } from '@/hooks/useVoiceSession';
import * as api from '@/lib/api';

vi.mock('@/lib/api', () => ({
  processVoice: vi.fn(),
  getErrorMessage: vi.fn(() => 'Mock error message'),
  createSession: vi.fn(),
  sanitizeApiUrlForLog: vi.fn((url: string | undefined) =>
    (url ?? '[unknown-url]').replace(/session_id=[^&#]+/g, 'session_id=[session_id]')
  ),
}));

const MOCK_SESSION_ID = 'test-session-123';

const emitWsJson = async (socket: WebSocket, message: Record<string, unknown>) => {
  await socket.onmessage?.(
    new MessageEvent('message', {
      data: JSON.stringify(message),
    })
  );
};

describe('useVoiceSession WebSocket text-only fallback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.createSession).mockResolvedValue({
      session_id: MOCK_SESSION_ID,
      message: 'Session started',
    });
  });

  it('emits a text-only response when backend audio is unavailable', async () => {
    const onResponse = vi.fn();
    const onError = vi.fn();
    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse,
        onError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    const socket = (WebSocket as unknown as { instances: WebSocket[] }).instances[0];
    expect(socket).toBeDefined();

    await act(async () => {
      await emitWsJson(socket, { type: 'transcription', text: 'My voice feels stuck.' });
      await emitWsJson(socket, { type: 'response', text: 'I am here with you.' });
      await emitWsJson(socket, { type: 'audio_unavailable', text: 'I am here with you.' });
      result.current.notifyPlaybackStart();
      await emitWsJson(socket, {
        type: 'audio_end',
        timings: {
          stt_provider: 'deepgram_stt',
          stt_streaming: true,
          stt_batch_fallback: true,
          audio_bytes: 1800,
          stt_ms: 140,
          workflow_ms: 220,
          tts_ms: null,
          tts_phrase_count: 0,
          mic_to_first_audio_ms: null,
          turn_total_ms: 420,
        },
      });
    });

    expect(onResponse).toHaveBeenCalledWith(
      expect.objectContaining({
        text: 'I am here with you.',
        user_text: 'My voice feels stuck.',
        audio_url: '',
        session_id: MOCK_SESSION_ID,
        timings: expect.objectContaining({
          stt_provider: 'deepgram_stt',
          stt_batch_fallback: true,
        }),
      })
    );
    expect(onError).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });
  });

  it('moves through speaking state for streamed WebSocket audio', async () => {
    const onResponse = vi.fn();
    const onError = vi.fn();
    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse,
        onError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    const socket = (WebSocket as unknown as { instances: WebSocket[] }).instances[0];
    expect(socket).toBeDefined();

    await act(async () => {
      await emitWsJson(socket, { type: 'response', text: 'Breathe with me.' });
      await emitWsJson(socket, { type: 'audio_start' });
    });

    await waitFor(() => {
      expect(result.current.state).toBe('speaking');
    });

    await act(async () => {
      await emitWsJson(socket, { type: 'audio_unavailable', text: 'Breathe with me.' });
      await emitWsJson(socket, { type: 'audio_end' });
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });
    expect(onResponse).toHaveBeenCalledWith(
      expect.objectContaining({
        text: 'Breathe with me.',
        audio_url: '',
        session_id: MOCK_SESSION_ID,
      })
    );
    expect(onError).not.toHaveBeenCalled();
  });

  it('drops interrupted WebSocket audio_end without emitting a stale response', async () => {
    const onResponse = vi.fn();
    const onError = vi.fn();
    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse,
        onError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    const socket = (WebSocket as unknown as { instances: WebSocket[] }).instances[0];
    expect(socket).toBeDefined();

    await act(async () => {
      await emitWsJson(socket, { type: 'response', text: 'This should be interrupted.' });
      await emitWsJson(socket, { type: 'audio_start' });
    });

    await waitFor(() => {
      expect(result.current.state).toBe('speaking');
    });

    act(() => {
      result.current.resumeListening();
    });

    await act(async () => {
      await emitWsJson(socket, { type: 'audio_end', interrupted: true });
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });
    expect(onResponse).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
    expect(socket.sent).toContain(JSON.stringify({ type: 'interrupt' }));
  });

  it('surfaces incomplete turn reasons without leaking them to later turns', async () => {
    const onResponse = vi.fn();
    const onError = vi.fn();
    const { result } = renderHook(() =>
      useVoiceSession({
        onResponse,
        onError,
      })
    );

    await act(async () => {
      await result.current.startSession();
    });

    await waitFor(() => {
      expect(result.current.state).toBe('listening');
    });

    const socket = (WebSocket as unknown as { instances: WebSocket[] }).instances[0];
    expect(socket).toBeDefined();

    await act(async () => {
      await emitWsJson(socket, { type: 'transcription', text: 'I feel like' });
      await emitWsJson(socket, { type: 'turn_incomplete', reason: 'dangling_phrase' });
      await emitWsJson(socket, {
        type: 'response',
        text: 'Say a little more so I can meet you there.',
      });
      await emitWsJson(socket, {
        type: 'audio_unavailable',
        text: 'Say a little more so I can meet you there.',
      });
      await emitWsJson(socket, { type: 'audio_end' });
    });

    expect(onResponse).toHaveBeenCalledWith(
      expect.objectContaining({
        text: 'Say a little more so I can meet you there.',
        user_text: 'I feel like',
        audio_url: '',
        turn_incomplete_reason: 'dangling_phrase',
        session_id: MOCK_SESSION_ID,
      })
    );

    await act(async () => {
      await emitWsJson(socket, { type: 'transcription', text: 'I feel calmer now.' });
      await emitWsJson(socket, { type: 'response', text: 'Good. Stay with that ease.' });
      await emitWsJson(socket, { type: 'audio_unavailable', text: 'Good. Stay with that ease.' });
      await emitWsJson(socket, { type: 'audio_end' });
    });

    expect(onResponse).toHaveBeenCalledTimes(2);
    expect(onResponse.mock.calls[1][0]).toEqual(
      expect.objectContaining({
        text: 'Good. Stay with that ease.',
        user_text: 'I feel calmer now.',
        audio_url: '',
        session_id: MOCK_SESSION_ID,
      })
    );
    expect(onResponse.mock.calls[1][0].turn_incomplete_reason).toBeUndefined();
    expect(onError).not.toHaveBeenCalled();
  });
});
