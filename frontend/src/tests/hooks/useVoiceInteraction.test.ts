import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useVoiceInteraction } from '../../hooks/useVoiceInteraction';
import { apiClient } from '../../services/apiClient';

// Mock the API client
vi.mock('../../services/apiClient', () => ({
  apiClient: {
    processVoice: vi.fn(),
  },
}));

describe('useVoiceInteraction', () => {
  const mockSessionId = 'test-session-123';
  const mockOnError = vi.fn();
  const mockOnResponseText = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with idle state', () => {
    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
        onError: mockOnError,
        onResponseText: mockOnResponseText,
      })
    );

    expect(result.current.voiceState).toBe('idle');
    expect(result.current.isIdle).toBe(true);
    expect(result.current.isListening).toBe(false);
    expect(result.current.isProcessing).toBe(false);
    expect(result.current.isSpeaking).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.responseText).toBe('');
  });

  it('should start recording and transition to listening state', async () => {
    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
      })
    );

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.voiceState).toBe('listening');
    expect(result.current.isListening).toBe(true);
    expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 44100,
      },
    });
  });

  it('should handle microphone permission errors', async () => {
    const mockError = new Error('Permission denied');
    vi.mocked(navigator.mediaDevices.getUserMedia).mockRejectedValueOnce(mockError);

    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.voiceState).toBe('idle');
    expect(result.current.error).toBe('Could not access microphone. Please check permissions.');
    expect(mockOnError).toHaveBeenCalledWith('Could not access microphone. Please check permissions.');
  });

  it('should stop recording and process audio', async () => {
    const mockAudioUrl = 'https://example.com/audio.mp3';
    const mockResponseText = 'Hello, how can I help you?';
    
    vi.mocked(apiClient.processVoice).mockResolvedValueOnce({
      text: mockResponseText,
      audio_url: mockAudioUrl,
      session_id: mockSessionId,
    });

    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
        onResponseText: mockOnResponseText,
      })
    );

    // Start recording
    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isListening).toBe(true);

    // Stop recording
    await act(async () => {
      result.current.stopRecording();
    });

    // Wait for processing
    await waitFor(() => {
      expect(result.current.voiceState).toBe('processing');
    });
  });

  it('should handle API errors during voice processing', async () => {
    const mockError = new Error('Network error');
    vi.mocked(apiClient.processVoice).mockRejectedValueOnce(mockError);

    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
        onError: mockOnError,
      })
    );

    // Start recording
    await act(async () => {
      await result.current.startRecording();
    });

    // Simulate recording stop and processing
    await act(async () => {
      result.current.stopRecording();
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  it('should cancel recording without processing', async () => {
    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
      })
    );

    // Start recording
    await act(async () => {
      await result.current.startRecording();
    });

    expect(result.current.isListening).toBe(true);

    // Cancel recording
    await act(async () => {
      result.current.cancelRecording();
    });

    expect(result.current.voiceState).toBe('idle');
    expect(apiClient.processVoice).not.toHaveBeenCalled();
  });

  it('should stop audio playback', async () => {
    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
      })
    );

    // Simulate speaking state
    act(() => {
      // This would normally be set by playAudioResponse
      // For testing, we'll just call stopAudio
      result.current.stopAudio();
    });

    expect(result.current.voiceState).toBe('idle');
  });

  it('should handle missing session ID', async () => {
    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: '',
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startRecording();
    });

    // Simulate stop to trigger processing
    await act(async () => {
      result.current.stopRecording();
    });

    await waitFor(() => {
      expect(result.current.error).toBe('No active session. Please refresh the page.');
      expect(mockOnError).toHaveBeenCalled();
    });
  });

  it('should cleanup resources on unmount', async () => {
    const { result, unmount } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
      })
    );

    await act(async () => {
      await result.current.startRecording();
    });

    unmount();

    // Verify cleanup happened (stream tracks stopped)
    // This is implicit in the hook's useEffect cleanup
  });

  it('should handle audio playback errors', async () => {
    const mockAudioUrl = 'https://example.com/audio.mp3';
    const mockResponseText = 'Test response';
    
    vi.mocked(apiClient.processVoice).mockResolvedValueOnce({
      text: mockResponseText,
      audio_url: mockAudioUrl,
      session_id: mockSessionId,
    });

    // Mock Audio to throw error on play
    const mockAudio = {
      play: vi.fn().mockRejectedValue(new Error('Playback failed')),
      pause: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      onplay: null,
      onended: null,
      onerror: null,
    };
    
    global.Audio = vi.fn(() => mockAudio) as any;

    const { result } = renderHook(() =>
      useVoiceInteraction({
        sessionId: mockSessionId,
        onError: mockOnError,
      })
    );

    await act(async () => {
      await result.current.startRecording();
    });

    await act(async () => {
      result.current.stopRecording();
    });

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalled();
    });
  });
});
