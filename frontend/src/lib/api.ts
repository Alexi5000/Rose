/**
 * 🌐 API Client for Rose Backend
 *
 * Handles communication with FastAPI backend for voice processing.
 */

import axios, { type AxiosInstance, type AxiosError } from 'axios';
import { VOICE_PROCESS_ENDPOINT, API_TIMEOUT_MS, API_BASE_URL } from '@/config/voice';
import type {
  VoiceResponse,
  ApiError,
  MemoryMode,
  PipelineTimings,
  SessionMemoryExport,
  SessionMemoryForget,
  SessionMemoryPreferences,
  WebSocketVoiceTimings,
} from '@/types/voice';

/**
 * Session response from backend
 */
interface SessionResponse {
  session_id: string;
  message: string;
}

const isPipelineTimings = (
  timings: PipelineTimings | WebSocketVoiceTimings
): timings is PipelineTimings => 'total_ms' in timings;

const SESSION_ID_IN_PATH = /\/session\/[^/?#]+/g;
const SESSION_ID_IN_QUERY = /([?&]session_id=)[^&#]+/g;

export const sanitizeApiUrlForLog = (url: string | undefined): string => {
  if (!url) {
    return '[unknown-url]';
  }

  return url
    .replace(SESSION_ID_IN_PATH, '/session/[session_id]')
    .replace(SESSION_ID_IN_QUERY, '$1[session_id]');
};

export const voiceResponseLogSummary = (response: VoiceResponse): Record<string, unknown> => ({
  has_user_text: Boolean(response.user_text),
  user_text_length: response.user_text?.length ?? 0,
  response_text_length: response.text.length,
  has_audio_url: Boolean(response.audio_url),
  has_audio_data: Boolean(response.audio_data),
  audio_streamed: Boolean(response.audio_streamed),
  has_timings: Boolean(response.timings),
});

/**
 * Create configured axios instance
 */
const createClient = (): AxiosInstance => {
  const client = axios.create({
    timeout: API_TIMEOUT_MS,
    headers: {
      'Accept': 'application/json',
    },
  });

  // Request interceptor - add logging
  client.interceptors.request.use(
    (config) => {
      console.log(`API Request: ${config.method?.toUpperCase()} ${sanitizeApiUrlForLog(config.url)}`);
      return config;
    },
    (error) => {
      console.error('Request error:', error?.name ?? 'unknown');
      return Promise.reject(error);
    }
  );

  // Response interceptor - add logging and error handling
  client.interceptors.response.use(
    (response) => {
      console.log(`API Response: ${response.status} ${sanitizeApiUrlForLog(response.config.url)}`);
      return response;
    },
    (error: AxiosError<ApiError>) => {
      if (error.response) {
        // Server responded with error status
        console.error(
          `API Error: ${error.response.status} ${sanitizeApiUrlForLog(error.response.config.url)}`
        );
      } else if (error.request) {
        // Request made but no response
        console.error('Network error: No response from server');
      } else {
        // Something else happened
        console.error('Request setup error:', error.message);
      }
      return Promise.reject(error);
    }
  );

  return client;
};

const client = createClient();

/**
 * Create a new session with Rose
 *
 * @returns Promise with session ID and welcome message
 * @throws AxiosError if request fails
 */
export async function createSession(): Promise<SessionResponse> {
  console.log('Creating new session...');

  const response = await client.post<SessionResponse>(
    `${API_BASE_URL}/session/start`
  );

  console.log('Session created');

  return response.data;
}

/**
 * Process voice input and get Rose's response
 *
 * @param audioBlob - Recorded audio from user
 * @param sessionId - Current session ID (REQUIRED)
 * @returns Promise with transcribed text, audio URL, and session ID
 * @throws AxiosError if request fails
 */
export async function processVoice(
  audioBlob: Blob,
  sessionId: string
): Promise<VoiceResponse> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');
  formData.append('session_id', sessionId);

  console.log(`Sending audio: ${(audioBlob.size / 1024).toFixed(2)} KB`);

  const response = await client.post<VoiceResponse>(
    VOICE_PROCESS_ENDPOINT,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }
  );

  console.log('Voice response received', voiceResponseLogSummary(response.data));

  // Log timing metrics if available (for performance analysis)
  if (response.data.timings) {
    const t = response.data.timings;
    if (isPipelineTimings(t)) {
      console.log(
        `Pipeline Timings: Total=${t.total_ms.toFixed(0)}ms | ` +
        `STT=${t.stt_ms.toFixed(0)}ms | Workflow=${t.workflow_ms.toFixed(0)}ms | ` +
        `TTS=${t.tts_ms.toFixed(0)}ms`
      );
    } else {
      console.log(
        `WebSocket Timings: Total=${t.turn_total_ms.toFixed(0)}ms | ` +
        `FirstAudio=${t.mic_to_first_audio_ms?.toFixed(0) ?? 'n/a'}ms | ` +
        `Provider=${t.stt_provider}`
      );
    }
  }

  return response.data;
}

export async function getMemoryPreferences(sessionId: string): Promise<SessionMemoryPreferences> {
  const response = await client.get<SessionMemoryPreferences>(
    `${API_BASE_URL}/session/${sessionId}/memory-preferences`
  );

  return response.data;
}

export async function updateMemoryPreferences(
  sessionId: string,
  memoryMode: MemoryMode
): Promise<SessionMemoryPreferences> {
  const response = await client.post<SessionMemoryPreferences>(
    `${API_BASE_URL}/session/${sessionId}/memory-preferences`,
    { memory_mode: memoryMode },
    {
      headers: {
        'Content-Type': 'application/json',
      },
    }
  );

  return response.data;
}

export async function exportSessionMemories(sessionId: string): Promise<SessionMemoryExport> {
  const response = await client.get<SessionMemoryExport>(
    `${API_BASE_URL}/session/${sessionId}/memory/export`
  );

  return response.data;
}

export async function forgetSessionMemories(sessionId: string): Promise<SessionMemoryForget> {
  const response = await client.post<SessionMemoryForget>(
    `${API_BASE_URL}/session/${sessionId}/memory/forget`
  );

  return response.data;
}

/**
 * Extract user-friendly error message from API error
 *
 * @param error - Axios error from failed request
 * @returns User-friendly error message
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;

    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }

    if (axiosError.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again.';
    }

    if (axiosError.code === 'ERR_NETWORK') {
      return 'Network error. Please check your connection.';
    }

    if (axiosError.response?.status === 429) {
      return 'Too many requests. Please wait a moment.';
    }

    if (axiosError.response?.status === 413) {
      return 'Audio file too large. Please speak for less time.';
    }

    if (axiosError.response?.status && axiosError.response.status >= 500) {
      return 'Server error. Please try again later.';
    }
  }

  return 'An unexpected error occurred. Please try again.';
}
