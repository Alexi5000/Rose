import { useState, useEffect } from 'react'
import VoiceButton from './components/VoiceButton'
import AudioVisualizer from './components/AudioVisualizer'
import StatusIndicator from './components/StatusIndicator'
import ErrorBoundary from './components/ErrorBoundary'
import { useVoiceRecording } from './hooks/useVoiceRecording'
import { useAudioPlayback } from './hooks/useAudioPlayback'
import { apiClient } from './services/apiClient'
import './App.css'

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error'

function App() {
  const [voiceState, setVoiceState] = useState<VoiceState>('idle')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [responseText, setResponseText] = useState<string>('')

  const { startRecording, stopRecording, audioBlob, isRecording } = useVoiceRecording()
  const { playAudio, isPlaying } = useAudioPlayback()

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const session = await apiClient.startSession()
        setSessionId(session.session_id)
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
      
      // Play audio response
      await playAudio(response.audio_url)
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

  return (
    <ErrorBoundary>
      <div className="app">
        <div className="container">
          <header className="header">
            <h1 className="title">Rose</h1>
            <p className="subtitle">Healer Shaman</p>
          </header>

          <main className="main">
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

            {responseText && voiceState === 'idle' && (
              <div className="response-text">
                <p>{responseText}</p>
              </div>
            )}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  )
}

export default App
