import axios, { AxiosInstance } from 'axios'
import {
  CONNECTION_ERRORS,
  SESSION_ERRORS,
  RATE_LIMIT_ERRORS,
  VOICE_PROCESSING_ERRORS,
  GENERIC_ERRORS,
} from '../config/errorMessages'

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
      timeout: 60000, // 60 seconds for voice processing
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
        // Log error with full context
        console.error('❌ API Error:', {
          url: error.config?.url,
          method: error.config?.method?.toUpperCase(),
          status: error.response?.status,
          message: error.message,
        })

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
          
          // Map specific status codes to helpful messages
          if (status === 401 || status === 403) {
            throw new Error(SESSION_ERRORS.SESSION_EXPIRED)
          }
          
          if (status === 413) {
            throw new Error(VOICE_PROCESSING_ERRORS.AUDIO_TOO_LARGE)
          }
          
          if (status === 429) {
            throw new Error(RATE_LIMIT_ERRORS.TOO_MANY_REQUESTS)
          }
          
          if (status >= 500) {
            throw new Error(CONNECTION_ERRORS.SERVER_ERROR)
          }
          
          // Use server-provided error message if available
          const message = data.detail || data.message || CONNECTION_ERRORS.SERVER_ERROR
          throw new Error(message)
        } else if (error.request) {
          // Request made but no response - likely server is down
          throw new Error(CONNECTION_ERRORS.BACKEND_UNREACHABLE)
        } else {
          // Something else happened
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
    const formData = new FormData()
    formData.append('audio', audioBlob, 'recording.webm')
    formData.append('session_id', sessionId)

    const response = await this.client.post<VoiceResponse>('/voice/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    return response.data
  }

  async checkHealth(): Promise<{ status: string; version: string }> {
    const response = await this.client.get('/health')
    return response.data
  }
}

export const apiClient = new ApiClient()
