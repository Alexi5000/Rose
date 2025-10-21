import { useState, useEffect } from 'react'

const SESSION_STORAGE_KEY = 'rose_session_id'
const SESSION_EXPIRY_KEY = 'rose_session_expiry'
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000 // 24 hours

export const useSessionPersistence = () => {
  const [sessionId, setSessionId] = useState<string | null>(() => {
    // Try to restore session from localStorage on mount
    const stored = localStorage.getItem(SESSION_STORAGE_KEY)
    const expiry = localStorage.getItem(SESSION_EXPIRY_KEY)
    
    if (stored && expiry) {
      const expiryTime = parseInt(expiry, 10)
      if (Date.now() < expiryTime) {
        return stored
      } else {
        // Session expired, clean up
        localStorage.removeItem(SESSION_STORAGE_KEY)
        localStorage.removeItem(SESSION_EXPIRY_KEY)
      }
    }
    
    return null
  })

  const saveSession = (id: string) => {
    const expiry = Date.now() + SESSION_DURATION_MS
    localStorage.setItem(SESSION_STORAGE_KEY, id)
    localStorage.setItem(SESSION_EXPIRY_KEY, expiry.toString())
    setSessionId(id)
  }

  const clearSession = () => {
    localStorage.removeItem(SESSION_STORAGE_KEY)
    localStorage.removeItem(SESSION_EXPIRY_KEY)
    setSessionId(null)
  }

  // Clean up expired session on mount
  useEffect(() => {
    const expiry = localStorage.getItem(SESSION_EXPIRY_KEY)
    if (expiry && Date.now() >= parseInt(expiry, 10)) {
      clearSession()
    }
  }, [])

  return {
    sessionId,
    saveSession,
    clearSession,
  }
}
