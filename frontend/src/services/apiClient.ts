import axios, { AxiosInstance } from 'axios'

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
    this.client = axios.create({
      baseURL: '/api/v1',
      timeout: 60000, // 60 seconds for voice processing
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.status, error.response.data)
          throw new Error(error.response.data.detail || 'Server error occurred')
        } else if (error.request) {
          // Request made but no response
          console.error('Network Error:', error.request)
          throw new Error('Network error. Please check your connection.')
        } else {
          // Something else happened
          console.error('Error:', error.message)
          throw new Error(error.message)
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
