import { useState, useEffect, Suspense, useRef } from 'react'
import { IceCaveScene } from './components/Scene/IceCaveScene'
import { HeroTitle } from './components/UI/HeroTitle'
import { VoiceButton } from './components/UI/VoiceButton'
import { LoadingScreen } from './components/UI/LoadingScreen'
import { SettingsPanel } from './components/UI/SettingsPanel'
import { KeyboardHelp } from './components/UI/KeyboardHelp'
import { WebGLFallback } from './components/UI/WebGLFallback'
import { SmoothScrollWrapper } from './components/Layout/SmoothScrollWrapper'
import { useVoiceInteraction } from './hooks/useVoiceInteraction'
import { useAudioAnalyzer } from './hooks/useAudioAnalyzer'
import { useAmbientAudio } from './hooks/useAmbientAudio'
import { useAssetLoader } from './hooks/useAssetLoader'
import { useWebGLDetection } from './hooks/useWebGLDetection'
import { useHealthCheck } from './hooks/useHealthCheck'
import { apiClient } from './services/apiClient'
import { getAutoDismissTimeout, shouldAutoDismiss } from './config/errorMessages'
import './App.css'

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking'

function App() {
  const [reducedMotion, setReducedMotion] = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const errorTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Health check - verify backend connectivity on mount
  const {
    isHealthy,
    error: healthError,
    version: apiVersion,
    isLoading: healthCheckLoading
  } = useHealthCheck()

  // WebGL detection - Requirements: 6.5
  const {
    isSupported: webglSupported,
    isChecking: webglChecking,
    capabilities: webglCapabilities,
    retry: retryWebGL
  } = useWebGLDetection()

  // Progressive asset loading (only if WebGL is supported)
  const {
    isLoading,
    progress: loadProgress,
    error: loadError,
  } = useAssetLoader({
    enabled: webglSupported,
    onProgress: (progress) => {
      console.log(`Loading ${progress.phase}: ${progress.percentage}% (${progress.currentAsset || ''})`)
    },
    onComplete: () => {
      console.log('All assets loaded successfully')
    },
    onError: (err) => {
      console.error('Asset loading error:', err)
      setError('Failed to load scene assets. Please refresh the page.')
    },
  })

  // Display health check error if backend is unreachable
  useEffect(() => {
    if (healthError) {
      setError(healthError)
    } else if (apiVersion) {
      console.log('✅ Connected to Rose API version:', apiVersion)
    }
  }, [healthError, apiVersion])

  // Auto-dismiss transient errors after timeout
  // Requirements: 7.4 - Auto-dismiss transient errors after 5 seconds
  useEffect(() => {
    // Clear any existing timeout
    if (errorTimeoutRef.current) {
      clearTimeout(errorTimeoutRef.current)
      errorTimeoutRef.current = null
    }

    // If there's an error, check if it should auto-dismiss
    if (error) {
      const timeout = getAutoDismissTimeout(error)
      
      if (timeout !== null) {
        console.log(`⏱️ Error will auto-dismiss in ${timeout}ms:`, error)
        
        errorTimeoutRef.current = setTimeout(() => {
          console.log('✅ Auto-dismissing transient error')
          setError(null)
          errorTimeoutRef.current = null
        }, timeout)
      } else {
        console.log('📌 Error requires manual dismissal:', error)
      }
    }

    // Cleanup timeout on unmount or when error changes
    return () => {
      if (errorTimeoutRef.current) {
        clearTimeout(errorTimeoutRef.current)
        errorTimeoutRef.current = null
      }
    }
  }, [error])

  // Initialize session on mount (only if health check passed)
  useEffect(() => {
    // Don't initialize session if health check failed
    if (isHealthy === false) {
      return
    }

    // Wait for health check to complete
    if (isHealthy === null) {
      return
    }

    const initSession = async () => {
      try {
        // Check for existing session in localStorage
        const storedSessionId = localStorage.getItem('rose_session_id')
        if (storedSessionId) {
          setSessionId(storedSessionId)
          console.log('Restored session from localStorage:', storedSessionId)
          return
        }

        // Create new session
        const session = await apiClient.startSession()
        setSessionId(session.session_id)
        localStorage.setItem('rose_session_id', session.session_id)
        console.log('Created new session:', session.session_id)
      } catch (err) {
        console.error('Failed to initialize session:', err)
        setError('Failed to connect to Rose. Please refresh the page.')
      }
    }

    initSession()
  }, [isHealthy])

  // Voice interaction hook
  const {
    voiceState,
    startRecording,
    stopRecording,
    audioElement,
    error: voiceError,
  } = useVoiceInteraction({
    sessionId,
    onError: (errorMsg) => setError(errorMsg),
  })

  // Audio analyzer for visual effects
  const { amplitude } = useAudioAnalyzer(audioElement)

  // Ambient audio system
  const {
    volume: ambientVolume,
    setVolume: setAmbientVolume,
    duck,
    unduck,
  } = useAmbientAudio({
    enabled: true,
  })

  // Handle ambient audio ducking during voice interaction
  useEffect(() => {
    if (voiceState === 'listening' || voiceState === 'processing' || voiceState === 'speaking') {
      duck()
    } else {
      unduck()
    }
  }, [voiceState, duck, unduck])

  // Detect prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReducedMotion(mediaQuery.matches)

    const handleChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  // Display loading errors
  useEffect(() => {
    if (loadError) {
      setError(loadError.message)
    }
  }, [loadError])

  // Keyboard navigation for voice interaction
  // Requirements: 5.5 - Keyboard accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle if not in an input field or range slider
      if (
        e.target instanceof HTMLInputElement || 
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLButtonElement
      ) {
        return
      }

      switch (e.key) {
        case ' ':
        case 'Enter':
          // Space or Enter to activate voice button
          e.preventDefault()
          if (voiceState === 'idle' && !error) {
            startRecording()
          }
          break
        case 'Escape':
          // Escape to cancel recording
          e.preventDefault()
          if (voiceState === 'listening') {
            stopRecording()
          }
          break
      }
    }

    const handleKeyUp = (e: KeyboardEvent) => {
      // Only handle if not in an input field
      if (
        e.target instanceof HTMLInputElement || 
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLButtonElement
      ) {
        return
      }

      // Release Space/Enter to stop recording (push-to-talk behavior)
      if ((e.key === ' ' || e.key === 'Enter') && voiceState === 'listening') {
        e.preventDefault()
        stopRecording()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('keyup', handleKeyUp)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('keyup', handleKeyUp)
    }
  }, [voiceState, startRecording, stopRecording, error])

  // Show WebGL fallback if not supported
  // Requirements: 6.5 - Provide graceful fallback for unsupported browsers
  if (!webglChecking && !webglSupported && webglCapabilities) {
    return <WebGLFallback capabilities={webglCapabilities} onRetry={retryWebGL} />
  }

  return (
    <SmoothScrollWrapper enabled={false}>
      <div className="relative w-full h-screen overflow-hidden bg-gradient-to-b from-[#0a1e3d] to-[#1e4d8b]">
        {/* Skip link for keyboard navigation */}
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-white focus:text-black"
        >
          Skip to main content
        </a>

        {/* Loading screen with progressive asset loading and health check */}
        <LoadingScreen 
          isLoading={isLoading || webglChecking || healthCheckLoading} 
          progress={loadProgress.percentage}
          currentAsset={loadProgress.currentAsset}
          phase={loadProgress.phase}
        />

        {/* Error message overlay */}
        {(error || voiceError) && !isLoading && (
          <div className="absolute top-24 left-1/2 -translate-x-1/2 z-20 max-w-md px-4">
            <div className="bg-red-500/20 backdrop-blur-md border border-red-500/30 rounded-lg p-4 relative">
              <p className="text-white text-sm text-center pr-8">{error || voiceError}</p>
              
              {/* Dismiss button */}
              <button
                onClick={() => {
                  setError(null)
                  console.log('🗑️ Error manually dismissed')
                }}
                className="absolute top-2 right-2 text-white/70 hover:text-white transition-colors"
                aria-label="Dismiss error"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              
              {/* Auto-dismiss indicator */}
              {(error && shouldAutoDismiss(error)) && (
                <p className="text-white/50 text-xs text-center mt-2">
                  Auto-dismissing in 5 seconds...
                </p>
              )}
            </div>
          </div>
        )}

        {/* 3D Scene */}
        {!isLoading && sessionId && (
          <Suspense fallback={null}>
            <IceCaveScene
              voiceState={voiceState}
              audioAmplitude={amplitude}
              reducedMotion={reducedMotion}
            />
          </Suspense>
        )}

        {/* UI Overlay */}
        {!isLoading && (
          <div id="main-content" role="main">
            {/* Hero Title - positioned at top center */}
            <HeroTitle />

            {/* Voice Button - positioned over water surface area (bottom center) */}
            <VoiceButton
              voiceState={voiceState}
              onStartRecording={startRecording}
              onStopRecording={stopRecording}
              audioAmplitude={amplitude}
              disabled={!sessionId || !!error}
            />

            {/* Settings Panel - positioned at top right */}
            <SettingsPanel
              ambientVolume={ambientVolume}
              onAmbientVolumeChange={setAmbientVolume}
              reducedMotion={reducedMotion}
              onReducedMotionChange={setReducedMotion}
            />

            {/* Keyboard Help - positioned at bottom right */}
            <KeyboardHelp />
          </div>
        )}
      </div>
    </SmoothScrollWrapper>
  )
}

export default App
