import { EffectComposer, Bloom, Vignette, BrightnessContrast, HueSaturation } from '@react-three/postprocessing';
import { BlendFunction } from 'postprocessing';
import { refinedPostProcessing } from '../../config/refinedColors';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface PostProcessingProps {
  enabled?: boolean; // Enable/disable post-processing
}

/**
 * Post-processing effects for cinematic visual quality
 * Includes bloom for glowing elements, color grading, and vignette
 * 
 * Task 22.1: Enhanced with refined post-processing settings
 * 
 * Requirements:
 * - 1.5: Smooth fade-in animations and atmospheric effects
 * - 1.4: Warm glowing igloo and lighting
 * - 6.1: Performance optimization with adaptive quality
 * - 9.1-9.3: Color palette and cinematic look
 * - 11.2: Cinematic composition and depth
 */
export const PostProcessing = ({ enabled = true }: PostProcessingProps) => {
  const { enablePostProcessing } = useResponsiveScene();

  // Disable post-processing on low-end devices for performance or if explicitly disabled
  if (!enablePostProcessing || !enabled) {
    return null;
  }

  return (
    <EffectComposer>
      {/* Bloom effect for glowing elements - refined settings for enhanced glow */}
      <Bloom
        intensity={refinedPostProcessing.bloom.intensity}
        luminanceThreshold={refinedPostProcessing.bloom.luminanceThreshold}
        luminanceSmoothing={refinedPostProcessing.bloom.luminanceSmoothing}
        mipmapBlur
        radius={refinedPostProcessing.bloom.radius}
      />

      {/* Brightness and contrast for cinematic look - refined values */}
      <BrightnessContrast
        brightness={refinedPostProcessing.colorGrading.brightness}
        contrast={refinedPostProcessing.colorGrading.contrast - 1} // Adjust for component scale
      />

      {/* Hue and saturation adjustments for color grading - refined saturation */}
      <HueSaturation
        saturation={refinedPostProcessing.colorGrading.saturation - 1} // Adjust for component scale
        hue={0}
        blendFunction={BlendFunction.NORMAL}
      />

      {/* Vignette effect for focus and cinematic framing - refined subtlety */}
      <Vignette
        offset={refinedPostProcessing.vignette.offset}
        darkness={refinedPostProcessing.vignette.darkness}
        eskil={false}
        blendFunction={BlendFunction.NORMAL}
      />
    </EffectComposer>
  );
};
