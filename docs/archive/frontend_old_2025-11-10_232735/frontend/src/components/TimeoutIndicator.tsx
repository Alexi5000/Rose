import { motion, AnimatePresence } from 'framer-motion'
import './TimeoutIndicator.css'

interface TimeoutIndicatorProps {
  showWarning: boolean
  showTimeout: boolean
  elapsedSeconds: number
}

const TimeoutIndicator = ({ showWarning, showTimeout, elapsedSeconds }: TimeoutIndicatorProps) => {
  return (
    <AnimatePresence>
      {showTimeout && (
        <motion.div
          className="timeout-indicator timeout"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.2 }}
          role="status"
          aria-live="polite"
        >
          <div className="timeout-icon" aria-hidden="true">⏱️</div>
          <div className="timeout-text">
            <strong>This is taking longer than expected</strong>
            <span>Processing for {elapsedSeconds} seconds. Please wait or try again</span>
          </div>
        </motion.div>
      )}
      {showWarning && !showTimeout && (
        <motion.div
          className="timeout-indicator warning"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.2 }}
          role="status"
          aria-live="polite"
        >
          <div className="timeout-icon" aria-hidden="true">⏳</div>
          <div className="timeout-text">
            <span>Processing your request for {elapsedSeconds} seconds</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default TimeoutIndicator
