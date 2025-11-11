import { describe, expect, it } from 'vitest';
import { calculateRms } from '../utils/audioAnalysis';

describe('calculateRms', () => {
  it('returns zero for empty input', () => {
    const result = calculateRms(new Float32Array());
    expect(result).toBe(0);
  });

  it('returns zero for silent signal', () => {
    const result = calculateRms(new Float32Array([0, 0, 0, 0]));
    expect(result).toBe(0);
  });

  it('computes rms for constant signal', () => {
    const result = calculateRms(new Float32Array([0.5, 0.5, 0.5, 0.5]));
    expect(result).toBeCloseTo(0.5);
  });

  it('computes rms for mixed signal', () => {
    const result = calculateRms(new Float32Array([0.25, -0.25, 0.75, -0.75]));
    expect(result).toBeCloseTo(0.5590169943749475);
  });
});
