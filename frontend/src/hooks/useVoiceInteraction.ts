import { useState, useRef, useCallback, useEffect } from 'react';
import { apiClient } from '../services/apiClient';
import { refinedVoiceRecordingConfig } from '../config/refinedAudio';
import {
  MICROPHONE_ERRORS,
  VOICE_PROCESSING_ERRORS,
  PLAYBACK_ERRORS,
  SESSION_ERRORS,
} from '../config/errorMessages';

/**
 * useVoiceInteraction Hook
 * 
 * Comprehensive hook for managing voice interactions with Rose
 * 
 * Task 22.3: Enhanced with refined audio settings for better quality
 * 
 * Handles microphone access, recording, processing, and playback
 * Manages state transitions: idle → listening → processing → speaking → idle
 * 
 * Requirements: 3.2, 3.3, 3.4, 11.7
 */

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

interface UseVoiceInteractionOptions {
  sessionId: string;
  onError?: (error: string) => void;
  onResponseText?: (text: string) => void;
}

export const useVoiceInteraction = (options: UseVoiceInteractionOptions) => {
  const { sessionId, onError, onResponseText } = options;

  // State management
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [error, setError] = useState<string | null>(null);
  const [responseText, setResponseText] = useState<string>('');

  // Refs for media handling
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  /**
   * Start recording audio from microphone
   */
  const startRecording = useCallback(async () => {
    try {
      setError(null);
      audioChunksRef.current = [];

      // Request microphone access with refined optimal settings
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: refinedVoiceRecordingConfig.audioConstraints,
      });

      streamRef.current = stream;

      // Determine the best audio format
      const mimeType = MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/mp4')
        ? 'audio/mp4'
        : 'audio/ogg';

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });

        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
        }

        // Validate audio size before processing (prevent invalid files from reaching backend)
        if (audioBlob.size < refinedVoiceRecordingConfig.minAudioSizeBytes) {
          console.warn(
            `⚠️ Audio too short: ${audioBlob.size} bytes (minimum ${refinedVoiceRecordingConfig.minAudioSizeBytes} bytes)`
          );
          const errorMessage = '🎤 Recording too short. Please hold the button longer and speak clearly.';
          setError(errorMessage);
          setVoiceState('idle');
          if (onError) onError(errorMessage);
          return;
        }

        console.log(`✅ Audio recorded: ${audioBlob.size} bytes`);

        // Process the recorded audio
        await processVoiceInput(audioBlob);
      };

      mediaRecorder.start();
      setVoiceState('listening');
    } catch (err) {
      console.error('❌ Error starting recording:', err);
      
      // Map browser errors to user-friendly messages with emojis
      let errorMessage: string = MICROPHONE_ERRORS.GENERIC_ERROR;
      if (err instanceof Error) {
        if (err.name === 'NotFoundError') {
          errorMessage = MICROPHONE_ERRORS.NOT_FOUND;
        } else if (err.name === 'NotAllowedError') {
          errorMessage = MICROPHONE_ERRORS.PERMISSION_DENIED;
        } else if (err.name === 'NotReadableError') {
          errorMessage = MICROPHONE_ERRORS.IN_USE;
        }
      }
      
      setError(errorMessage);
      setVoiceState('idle');
      if (onError) onError(errorMessage);
    }
  }, [sessionId, onError]);

  /**
   * Stop recording audio
   */
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'listening') {
      mediaRecorderRef.current.stop();
      // State will transition to 'processing' in processVoiceInput
    }
  }, [voiceState]);

  /**
   * Process recorded audio through backend API
   */
  const processVoiceInput = useCallback(
    async (audioBlob: Blob) => {
      if (!sessionId) {
        const errorMessage = SESSION_ERRORS.SESSION_NOT_FOUND;
        setError(errorMessage);
        setVoiceState('idle');
        if (onError) onError(errorMessage);
        return;
      }

      setVoiceState('processing');
      setError(null);

      try {
        console.log('🎤 Processing voice input...');
        const response = await apiClient.processVoice(audioBlob, sessionId);
        console.log('✅ Voice processing successful');
        setResponseText(response.text);
        if (onResponseText) onResponseText(response.text);

        // Play audio response
        await playAudioResponse(response.audio_url);
      } catch (err) {
        console.error('❌ Voice processing error:', err);
        
        // Use error message from API client if available, otherwise use default
        const errorMessage =
          err instanceof Error ? err.message : VOICE_PROCESSING_ERRORS.TRANSCRIPTION_FAILED;
        
        setError(errorMessage);
        setVoiceState('idle');
        if (onError) onError(errorMessage);
      }
    },
    [sessionId, onError, onResponseText]
  );

  /**
   * Play audio response from Rose
   */
  const playAudioResponse = useCallback(async (audioUrl: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        // Stop any currently playing audio
        if (audioElementRef.current) {
          audioElementRef.current.pause();
          audioElementRef.current = null;
        }

        console.log('🔊 Playing audio response...');
        
        // Create new audio element
        const audio = new Audio(audioUrl);
        audioElementRef.current = audio;

        audio.onplay = () => {
          console.log('✅ Audio playback started');
          setVoiceState('speaking');
        };

        audio.onended = () => {
          console.log('✅ Audio playback completed');
          setVoiceState('idle');
          audioElementRef.current = null;
          resolve();
        };

        audio.onerror = (e) => {
          console.error('❌ Audio playback error:', e);
          const errorMessage = PLAYBACK_ERRORS.PLAYBACK_FAILED;
          setError(errorMessage);
          setVoiceState('idle');
          audioElementRef.current = null;
          if (onError) onError(errorMessage);
          reject(new Error(errorMessage));
        };

        // Play the audio
        audio.play().catch((err) => {
          console.error('❌ Error playing audio:', err);
          const errorMessage = PLAYBACK_ERRORS.PLAYBACK_FAILED;
          setError(errorMessage);
          setVoiceState('idle');
          if (onError) onError(errorMessage);
          reject(err);
        });
      } catch (err) {
        console.error('❌ Error creating audio element:', err);
        const errorMessage = PLAYBACK_ERRORS.AUDIO_LOAD_FAILED;
        setError(errorMessage);
        setVoiceState('idle');
        if (onError) onError(errorMessage);
        reject(err);
      }
    });
  }, [onError]);

  /**
   * Stop any ongoing audio playback
   */
  const stopAudio = useCallback(() => {
    if (audioElementRef.current) {
      audioElementRef.current.pause();
      audioElementRef.current = null;
      setVoiceState('idle');
    }
  }, []);

  /**
   * Cancel recording if in progress
   */
  const cancelRecording = useCallback(() => {
    if (mediaRecorderRef.current && voiceState === 'listening') {
      // Stop recording without processing
      mediaRecorderRef.current.stop();
      audioChunksRef.current = [];
      
      // Clean up stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      
      setVoiceState('idle');
    }
  }, [voiceState]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      // Clean up media stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
      
      // Clean up audio playback
      if (audioElementRef.current) {
        audioElementRef.current.pause();
      }
    };
  }, []);

  return {
    // State
    voiceState,
    error,
    responseText,
    
    // Controls
    startRecording,
    stopRecording,
    cancelRecording,
    stopAudio,
    
    // Status checks
    isListening: voiceState === 'listening',
    isProcessing: voiceState === 'processing',
    isSpeaking: voiceState === 'speaking',
    isIdle: voiceState === 'idle',
    
    // Audio element ref (for audio analysis)
    audioElement: audioElementRef.current,
  };
};
