import { useState, useEffect } from 'react'
import { apiClient } from '../services/apiClient'
import { HEALTH_CHECK_ERRORS } from '../config/errorMessages'

interface HealthCheckResult {
  isHealthy: boolean | null
  error: string | null
  version: string | null
  isLoading: boolean
}

/**
 * 🏥 Health Check Hook
 * 
 * Verifies backend connectivity on mount by calling the /api/v1/health endpoint.
 * Returns health status, error state, API version, and loading state.
 */
export const useHealthCheck = (): HealthCheckResult => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        console.log('🏥 Checking backend health...')
        setIsLoading(true)
        
        const response = await apiClient.checkHealth()
        
        console.log('✅ Backend healthy:', response)
        setIsHealthy(true)
        setVersion(response.version || null)
        setError(null)
      } catch (err) {
        console.error('❌ Backend health check failed:', err)
        
        // Use error message from API client if available, otherwise use default
        const errorMessage = err instanceof Error 
          ? err.message 
          : HEALTH_CHECK_ERRORS.HEALTH_CHECK_FAILED
        
        setError(errorMessage)
        setIsHealthy(false)
        setVersion(null)
      } finally {
        setIsLoading(false)
      }
    }

    checkHealth()
  }, [])

  return { isHealthy, error, version, isLoading }
}
