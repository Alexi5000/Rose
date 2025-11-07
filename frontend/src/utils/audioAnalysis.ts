export const calculateRms = (samples: Float32Array): number => {
  if (samples.length === 0) {
    return 0;
  }

  let sumSquares = 0;
  for (let index = 0; index < samples.length; index += 1) {
    const sample = samples[index];
    sumSquares += sample * sample;
  }

  return Math.sqrt(sumSquares / samples.length);
};
