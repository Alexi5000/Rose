/* Rose full repository refresh 2026-05-17 */
/**
 * 📤 API Client Smoke Tests
 *
 * Tests API client error handling utilities (simplified for smoke testing).
 */

import { describe, expect, it } from 'vitest';
import { getErrorMessage } from '@/lib/api';

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
});

console.log('✅ API client tests loaded');
