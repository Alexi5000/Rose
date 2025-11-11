import { useState, useRef, useCallback } from 'react'

export const useAudioPlayback = () => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const playAudio = useCallback(async (audioUrl: string): Promise<void> => {
    try {
      setError(null)
      
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }

      // Create new audio element
      const audio = new Audio(audioUrl)
      audioRef.current = audio

      audio.onplay = () => {
        setIsPlaying(true)
      }

      audio.onended = () => {
        setIsPlaying(false)
        audioRef.current = null
      }

      audio.onerror = (e) => {
        console.error('Audio playback error:', e)
        setError('Failed to play audio response')
        setIsPlaying(false)
        audioRef.current = null
      }

      // Play the audio
      await audio.play()
    } catch (err) {
      console.error('Error playing audio:', err)
      setError('Failed to play audio response')
      setIsPlaying(false)
    }
  }, [])

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
      setIsPlaying(false)
    }
  }, [])

  return {
    playAudio,
    stopAudio,
    isPlaying,
    error,
  }
}
