import { motion } from 'framer-motion';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { triggerHapticFeedback } from '../../utils/touchOptimization';

/**
 * VoiceButton Component
 * 
 * Circular button with glassmorphism effect for push-to-talk interaction.
 * Supports both mouse and touch events with visual states for idle, listening, processing, and speaking.
 * Includes advanced visual effects: pulsing glow, ripple effects, spinner, and audio-reactive pulsing.
 * Optimized for touch interactions on iOS and Android with haptic feedback.
 * 
 * Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 5.4
 */

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

interface VoiceButtonProps {
  voiceState: VoiceState;
  onToggle: () => void | Promise<void>;
  disabled?: boolean;
  audioAmplitude?: number; // For audio-reactive pulsing during speaking
  isActive: boolean;
}

// Animation variants for different voice states
// Requirements: 3.3, 3.4, 11.3
const buttonVariants = {
  idle: {
    scale: 1,
    boxShadow: '0 0 20px rgba(77, 159, 255, 0.4)',
    transition: {
      duration: 0.3,
      ease: 'easeOut',
    },
  },
  listening: {
    scale: 1.1,
    boxShadow: '0 0 40px rgba(77, 159, 255, 0.8)',
    transition: {
      duration: 0.3,
      ease: 'easeOut',
    },
  },
  processing: {
    scale: 1.05,
    boxShadow: '0 0 30px rgba(157, 77, 255, 0.6)',
    transition: {
      duration: 0.3,
      ease: 'easeInOut',
    },
  },
  speaking: {
    scale: [1, 1.05, 1],
    boxShadow: '0 0 30px rgba(255, 140, 66, 0.6)',
    transition: {
      repeat: Infinity,
      duration: 1,
      ease: 'easeInOut',
    },
  },
};

// Hover and tap animation variants
const hoverVariant = {
  scale: 1.05,
  transition: {
    duration: 0.2,
    ease: 'easeOut',
  },
};

const tapVariant = {
  scale: 0.95,
  transition: {
    duration: 0.1,
    ease: 'easeIn',
  },
};

export const VoiceButton = ({
  voiceState,
  onToggle,
  disabled = false,
  audioAmplitude = 0,
  isActive,
}: VoiceButtonProps) => {
  const handleActivate = () => {
    if (disabled) {
      return;
    }
    triggerHapticFeedback(15);
    void onToggle();
  };

  // Render appropriate icon based on state
  const renderIcon = () => {
    switch (voiceState) {
      case 'processing':
        return <Loader2 className="w-8 h-8 text-white animate-spin" />;
      case 'speaking':
        return <Mic className="w-8 h-8 text-white" />;
      case 'listening':
        return <Mic className="w-8 h-8 text-white" />;
      case 'idle':
      default:
        return <MicOff className="w-8 h-8 text-white/80" />;
    }
  };

  // Get aria label based on state
  const getAriaLabel = () => {
    switch (voiceState) {
      case 'listening':
        return 'Listening for your voice. Tap to mute.';
      case 'processing':
        return 'Processing your message...';
      case 'speaking':
        return 'Rose is responding...';
      case 'idle':
      default:
        return 'Tap to activate Rose and start talking';
    }
  };

  // Calculate dynamic scale based on audio amplitude when speaking
  const audioScale = voiceState === 'speaking' ? 1 + audioAmplitude * 0.1 : 1;

  return (
    <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-10">
      {/* Ripple effect for listening state */}
      {voiceState === 'listening' && (
        <>
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-blue-400/50"
            initial={{ scale: 1, opacity: 0.8 }}
            animate={{ scale: 2, opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeOut' }}
            style={{ width: '80px', height: '80px', left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-blue-400/30"
            initial={{ scale: 1, opacity: 0.6 }}
            animate={{ scale: 2.5, opacity: 0 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeOut', delay: 0.5 }}
            style={{ width: '80px', height: '80px', left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
          />
        </>
      )}

      {/* Pulsing glow for idle state */}
      {voiceState === 'idle' && (
        <motion.div
          className="absolute inset-0 rounded-full bg-blue-400/20 blur-xl"
          animate={{ opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          style={{ width: '100px', height: '100px', left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }}
        />
      )}

      <motion.button
        className="relative focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-400/70 rounded-full touch-none select-none"
        variants={buttonVariants}
        animate={voiceState}
        style={{ 
          scale: audioScale,
          WebkitTapHighlightColor: 'transparent', // Remove tap highlight on iOS
          WebkitTouchCallout: 'none', // Disable callout on iOS
        }}
        whileHover={!disabled ? hoverVariant : undefined}
        whileTap={!disabled ? tapVariant : undefined}
        onClick={handleActivate}
        disabled={disabled}
        aria-label={getAriaLabel()}
        aria-pressed={isActive}
        role="button"
        tabIndex={0}
      >
        <motion.div
          className="w-20 h-20 rounded-full bg-white/10 backdrop-blur-md
                     border-2 border-white/30 flex items-center justify-center"
          animate={{
            borderColor: voiceState === 'listening' 
              ? 'rgba(77, 159, 255, 0.6)'
              : voiceState === 'speaking'
              ? 'rgba(255, 140, 66, 0.6)'
              : 'rgba(255, 255, 255, 0.3)',
            backgroundColor: voiceState === 'listening'
              ? 'rgba(77, 159, 255, 0.15)'
              : voiceState === 'speaking'
              ? 'rgba(255, 140, 66, 0.15)'
              : 'rgba(255, 255, 255, 0.1)',
          }}
          transition={{
            duration: 0.3,
            ease: 'easeInOut',
          }}
        >
          {renderIcon()}
        </motion.div>

        {/* Screen reader status announcements */}
        <span className="sr-only" aria-live="polite" aria-atomic="true">
          {voiceState === 'processing' && 'Processing your message...'}
          {voiceState === 'speaking' && 'Rose is responding...'}
        </span>
      </motion.button>
    </div>
  );
};
