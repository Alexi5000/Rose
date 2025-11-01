import axios, { AxiosInstance } from 'axios'
import {
  CONNECTION_ERRORS,
  SESSION_ERRORS,
  RATE_LIMIT_ERRORS,
  VOICE_PROCESSING_ERRORS,
  GENERIC_ERRORS,
} from '../config/errorMessages'

// 🎯 API Configuration Constants - No Magic Numbers (Uncle Bob approved)
const API_TIMEOUT_MS = 60000; // 60 seconds for voice processing
const HTTP_STATUS_UNAUTHORIZED = 401;
const HTTP_STATUS_FORBIDDEN = 403;
const HTTP_STATUS_PAYLOAD_TOO_LARGE = 413;
const HTTP_STATUS_TOO_MANY_REQUESTS = 429;
const HTTP_STATUS_INTERNAL_ERROR = 500;

interface SessionResponse {
  session_id: string
  message: string
}

interface VoiceResponse {
  text: string
  audio_url: string
  session_id: string
}

class ApiClient {
  private client: AxiosInstance

  constructor() {
    // Use environment variable for API base URL, fallback to relative path
    const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
    
    console.log('🔌 Initializing API client with base URL:', baseURL)
    
    this.client = axios.create({
      baseURL,
      timeout: API_TIMEOUT_MS,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 📤 Request logging interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Check if browser is online
        if (!navigator.onLine) {
          console.error('❌ No internet connection detected')
          return Promise.reject(new Error(CONNECTION_ERRORS.NO_INTERNET))
        }
        
        // Log outgoing request
        console.log('📤 API Request:', config.method?.toUpperCase(), config.url)
        return config
      },
      (error) => {
        console.error('❌ Request interceptor error:', error)
        return Promise.reject(error)
      }
    )

    // ✅ Response logging interceptor
    this.client.interceptors.response.use(
      (response) => {
        // Log successful response
        console.log('✅ API Response:', response.config.url, 'Status:', response.status)
        return response
      },
      (error) => {
        // 🔍 ENHANCED ERROR LOGGING - Uncle Bob approved
        const errorContext = {
          url: error.config?.url,
          method: error.config?.method?.toUpperCase(),
          status: error.response?.status,
          statusText: error.response?.statusText,
          message: error.message,
          responseData: error.response?.data,
          requestData: error.config?.data instanceof FormData ? '[FormData]' : error.config?.data,
        }
        
        console.error('❌ API Error Details:', errorContext)
        
        // Log full error object for debugging
        console.error('❌ Full Error Object:', error)

        // Map errors to user-friendly messages
        if (error.message === CONNECTION_ERRORS.NO_INTERNET) {
          throw new Error(CONNECTION_ERRORS.NO_INTERNET)
        }
        
        if (error.code === 'ECONNABORTED') {
          throw new Error(CONNECTION_ERRORS.TIMEOUT)
        }

        if (error.response) {
          // Server responded with error status
          const status = error.response.status
          const data = error.response.data
          
          console.error(`❌ Server Error ${status}:`, data)
          
          // Map specific status codes to helpful messages
          if (status === HTTP_STATUS_UNAUTHORIZED || status === HTTP_STATUS_FORBIDDEN) {
            throw new Error(SESSION_ERRORS.SESSION_EXPIRED)
          }
          
          if (status === HTTP_STATUS_PAYLOAD_TOO_LARGE) {
            throw new Error(VOICE_PROCESSING_ERRORS.AUDIO_TOO_LARGE)
          }
          
          if (status === HTTP_STATUS_TOO_MANY_REQUESTS) {
            throw new Error(RATE_LIMIT_ERRORS.TOO_MANY_REQUESTS)
          }
          
          if (status >= HTTP_STATUS_INTERNAL_ERROR) {
            console.error(`❌ 500+ Error - Server Detail: ${data?.detail || 'No detail provided'}`)
            throw new Error(CONNECTION_ERRORS.SERVER_ERROR)
          }
          
          // Use server-provided error message if available
          const message = data.detail || data.message || CONNECTION_ERRORS.SERVER_ERROR
          throw new Error(message)
        } else if (error.request) {
          // Request made but no response - likely server is down
          console.error('❌ No response received from server')
          throw new Error(CONNECTION_ERRORS.BACKEND_UNREACHABLE)
        } else {
          // Something else happened
          console.error('❌ Unknown error type')
          throw new Error(GENERIC_ERRORS.UNKNOWN_ERROR)
        }
      }
    )
  }

  async startSession(): Promise<SessionResponse> {
    const response = await this.client.post<SessionResponse>('/session/start')
    return response.data
  }

  async processVoice(audioBlob: Blob, sessionId: string): Promise<VoiceResponse> {
    console.log('🎙️ API: Preparing voice processing request', {
      audioBlobSize: audioBlob.size,
      audioBlobType: audioBlob.type,
      sessionId,
    });
    
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('session_id', sessionId)
    
    console.log('📤 API: Sending voice processing request to /voice/process');

    const response = await this.client.post<VoiceResponse>('/voice/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    console.log('✅ API: Voice processing response received', {
      textLength: response.data.text.length,
      audioUrl: response.data.audio_url,
    });

    return response.data
  }

  async checkHealth(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/health')
    return response.data
  }
}

export const apiClient = new ApiClient()
