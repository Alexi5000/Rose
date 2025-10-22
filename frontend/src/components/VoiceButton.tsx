import { motion } from 'framer-motion'
import { useEffect } from 'react'
import { VoiceState } from '../App'
import './VoiceButton.css'

interface VoiceButtonProps {
  state: VoiceState
  onPress: () => void
  onRelease: () => void
}

const VoiceButton = ({ state, onPress, onRelease }: VoiceButtonProps) => {
  const getButtonVariant = () => {
    switch (state) {
      case 'idle':
        return 'idle'
      case 'listening':
        return 'listening'
      case 'processing':
        return 'processing'
      case 'speaking':
        return 'speaking'
      case 'error':
        return 'error'
      default:
        return 'idle'
    }
  }

  // Get accessible label for current state
  const getAriaLabel = () => {
    switch (state) {
      case 'idle':
        return 'Press and hold to speak with Rose'
      case 'listening':
        return 'Listening... Release to send your message'
      case 'processing':
        return 'Processing your message, please wait'
      case 'speaking':
        return 'Rose is speaking, please wait'
      case 'error':
        return 'Error occurred. Press to try again'
      default:
        return 'Voice input button'
    }
  }

  // Get live region announcement for screen readers
  const getLiveRegionText = () => {
    switch (state) {
      case 'listening':
        return 'Recording started. Release button when finished speaking.'
      case 'processing':
        return 'Processing your message.'
      case 'speaking':
        return 'Rose is responding.'
      case 'error':
        return 'An error occurred. Please try again.'
      default:
        return ''
    }
  }

  // Keyboard shortcuts: Space or Enter to activate
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if button is not disabled and key is Space or Enter
      if ((e.code === 'Space' || e.code === 'Enter') && (state === 'idle' || state === 'error')) {
        e.preventDefault()
        onPress()
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      // Release on key up if we're listening
      if ((e.code === 'Space' || e.code === 'Enter') && state === 'listening') {
        e.preventDefault()
        onRelease()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [state, onPress, onRelease])

  const buttonVariants = {
    idle: {
      scale: 1,
      boxShadow: '0 0 30px rgba(232, 213, 196, 0.3)',
    },
    listening: {
      scale: 1.1,
      boxShadow: '0 0 50px rgba(232, 213, 196, 0.6)',
    },
    processing: {
      scale: 1,
      boxShadow: '0 0 40px rgba(168, 159, 145, 0.5)',
    },
    speaking: {
      scale: 1.05,
      boxShadow: '0 0 45px rgba(232, 213, 196, 0.5)',
    },
    error: {
      scale: 1,
      boxShadow: '0 0 40px rgba(220, 100, 100, 0.5)',
    },
  }

  const pulseVariants = {
    idle: {
      scale: [1, 1.05, 1],
      opacity: [0.5, 0.7, 0.5],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    listening: {
      scale: [1, 1.2, 1],
      opacity: [0.6, 0.9, 0.6],
      transition: {
        duration: 1,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    processing: {
      rotate: 360,
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: 'linear',
      },
    },
    speaking: {
      scale: [1, 1.1, 1],
      opacity: [0.6, 0.8, 0.6],
      transition: {
        duration: 1.5,
        repeat: Infinity,
        ease: 'easeInOut',
      },
    },
    error: {
      scale: 1,
      opacity: 0.7,
    },
  }

  const handleMouseDown = () => {
    if (state === 'idle' || state === 'error') {
      onPress()
    }
  }

  const handleMouseUp = () => {
    if (state === 'listening') {
      onRelease()
    }
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    e.preventDefault()
    if (state === 'idle' || state === 'error') {
      onPress()
    }
  }

  const handleTouchEnd = (e: React.TouchEvent) => {
    e.preventDefault()
    if (state === 'listening') {
      onRelease()
    }
  }

  const isDisabled = state === 'processing' || state === 'speaking'

  return (
    <div className="voice-button-container">
      {/* Screen reader live region for state announcements */}
      <div 
        className="sr-only" 
        role="status" 
        aria-live="polite" 
        aria-atomic="true"
      >
        {getLiveRegionText()}
      </div>

      <motion.div
        className={`voice-button-pulse ${getButtonVariant()}`}
        variants={pulseVariants}
        animate={getButtonVariant()}
        aria-hidden="true"
      />
      
      <motion.button
        className={`voice-button ${getButtonVariant()}`}
        variants={buttonVariants}
        animate={getButtonVariant()}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        disabled={isDisabled}
        whileTap={!isDisabled ? { scale: 0.95 } : {}}
        aria-label={getAriaLabel()}
        aria-pressed={state === 'listening'}
        aria-disabled={isDisabled}
        role="button"
        tabIndex={0}
      >
        <div className="button-icon">
          {state === 'idle' && (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
          )}
          {state === 'listening' && (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="8" />
            </svg>
          )}
          {state === 'processing' && (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" strokeDasharray="60" strokeDashoffset="15" />
            </svg>
          )}
          {state === 'speaking' && (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
            </svg>
          )}
          {state === 'error' && (
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          )}
        </div>
      </motion.button>
    </div>
  )
}

export default VoiceButton
