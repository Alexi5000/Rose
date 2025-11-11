import { useState, useEffect } from 'react'
import { detectWebGL, meetsMinimumRequirements, type WebGLCapabilities } from '../utils/webglDetection'

interface UseWebGLDetectionResult {
  isSupported: boolean
  isChecking: boolean
  capabilities: WebGLCapabilities | null
  retry: () => void
}

/**
 * Hook for detecting WebGL support and capabilities
 * Requirements: 6.5 - Detect WebGL support on load
 */
export const useWebGLDetection = (): UseWebGLDetectionResult => {
  const [isChecking, setIsChecking] = useState(true)
  const [capabilities, setCapabilities] = useState<WebGLCapabilities | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  const checkWebGL = () => {
    setIsChecking(true)
    
    // Small delay to ensure DOM is ready
    setTimeout(() => {
      try {
        const detected = detectWebGL()
        setCapabilities(detected)
        
        // Log capabilities for debugging
        console.log('WebGL Detection:', {
          supported: detected.supported,
          version: detected.version,
          renderer: detected.renderer,
          vendor: detected.vendor,
          maxTextureSize: detected.maxTextureSize,
          meetsRequirements: meetsMinimumRequirements(detected)
        })
      } catch (error) {
        console.error('Error during WebGL detection:', error)
        setCapabilities({
          supported: false,
          version: null,
          renderer: null,
          vendor: null,
          maxTextureSize: null,
          error: 'An error occurred while detecting WebGL support'
        })
      } finally {
        setIsChecking(false)
      }
    }, 100)
  }

  useEffect(() => {
    checkWebGL()
  }, [retryCount])

  const retry = () => {
    setRetryCount(prev => prev + 1)
  }

  const isSupported = capabilities ? meetsMinimumRequirements(capabilities) : false

  return {
    isSupported,
    isChecking,
    capabilities,
    retry
  }
}
