/**
 * 🎭 Shader Background Wrapper Component
 *
 * Orchestrates the full voice interaction experience:
 * - Handles full-screen click events (entire screen is a button)
 * - Manages voice session lifecycle
 * - Manages Rose audio playback
 * - Updates shader with real-time audio data
 * - Controls cursor states for visual feedback
 */

import React, { useCallback, useState } from 'react';
import ShaderBackground from './shader-background';
import { useVoiceSession } from '@/hooks/useVoiceSession';
import { useRoseAudio } from '@/hooks/useRoseAudio';
import type { VoiceState } from '@/types/voice';

interface ShaderBackgroundWrapperProps {
  /** Callback when error occurs */
  onError: (error: string) => void;
  /** Children to render on top of shader */
  children?: React.ReactNode;
}

const ShaderBackgroundWrapper: React.FC<ShaderBackgroundWrapperProps> = ({
  onError,
  children,
}) => {
  const [currentState, setCurrentState] = useState<VoiceState>('idle');

  // 🎙️ Voice session hook
  const voiceSession = useVoiceSession({
    onResponse: (response) => {
      console.log(`💬 User said: "${response.text}"`);
      setCurrentState('speaking');

      // Play Rose's audio response
      roseAudio.playAudio(response.audio_url);
    },
    onError: (error) => {
      console.error('❌ Voice error:', error);
      onError(error);
    },
  });

  // 🔊 Rose audio hook
  const roseAudio = useRoseAudio({
    onPlaybackStart: () => {
      console.log('🗣️ Rose started speaking');
      setCurrentState('speaking');
    },
    onPlaybackEnd: () => {
      console.log('✅ Rose finished speaking');
      // Return to listening if session is active
      if (voiceSession.state === 'listening' || voiceSession.state === 'processing') {
        setCurrentState('listening');
      } else {
        setCurrentState('idle');
      }
    },
    onError: (error) => {
      console.error('❌ Audio playback error:', error);
      onError(error);
    },
  });

  // 👆 Handle screen tap
  const handleScreenTap = useCallback(() => {
    if (voiceSession.state === 'idle') {
      // Start session
      console.log('👆 Screen tapped - starting session');
      voiceSession.startSession();
      setCurrentState('listening');
    } else if (voiceSession.state === 'listening') {
      // Stop session
      console.log('👆 Screen tapped - stopping session');
      voiceSession.stopSession();
      roseAudio.stopAudio();
      setCurrentState('idle');
    }
    // Ignore taps during processing/speaking
  }, [voiceSession, roseAudio]);

  // 🎨 Get cursor style based on state
  const getCursorClass = (): string => {
    switch (currentState) {
      case 'idle':
        return 'cursor-pointer'; // Clickable
      case 'listening':
        return 'cursor-pointer'; // Can tap to stop
      case 'processing':
        return 'cursor-wait'; // Processing
      case 'speaking':
        return 'cursor-not-allowed'; // Can't interrupt Rose
      default:
        return 'cursor-pointer';
    }
  };

  // Sync state with voice session
  React.useEffect(() => {
    if (voiceSession.state !== currentState && !roseAudio.isPlaying) {
      setCurrentState(voiceSession.state);
    }
  }, [voiceSession.state, currentState, roseAudio.isPlaying]);

  return (
    <div
      className={`fixed inset-0 ${getCursorClass()}`}
      onClick={handleScreenTap}
      role="button"
      aria-label={
        currentState === 'idle'
          ? 'Tap to talk to Rose'
          : currentState === 'listening'
          ? 'Tap to stop listening'
          : 'Processing'
      }
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleScreenTap();
        }
      }}
    >
      {/* Shader background with audio reactivity */}
      <ShaderBackground
        userAmplitude={voiceSession.userAmplitude}
        roseAmplitude={roseAudio.roseAmplitude}
        state={currentState}
      />

      {/* Overlay children (error alerts, dev panel, etc.) */}
      <div className="relative z-10 pointer-events-none">
        {children}
      </div>
    </div>
  );
};

export default ShaderBackgroundWrapper;
