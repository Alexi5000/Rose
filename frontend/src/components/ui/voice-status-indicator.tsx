/**
 * 🎙️ Voice Status Indicator
 * 
 * Phase 8: Visual feedback component showing current voice state.
 * Follows "Don't Make Me Think" UX principles:
 * - Clear affordances for each state
 * - Pulsing animation during processing
 * - Hint text for available actions
 */

import React from 'react';
import type { VoiceState } from '@/types/voice';

interface VoiceStatusIndicatorProps {
  state: VoiceState;
  className?: string;
}

const VoiceStatusIndicator: React.FC<VoiceStatusIndicatorProps> = ({
  state,
  className = '',
}) => {
  const getStateConfig = () => {
    switch (state) {
      case 'idle':
        return {
          icon: '👆',
          text: 'Tap anywhere to talk',
          subtext: 'Rose is ready to listen',
          pulseClass: '',
          bgClass: 'bg-white/10',
        };
      case 'listening':
        return {
          icon: '🎙️',
          text: 'Listening...',
          subtext: 'Tap to stop',
          pulseClass: 'animate-pulse',
          bgClass: 'bg-green-500/20 border-green-400/30',
        };
      case 'processing':
        return {
          icon: '✨',
          text: 'Processing...',
          subtext: 'Rose is thinking',
          pulseClass: 'animate-pulse',
          bgClass: 'bg-amber-500/20 border-amber-400/30',
        };
      case 'speaking':
        return {
          icon: '🌹',
          text: 'Rose is speaking',
          subtext: 'Tap to interrupt',
          pulseClass: 'animate-pulse',
          bgClass: 'bg-rose-500/20 border-rose-400/30',
        };
      default:
        return {
          icon: '👆',
          text: 'Tap to start',
          subtext: '',
          pulseClass: '',
          bgClass: 'bg-white/10',
        };
    }
  };

  const config = getStateConfig();

  return (
    <div
      className={`
        fixed bottom-8 left-1/2 transform -translate-x-1/2
        px-6 py-3 rounded-full backdrop-blur-sm
        border border-white/10 shadow-lg
        transition-all duration-300 ease-out
        ${config.bgClass}
        ${config.pulseClass}
        ${className}
      `}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-3">
        <span className="text-2xl" aria-hidden="true">
          {config.icon}
        </span>
        <div className="flex flex-col">
          <span className="text-white font-medium text-sm">
            {config.text}
          </span>
          {config.subtext && (
            <span className="text-white/60 text-xs">
              {config.subtext}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default VoiceStatusIndicator;
