/**
 * Shader Background Wrapper Component
 *
 * Orchestrates the full voice interaction experience:
 * - Full-screen tap to start/stop/interrupt
 * - Voice session lifecycle via useVoiceSession
 * - Rose audio playback via useRoseAudio
 * - Real-time shader visualization
 * - Conversation transcript overlay
 */

import React, { useCallback, useState, useRef } from 'react';
import ShaderBackground from './shader-background';
import VoiceStatusIndicator from './voice-status-indicator';
import { useVoiceSession } from '@/hooks/useVoiceSession';
import { useRoseAudio } from '@/hooks/useRoseAudio';
import type { VoiceState, VoiceResponse } from '@/types/voice';

interface TranscriptEntry {
  role: 'user' | 'rose';
  text: string;
  timestamp: number;
}

interface ShaderBackgroundWrapperProps {
  onError: (error: string) => void;
  children?: React.ReactNode;
}

const TRANSCRIPT_MAX_ENTRIES = 4;
const TRANSCRIPT_FADE_MS = 8000;

const ShaderBackgroundWrapper: React.FC<ShaderBackgroundWrapperProps> = ({
  onError,
  children,
}) => {
  // Conversation transcript state
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);

  // Stable ref to roseAudio.playAudio — avoids stale closure in onResponse
  const playAudioRef = useRef<((response: VoiceResponse) => Promise<void>) | undefined>(undefined);

  const handleResponse = useCallback((response: VoiceResponse) => {
    // Add Rose's reply to transcript
    if (response.text) {
      setTranscript((prev) => {
        const next = [...prev];
        next.push({ role: 'rose', text: response.text, timestamp: Date.now() });
        return next.slice(-TRANSCRIPT_MAX_ENTRIES);
      });
    }

    // Play audio via ref (always current, no stale closure)
    playAudioRef.current?.(response);
  }, []);

  const handleError = useCallback(
    (error: string) => {
      onError(error);
    },
    [onError]
  );

  // Voice session hook
  const voiceSession = useVoiceSession({
    onResponse: handleResponse,
    onError: handleError,
  });

  // Rose audio hook
  const roseAudio = useRoseAudio({
    onError: (error) => onError(error),
  });

  // Keep playAudioRef current (not a hook, just assignment during render)
  playAudioRef.current = roseAudio.playAudio;

  // Derived display state: single source of truth.
  // voiceSession.state knows idle/listening/processing.
  // roseAudio.isPlaying knows if Rose is speaking.
  // No duplicate useState, no sync useEffect, no race conditions.
  const displayState: VoiceState = roseAudio.isPlaying
    ? 'speaking'
    : voiceSession.state;

  // Handle screen tap
  const handleScreenTap = useCallback(() => {
    if (voiceSession.state === 'idle') {
      voiceSession.startSession();
    } else if (voiceSession.state === 'listening') {
      voiceSession.stopSession();
      roseAudio.stopAudio();
    } else if (roseAudio.isPlaying) {
      // Barge-in: interrupt Rose and start listening
      roseAudio.stopAudio();
      voiceSession.startSession();
    }
    // Ignore taps during processing
  }, [voiceSession, roseAudio]);

  const getCursorClass = (): string => {
    return displayState === 'processing' ? 'cursor-wait' : 'cursor-pointer';
  };

  // Auto-fade old transcript entries
  React.useEffect(() => {
    if (transcript.length === 0) return;
    const timer = setTimeout(() => {
      setTranscript((prev) =>
        prev.filter((entry) => Date.now() - entry.timestamp < TRANSCRIPT_FADE_MS)
      );
    }, TRANSCRIPT_FADE_MS);
    return () => clearTimeout(timer);
  }, [transcript]);

  return (
    <div
      className={`fixed inset-0 ${getCursorClass()}`}
      onClick={handleScreenTap}
      role="button"
      aria-label={
        displayState === 'idle'
          ? 'Tap to talk to Rose'
          : displayState === 'listening'
          ? 'Tap to stop listening'
          : displayState === 'speaking'
          ? 'Tap to interrupt Rose'
          : 'Processing'
      }
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleScreenTap();
        }
      }}
    >
      <ShaderBackground
        userAmplitude={voiceSession.userAmplitude}
        roseAmplitude={roseAudio.roseAmplitude}
        state={displayState}
      />

      <VoiceStatusIndicator state={displayState} />

      {/* Conversation transcript overlay */}
      {transcript.length > 0 && (
        <div className="fixed bottom-20 left-4 right-4 z-10 pointer-events-none flex flex-col gap-2 max-w-lg">
          {transcript.map((entry) => (
            <div
              key={entry.timestamp}
              className={`text-sm px-3 py-2 rounded-lg backdrop-blur-sm ${
                entry.role === 'rose'
                  ? 'bg-white/10 text-white/90 self-start'
                  : 'bg-white/5 text-white/70 self-end italic'
              }`}
            >
              <span className="font-medium text-xs text-white/50 mr-2">
                {entry.role === 'rose' ? 'Rose' : 'You'}
              </span>
              {entry.text}
            </div>
          ))}
        </div>
      )}

      <div className="relative z-10 pointer-events-none">
        {children}
      </div>
    </div>
  );
};

export default ShaderBackgroundWrapper;
