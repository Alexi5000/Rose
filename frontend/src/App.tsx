import { useState, useEffect } from 'react'
import VoiceButton from './components/VoiceButton'
import AudioVisualizer from './components/AudioVisualizer'
import StatusIndicator from './components/StatusIndicator'
import NetworkStatus from './components/NetworkStatus'
import TimeoutIndicator from './components/TimeoutIndicator'
import ErrorBoundary from './components/ErrorBoundary'
import { useVoiceRecording } from './hooks/useVoiceRecording'
import { useAudioPlayback } from './hooks/useAudioPlayback'
import { useNetworkStatus } from './hooks/useNetworkStatus'
import { useSessionPersistence } from './hooks/useSessionPersistence'
import { useOperationTimeout } from './hooks/useOperationTimeout'
import { apiClient } from './services/apiClient'
import './App.css'

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'

function App() {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [responseText, setResponseText] = useState<string>('')

  const { startRecording, stopRecording, audioBlob } = useVoiceRecording()
  const { playAudio, isPlaying } = useAudioPlayback()
  const { isOnline, wasOffline } = useNetworkStatus()
  const { sessionId, saveSession } = useSessionPersistence()
  
  // Track timeout for processing operations
  const { showWarning, showTimeout, elapsedSeconds } = useOperationTimeout(
    voiceState === 'processing',
    { warningThreshold: 10000, timeoutThreshold: 30000 }
  )

  // Initialize session on mount (or restore from localStorage)
  useEffect(() => {
    const initSession = async () => {
      // Skip if we already have a valid session from localStorage
      if (sessionId) {
        console.log('Restored session from localStorage:', sessionId)
        return
      }

      try {
        const session = await apiClient.startSession()
        saveSession(session.session_id)
      } catch (error) {
        console.error('Failed to initialize session:', error)
        setErrorMessage('Failed to connect to Rose. Please refresh the page.')
        setVoiceState('error')
      }
    }
    initSession()
  }, [])

  // Update voice state based on playback
  useEffect(() => {
    if (isPlaying) {
      setVoiceState('speaking')
    } else if (voiceState === 'speaking') {
      setVoiceState('idle')
    }
  }, [isPlaying])

  // Process audio when recording stops
  useEffect(() => {
    if (audioBlob && sessionId) {
      processVoiceInput(audioBlob)
    }
  }, [audioBlob, sessionId])

  const processVoiceInput = async (audio: Blob) => {
    if (!sessionId) return

    setVoiceState('processing')
    setErrorMessage(null)

    try {
      const response = await apiClient.processVoice(audio, sessionId)
      setResponseText(response.text)
      
      // Play audio response with fallback to text-only display
      try {
        await playAudio(response.audio_url)
      } catch (audioError) {
        console.error('Audio playback error:', audioError)
        // Fallback: Show text response even if audio fails
        setVoiceState('idle')
        // Text is already set above, so user can read the response
      }
    } catch (error) {
      console.error('Voice processing error:', error)
      setErrorMessage('I couldn\'t hear that clearly. Could you try again?')
      setVoiceState('error')
      
      // Auto-reset error state after 3 seconds
      setTimeout(() => {
        if (voiceState === 'error') {
          setVoiceState('idle')
          setErrorMessage(null)
        }
      }, 3000)
    }
  }

  const handleButtonPress = () => {
    // Prevent interaction when offline
    if (!isOnline) {
      setErrorMessage('No internet connection. Please check your network.')
      setVoiceState('error')
      return
    }

    if (voiceState === 'idle' || voiceState === 'error') {
      setVoiceState('listening')
      setErrorMessage(null)
      startRecording()
    }
  }

  const handleButtonRelease = () => {
    if (voiceState === 'listening') {
      stopRecording()
    }
  }

  const handleRetry = () => {
    setVoiceState('idle')
    setErrorMessage(null)
  }

  // Handle network reconnection
  useEffect(() => {
    if (isOnline && wasOffline && voiceState === 'error') {
      // Auto-retry if we were in error state due to network issues
      setVoiceState('idle')
      setErrorMessage(null)
    }
  }, [isOnline, wasOffline])

  return (
    <ErrorBoundary>
      <div className="app">
        {/* Skip link for keyboard navigation */}
        <a href="#main-content" className="skip-link">
          Skip to main content
        </a>

        <NetworkStatus isOnline={isOnline} wasOffline={wasOffline} />
        
        <div className="container">
          <header className="header" role="banner">
            <h1 className="title">Rose</h1>
            <p className="subtitle">Healer Shaman</p>
          </header>

          <main className="main" id="main-content" role="main">
            <AudioVisualizer 
              isActive={voiceState === 'listening' || voiceState === 'speaking'}
              isListening={voiceState === 'listening'}
            />

            <VoiceButton
              state={voiceState}
              onPress={handleButtonPress}
              onRelease={handleButtonRelease}
            />

            <StatusIndicator 
              state={voiceState}
              errorMessage={errorMessage}
              onRetry={handleRetry}
            />

            {(showWarning || showTimeout) && (
              <TimeoutIndicator
                showWarning={showWarning}
                showTimeout={showTimeout}
                elapsedSeconds={elapsedSeconds}
              />
            )}

            {responseText && voiceState === 'idle' && (
              <div className="response-text" role="region" aria-label="Rose's response">
                <p>{responseText}</p>
              </div>
            )}

            <div className="keyboard-shortcuts" role="complementary" aria-label="Keyboard shortcuts">
              <details>
                <summary>Keyboard Shortcuts</summary>
                <ul>
                  <li><kbd>Space</kbd> or <kbd>Enter</kbd> - Press and hold to speak, release to send</li>
                  <li><kbd>Tab</kbd> - Navigate between interactive elements</li>
                </ul>
              </details>
            </div>
          </main>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default App
