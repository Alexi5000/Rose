import { useState, useEffect } from 'react';
import { breakpoints, cameraSettings, qualitySettings } from '../config/constants';
import { getTextureQualityPreset, TextureQualityPreset } from '../utils/textureOptimization';

export type ViewportType = 'mobile' | 'tablet' | 'desktop' | 'ultrawide';

/**
 * Hook for viewport-based scene adjustments
 * Detects screen size and provides appropriate camera and quality settings
 */
export const useResponsiveScene = () => {
  const [viewport, setViewport] = useState<ViewportType>('desktop');
  const [aspectRatio, setAspectRatio] = useState<number>(16 / 9);

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      
      // Calculate aspect ratio for scene composition adjustments
      setAspectRatio(width / height);
      
      // Determine viewport type based on width
      if (width < breakpoints.mobile) {
        setViewport('mobile');
      } else if (width < breakpoints.tablet) {
        setViewport('tablet');
      } else if (width < breakpoints.desktop) {
        setViewport('desktop');
      } else {
        setViewport('ultrawide');
      }
    };

    // Initial check
    handleResize();

    // Listen for resize events with debouncing for performance
    let timeoutId: number;
    const debouncedResize = () => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(handleResize, 100);
    };
    
    window.addEventListener('resize', debouncedResize);
    
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', debouncedResize);
    };
  }, []);

  // Get camera configuration for current viewport
  const cameraConfig = cameraSettings[viewport];
  
  // Get quality settings for current viewport
  // Use desktop settings for ultrawide
  const quality = viewport === 'ultrawide' 
    ? qualitySettings.desktop 
    : qualitySettings[viewport];

  // Get texture quality preset based on device
  const textureQuality: TextureQualityPreset = getTextureQualityPreset(
    viewport === 'mobile',
    viewport === 'tablet'
  );

  return {
    viewport,
    cameraConfig,
    quality,
    aspectRatio,
    isMobile: viewport === 'mobile',
    isTablet: viewport === 'tablet',
    isDesktop: viewport === 'desktop' || viewport === 'ultrawide',
    isPortrait: aspectRatio < 1,
    isLandscape: aspectRatio >= 1,
    // Expose individual quality settings for convenience
    enablePostProcessing: quality.postProcessing,
    enableShadows: quality.shadows,
    particleCount: quality.particleCount,
    waterSubdivision: quality.waterSubdivision,
    // Texture optimization settings
    textureQuality,
  };
};
