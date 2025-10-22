import { motion, AnimatePresence } from 'framer-motion'
import { VoiceState } from '../App'
import './StatusIndicator.css'

interface StatusIndicatorProps {
  state: VoiceState
  errorMessage: string | null
  onRetry: () => void
}

const StatusIndicator = ({ state, errorMessage, onRetry }: StatusIndicatorProps) => {
  const getStatusMessage = () => {
    switch (state) {
      case 'idle':
        return 'Press and hold to speak'
      case 'listening':
        return 'Listening...'
      case 'processing':
        return 'Processing your message...'
      case 'speaking':
        return 'Rose is speaking...'
      case 'error':
        return errorMessage || 'Something went wrong'
      default:
        return ''
    }
  }

  const getStatusColor = () => {
    switch (state) {
      case 'error':
        return '#dc6464'
      case 'listening':
        return '#e8d5c4'
      case 'processing':
        return '#a89f91'
      case 'speaking':
        return '#d4c4b0'
      default:
        return '#8a8175'
    }
  }

  return (
    <div className="status-indicator">
      <AnimatePresence mode="wait">
        <motion.div
          key={state}
          className="status-message"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          style={{ color: getStatusColor() }}
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          {getStatusMessage()}
        </motion.div>
      </AnimatePresence>

      {state === 'error' && (
        <motion.button
          className="retry-button"
          onClick={onRetry}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          aria-label="Retry voice input"
        >
          Try Again
        </motion.button>
      )}
    </div>
  )
}

export default StatusIndicator
