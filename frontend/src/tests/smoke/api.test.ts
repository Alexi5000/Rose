/**
 * 📤 API Client Smoke Tests
 *
 * Tests API client error handling utilities (simplified for smoke testing).
 */

import { describe, expect, it } from 'vitest';
import { getErrorMessage, sanitizeApiUrlForLog, voiceResponseLogSummary } from '@/lib/api';

console.log('📤 Loading API client tests');

// Constants (no magic numbers!)
const GENERIC_ERROR_MESSAGE = 'Test error';

describe('📤 API Client', () => {
  describe('getErrorMessage', () => {
    it('✅ handles unknown errors gracefully', () => {
      console.log('  🔍 Testing unknown error handling');

      const message = getErrorMessage(new Error(GENERIC_ERROR_MESSAGE));
      expect(message).toContain('unexpected error');

      console.log('  ✅ Unknown error handled gracefully');
    });

    it('✅ handles null/undefined errors', () => {
      console.log('  🔍 Testing null error handling');

      const message1 = getErrorMessage(null);
      expect(message1).toContain('unexpected error');

      const message2 = getErrorMessage(undefined);
      expect(message2).toContain('unexpected error');

      console.log('  ✅ Null/undefined errors handled');
    });

    it('✅ returns string for generic errors', () => {
      console.log('  🔍 Testing return type');

      const message = getErrorMessage({ some: 'object' });
      expect(typeof message).toBe('string');
      expect(message.length).toBeGreaterThan(0);

      console.log('  ✅ Returns valid string');
    });

    it('✅ error messages are user-friendly', () => {
      console.log('  🔍 Testing message readability');

      const message = getErrorMessage(new Error('Technical error'));

      // Should not include technical jargon or stack traces
      expect(message).not.toContain('stack');
      expect(message).not.toContain('TypeError');
      expect(message).not.toContain('undefined');

      console.log('  ✅ Messages are user-friendly');
    });
  });

  describe('privacy-safe logging helpers', () => {
    it('redacts session identifiers from logged API URLs', () => {
      const sanitizedPath = sanitizeApiUrlForLog(
        '/api/v1/session/123e4567-e89b-12d3-a456-426614174000/memory/export'
      );
      const sanitizedQuery = sanitizeApiUrlForLog(
        '/api/v1/voice/ws?session_id=123e4567-e89b-12d3-a456-426614174000'
      );

      expect(sanitizedPath).toBe('/api/v1/session/[session_id]/memory/export');
      expect(sanitizedQuery).toBe('/api/v1/voice/ws?session_id=[session_id]');
      expect(sanitizedPath).not.toContain('123e4567');
      expect(sanitizedQuery).not.toContain('123e4567');
    });

    it('summarizes voice responses without raw transcript text', () => {
      const privateUserText = 'I feel scared and I said a secret name.';
      const privateRoseText = 'I am here with you. Let us take one breath.';

      const summary = voiceResponseLogSummary({
        text: privateRoseText,
        user_text: privateUserText,
        audio_url: '/api/v1/voice/audio/rose.mp3',
        audio_data: 'base64-audio',
        session_id: 'session-123',
      });

      const serialized = JSON.stringify(summary);
      expect(summary).toEqual({
        has_user_text: true,
        user_text_length: privateUserText.length,
        response_text_length: privateRoseText.length,
        has_audio_url: true,
        has_audio_data: true,
        audio_streamed: false,
        has_timings: false,
      });
      expect(serialized).not.toContain(privateUserText);
      expect(serialized).not.toContain(privateRoseText);
      expect(serialized).not.toContain('base64-audio');
      expect(serialized).not.toContain('session-123');
    });
  });
});

console.log('✅ API client tests loaded');
