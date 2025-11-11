import { useState, useEffect, useRef } from 'react'

interface UseOperationTimeoutOptions {
  warningThreshold?: number // Show warning after this many ms
  timeoutThreshold?: number // Show timeout message after this many ms
}

export const useOperationTimeout = (
  isActive: boolean,
  options: UseOperationTimeoutOptions = {}
) => {
  const {
    warningThreshold = 10000, // 10 seconds
    timeoutThreshold = 30000, // 30 seconds
  } = options

  const [elapsedTime, setElapsedTime] = useState(0)
  const [showWarning, setShowWarning] = useState(false)
  const [showTimeout, setShowTimeout] = useState(false)
  const startTimeRef = useRef<number | null>(null)
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (isActive) {
      // Start tracking time
      startTimeRef.current = Date.now()
      setElapsedTime(0)
      setShowWarning(false)
      setShowTimeout(false)

      intervalRef.current = window.setInterval(() => {
        if (startTimeRef.current) {
          const elapsed = Date.now() - startTimeRef.current
          setElapsedTime(elapsed)

          if (elapsed >= timeoutThreshold) {
            setShowTimeout(true)
          } else if (elapsed >= warningThreshold) {
            setShowWarning(true)
          }
        }
      }, 1000) // Update every second
    } else {
      // Reset when operation completes
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      startTimeRef.current = null
      setElapsedTime(0)
      setShowWarning(false)
      setShowTimeout(false)
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isActive, warningThreshold, timeoutThreshold])

  return {
    elapsedTime,
    showWarning,
    showTimeout,
    elapsedSeconds: Math.floor(elapsedTime / 1000),
  }
}
