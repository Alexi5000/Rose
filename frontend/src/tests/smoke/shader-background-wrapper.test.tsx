import { act, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ShaderBackgroundWrapper from '@/components/ui/shader-background-wrapper';
import type { VoiceResponse } from '@/types/voice';

const hookState = vi.hoisted(() => ({
  onResponse: undefined as ((response: VoiceResponse) => void) | undefined,
  playAudio: vi.fn(),
}));

vi.mock('@/hooks/useVoiceSession', () => ({
  useVoiceSession: vi.fn((props: { onResponse: (response: VoiceResponse) => void }) => {
    hookState.onResponse = props.onResponse;
    return {
      state: 'listening',
      userAmplitude: 0,
      isUserSpeaking: false,
      startSession: vi.fn(),
      stopSession: vi.fn(),
      resumeListening: vi.fn(),
      notifyPlaybackStart: vi.fn(),
      notifyPlaybackEnd: vi.fn(),
      sessionId: null,
      error: null,
    };
  }),
}));

vi.mock('@/hooks/useRoseAudio', () => ({
  useRoseAudio: vi.fn(() => ({
    isPlaying: false,
    roseAmplitude: 0,
    playAudio: hookState.playAudio,
    stopAudio: vi.fn(),
    error: null,
  })),
}));

vi.mock('@/components/ui/shader-background', () => ({
  default: () => <canvas data-testid="shader-background" />,
}));

describe('ShaderBackgroundWrapper transcript', () => {
  it('marks Rose continuation prompts separately from normal replies', async () => {
    render(<ShaderBackgroundWrapper onError={vi.fn()} />);

    await act(async () => {
      hookState.onResponse?.({
        text: 'Say a little more so I can meet you there.',
        user_text: 'I feel like',
        audio_url: '',
        turn_incomplete_reason: 'dangling_phrase',
        session_id: 'session-123',
      });
    });

    const continuation = screen
      .getByText('Say a little more so I can meet you there.')
      .closest('[data-turn-kind]');
    expect(continuation).toHaveAttribute('data-turn-kind', 'continuation');
    expect(continuation).toHaveAttribute(
      'title',
      'Rose asked for a little more before answering'
    );

    await act(async () => {
      hookState.onResponse?.({
        text: 'Good. Stay with that ease.',
        user_text: 'I feel calmer now.',
        audio_url: '',
        session_id: 'session-123',
      });
    });

    const normalReply = screen.getByText('Good. Stay with that ease.').closest('[data-turn-kind]');
    expect(normalReply).toHaveAttribute('data-turn-kind', 'response');
    expect(normalReply).not.toHaveAttribute('title');
  });
});
