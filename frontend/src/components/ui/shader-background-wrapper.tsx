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
import {
  exportSessionMemories,
  forgetSessionMemories,
  updateMemoryPreferences,
} from '@/lib/api';
import type { MemoryMode } from '@/types/voice';
import type { VoiceState, VoiceResponse } from '@/types/voice';

interface TranscriptEntry {
  id: number;
  role: 'user' | 'rose';
  text: string;
  timestamp: number;
  kind?: 'continuation';
}

interface ShaderBackgroundWrapperProps {
  onError: (error: string) => void;
  children?: React.ReactNode;
}

const TRANSCRIPT_MAX_ENTRIES = 4;
const TRANSCRIPT_FADE_MS = 16000;

const ShaderBackgroundWrapper: React.FC<ShaderBackgroundWrapperProps> = ({
  onError,
  children,
}) => {
  // Conversation transcript state
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [sessionOnlyMemory, setSessionOnlyMemory] = useState<boolean>(() => {
    try {
      return localStorage.getItem('rose_memory_mode') === 'session_only';
    } catch {
      return false;
    }
  });
  const [memoryUpdating, setMemoryUpdating] = useState(false);
  const [memoryActionBusy, setMemoryActionBusy] = useState(false);
  const [memoryStatus, setMemoryStatus] = useState<string | null>(null);

  // Stable refs , avoids stale closures and circular hook dependencies
  const playAudioRef = useRef<((response: VoiceResponse) => Promise<void>) | undefined>(undefined);
  const notifyPlaybackEndRef = useRef<(() => void) | undefined>(undefined);
  const nextTranscriptIdRef = useRef(1);

  const handleResponse = useCallback((response: VoiceResponse) => {
    // Add user's transcribed text first (if available)
    if (response.user_text) {
      setTranscript((prev) => {
        const next = [...prev];
        next.push({
          id: nextTranscriptIdRef.current++,
          role: 'user',
          text: response.user_text as string,
          timestamp: Date.now(),
        });
        return next.slice(-TRANSCRIPT_MAX_ENTRIES);
      });
    }

    // Add Rose's reply to transcript
    if (response.text) {
      setTranscript((prev) => {
        const next = [...prev];
        next.push({
          id: nextTranscriptIdRef.current++,
          role: 'rose',
          text: response.text,
          timestamp: Date.now(),
          kind: response.turn_incomplete_reason ? 'continuation' : undefined,
        });
        return next.slice(-TRANSCRIPT_MAX_ENTRIES);
      });
    }

    // Play audio via ref (always current, no stale closure)
    playAudioRef.current?.(response);

    // If there is no audio or text (silence handling), resume listening immediately
    if (!response.audio_url && !response.text) {
      notifyPlaybackEndRef.current?.();
    }
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
    onPlaybackStart: () => voiceSession.notifyPlaybackStart(),
    onPlaybackEnd: () => voiceSession.notifyPlaybackEnd(),
    onError: (error) => onError(error),
  });

  // Keep refs current (not hooks, just assignments during render)
  playAudioRef.current = roseAudio.playAudio;
  notifyPlaybackEndRef.current = voiceSession.notifyPlaybackEnd;

  const applyMemoryMode = useCallback(
    (nextSessionOnly: boolean) => {
      const memoryMode: MemoryMode = nextSessionOnly ? 'session_only' : 'enabled';
      setSessionOnlyMemory(nextSessionOnly);
      try {
        localStorage.setItem('rose_memory_mode', memoryMode);
      } catch {
        // Ignore storage failures; the live API preference still matters.
      }
    },
    []
  );

  React.useEffect(() => {
    if (!voiceSession.sessionId) {
      return;
    }

    const memoryMode: MemoryMode = sessionOnlyMemory ? 'session_only' : 'enabled';
    setMemoryUpdating(true);
    updateMemoryPreferences(voiceSession.sessionId, memoryMode)
      .catch(() => {
        onError('Could not update memory mode. Please try again.');
      })
      .finally(() => {
        setMemoryUpdating(false);
      });
  }, [onError, sessionOnlyMemory, voiceSession.sessionId]);

  const handleExportMemories = useCallback(async () => {
    if (!voiceSession.sessionId) {
      onError('Start a session before exporting memories.');
      return;
    }

    setMemoryActionBusy(true);
    setMemoryStatus(null);
    try {
      const exported = await exportSessionMemories(voiceSession.sessionId);
      if (exported.memories.length === 0) {
        setMemoryStatus('No saved memories.');
        return;
      }

      const blob = new Blob([JSON.stringify(exported, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `rose-memories-${voiceSession.sessionId}.json`;
      link.click();
      URL.revokeObjectURL(url);
      setMemoryStatus(`Exported ${exported.memories.length}.`);
    } catch {
      onError('Could not export memories. Please try again.');
    } finally {
      setMemoryActionBusy(false);
    }
  }, [onError, voiceSession.sessionId]);

  const handleForgetMemories = useCallback(async () => {
    if (!voiceSession.sessionId) {
      onError('Start a session before deleting memories.');
      return;
    }

    if (!window.confirm('Delete long-term memories saved for this session?')) {
      return;
    }

    setMemoryActionBusy(true);
    setMemoryStatus(null);
    try {
      const result = await forgetSessionMemories(voiceSession.sessionId);
      setMemoryStatus(result.deleted ? 'Memories deleted.' : 'Deletion not confirmed.');
      if (!result.deleted) {
        onError('Could not confirm memory deletion. Please try again.');
      }
    } catch {
      onError('Could not delete memories. Please try again.');
    } finally {
      setMemoryActionBusy(false);
    }
  }, [onError, voiceSession.sessionId]);

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
      // Barge-in: interrupt Rose and immediately resume listening.
      // stopAudio() fires onPlaybackEnd which sets state back to 'listening',
      // then resumeListening() completes the transition without re-init.
      roseAudio.stopAudio();
      voiceSession.resumeListening();
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

      <div className="fixed bottom-4 left-4 z-20 max-w-sm pointer-events-none text-xs leading-relaxed text-white/55">
        Rose is AI emotional support, not professional care or emergency help. In a U.S. crisis, call or text 988.
      </div>

      <div
        className="fixed top-4 right-4 z-50 pointer-events-auto rounded-lg bg-black/35 border border-white/10 backdrop-blur-sm px-3 py-2 text-xs text-white/80"
        onClick={(event) => event.stopPropagation()}
      >
        <label className="flex items-center gap-2 cursor-pointer select-none">
          <input
            type="checkbox"
            checked={sessionOnlyMemory}
            disabled={memoryUpdating}
            onChange={(event) => {
              void applyMemoryMode(event.target.checked);
            }}
            className="h-4 w-4 accent-rose-400"
          />
          <span>Session-only memory</span>
        </label>
        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              void handleExportMemories();
            }}
            disabled={memoryActionBusy || !voiceSession.sessionId}
            className="rounded border border-white/15 px-2 py-1 text-white/80 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-45"
          >
            Export
          </button>
          <button
            type="button"
            onClick={() => {
              void handleForgetMemories();
            }}
            disabled={memoryActionBusy || !voiceSession.sessionId}
            className="rounded border border-white/15 px-2 py-1 text-white/80 hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-45"
          >
            Forget
          </button>
        </div>
        {memoryStatus && (
          <div className="mt-2 max-w-40 text-white/60" role="status">
            {memoryStatus}
          </div>
        )}
      </div>

      {/* Conversation transcript overlay */}
      {transcript.length > 0 && (
        <div className="fixed bottom-20 left-4 right-4 z-10 pointer-events-none flex flex-col gap-2 max-w-lg">
          {transcript.map((entry) => (
            <div
              key={entry.id}
              data-turn-kind={entry.kind || 'response'}
              title={entry.kind === 'continuation' ? 'Rose asked for a little more before answering' : undefined}
              className={`text-sm px-3 py-2 rounded-lg backdrop-blur-sm ${
                entry.role === 'rose'
                  ? `bg-white/10 text-white/90 self-start ${
                      entry.kind === 'continuation' ? 'border border-amber-200/25' : ''
                    }`
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
