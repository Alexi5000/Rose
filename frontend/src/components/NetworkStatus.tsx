import { motion, AnimatePresence } from 'framer-motion'
import './NetworkStatus.css'

interface NetworkStatusProps {
  isOnline: boolean
  wasOffline: boolean
}

const NetworkStatus = ({ isOnline, wasOffline }: NetworkStatusProps) => {
  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          className="network-status offline"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          role="alert"
          aria-live="assertive"
        >
          <div className="network-status-icon" aria-hidden="true">⚠️</div>
          <div className="network-status-text">
            <strong>No Internet Connection</strong>
            <span>Please check your network and try again</span>
          </div>
        </motion.div>
      )}
      {isOnline && wasOffline && (
        <motion.div
          className="network-status online"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          role="status"
          aria-live="polite"
        >
          <div className="network-status-icon" aria-hidden="true">✓</div>
          <div className="network-status-text">
            <strong>Back Online</strong>
            <span>Connection restored</span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default NetworkStatus
