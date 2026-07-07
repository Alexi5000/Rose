/**
 * 🔊 Audio Utilities Smoke Tests
 *
 * Tests RMS calculation and audio analysis utilities.
 * Copied from archive and enhanced for new architecture.
 */

import { describe, expect, it, vi } from 'vitest';
import {
  calculateRms,
  getSupportedMimeType,
  checkAudioSupport,
} from '@/lib/audio-utils';

console.log('🔊 Loading audio-utils tests');

// Constants (no magic numbers!)
const SILENT_SIGNAL = 0;
const HALF_AMPLITUDE = 0.5;
const EXPECTED_MIXED_RMS = 0.5590169943749475;

describe('🔊 Audio Utilities', () => {
  describe('calculateRms', () => {
    it('✅ returns zero for empty input', () => {
      console.log('  🔍 Testing empty array');
      const result = calculateRms(new Float32Array());
      expect(result).toBe(SILENT_SIGNAL);
    });

    it('✅ returns zero for silent signal', () => {
      console.log('  🔍 Testing silent signal');
      const result = calculateRms(new Float32Array([0, 0, 0, 0]));
      expect(result).toBe(SILENT_SIGNAL);
    });

    it('✅ computes RMS for constant signal', () => {
      console.log('  🔍 Testing constant signal');
      const result = calculateRms(new Float32Array([
        HALF_AMPLITUDE,
        HALF_AMPLITUDE,
        HALF_AMPLITUDE,
        HALF_AMPLITUDE,
      ]));
      expect(result).toBeCloseTo(HALF_AMPLITUDE);
    });

    it('✅ computes RMS for mixed signal', () => {
      console.log('  🔍 Testing mixed positive/negative signal');
      const result = calculateRms(new Float32Array([0.25, -0.25, 0.75, -0.75]));
      expect(result).toBeCloseTo(EXPECTED_MIXED_RMS);
    });

    it('✅ handles large arrays efficiently', () => {
      console.log('  🔍 Testing large array (1024 samples)');
      const largeArray = new Float32Array(1024).fill(0.5);
      const result = calculateRms(largeArray);
      expect(result).toBeCloseTo(HALF_AMPLITUDE);
    });
  });

  describe('getSupportedMimeType', () => {
    it('✅ returns preferred type if supported', () => {
      console.log('  🔍 Testing preferred MIME type');
      const result = getSupportedMimeType('audio/webm', ['audio/mp4']);
      expect(result).toBe('audio/webm'); // Our mock supports webm
    });

    it('✅ falls back to supported type', () => {
      console.log('  🔍 Testing fallback MIME type');
      const result = getSupportedMimeType('audio/unsupported', ['audio/webm', 'audio/mp4']);
      expect(result).toBe('audio/webm'); // First supported fallback
    });

    it('✅ returns empty string if none supported', () => {
      console.log('  🔍 Testing unsupported MIME types');
      // Mock MediaRecorder to reject all types
      const originalIsTypeSupported = MediaRecorder.isTypeSupported;
      MediaRecorder.isTypeSupported = vi.fn(() => false);

      const result = getSupportedMimeType('audio/unsupported', ['audio/also-unsupported']);
      expect(result).toBe('');

      // Restore original
      MediaRecorder.isTypeSupported = originalIsTypeSupported;
    });
  });

  describe('checkAudioSupport', () => {
    it('✅ detects all required APIs', () => {
      console.log('  🔍 Testing API support detection');
      const support = checkAudioSupport();

      expect(support.mediaDevices).toBe(true);
      expect(support.audioContext).toBe(true);
      expect(support.mediaRecorder).toBe(true);
    });

    it('✅ returns consistent structure', () => {
      console.log('  🔍 Testing support object structure');
      const support = checkAudioSupport();

      expect(support).toHaveProperty('mediaDevices');
      expect(support).toHaveProperty('audioContext');
      expect(support).toHaveProperty('mediaRecorder');
    });
  });
});

console.log('✅ Audio-utils tests loaded');
