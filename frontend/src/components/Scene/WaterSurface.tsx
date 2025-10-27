import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import gsap from 'gsap';
import { waterShader } from '../../shaders/waterShader';
import { colorPalette, qualitySettings } from '../../config/constants';
import { refinedAudioReactiveAnimations } from '../../config/refinedAnimations';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface WaterSurfaceProps {
  rippleStrength?: number;
  rosePosition?: [number, number]; // Rose's position in world space for ripple center
  audioAmplitude?: number; // Audio amplitude from analyzer (0-1)
}

/**
 * WaterSurface component with custom shader
 * Features:
 * - High subdivision PlaneGeometry for smooth ripples
 * - Custom shader with concentric ripple animation from Rose's position
 * - Distance-based fade for natural ripple dissipation
 * - Sky gradient reflection
 * - Refraction distortion effects
 * - Audio-reactive ripple strength with smooth GSAP interpolation
 */
export const WaterSurface = ({ 
  rippleStrength = 0.5,
  rosePosition = [0, 0],
  audioAmplitude = 0
}: WaterSurfaceProps) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const { viewport } = useResponsiveScene();
  
  // Ref to store the current interpolated ripple strength
  const interpolatedRippleRef = useRef({ value: rippleStrength });
  
  // Get quality settings based on viewport
  const quality = qualitySettings[viewport as keyof typeof qualitySettings] || qualitySettings.desktop;
  
  // Create shader material with uniforms
  const shaderMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        ...waterShader.uniforms,
        skyColorTop: { value: new THREE.Color(colorPalette.deepBlue) },
        skyColorHorizon: { value: new THREE.Color(colorPalette.warmOrange) },
        waterColorDeep: { value: new THREE.Color(colorPalette.deepBlue) },
        waterColorShallow: { value: new THREE.Color(colorPalette.iceBlue) },
      },
      vertexShader: waterShader.vertexShader,
      fragmentShader: waterShader.fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
    });
  }, []);
  
  // Smooth interpolation for ripple strength changes using GSAP - refined timing
  useEffect(() => {
    // Calculate target ripple strength based on base strength and audio amplitude
    // Audio amplitude boosts the ripple strength for audio-reactive effects - refined multiplier
    const targetStrength = rippleStrength * (1 + audioAmplitude * refinedAudioReactiveAnimations.waterRipples.amplitudeMultiplier);
    
    // Animate to target strength with smooth easing - refined duration
    gsap.to(interpolatedRippleRef.current, {
      value: targetStrength,
      duration: refinedAudioReactiveAnimations.waterRipples.transitionDuration,
      ease: refinedAudioReactiveAnimations.waterRipples.ease,
    });
  }, [rippleStrength, audioAmplitude]);
  
  // Update uniforms on each frame
  useFrame((state) => {
    if (meshRef.current && meshRef.current.material instanceof THREE.ShaderMaterial) {
      const material = meshRef.current.material;
      
      // Update time for animation
      material.uniforms.time.value = state.clock.elapsedTime;
      
      // Update ripple strength with smoothly interpolated value
      material.uniforms.rippleStrength.value = interpolatedRippleRef.current.value;
      
      // Convert Rose's world position to UV coordinates (0-1 range)
      // Assuming water plane is 20x20 units centered at origin
      const uvX = (rosePosition[0] + 10) / 20;
      const uvY = (rosePosition[1] + 10) / 20;
      material.uniforms.rippleCenter.value.set(uvX, uvY);
    }
  });
  
  return (
    <mesh
      ref={meshRef}
      rotation={[-Math.PI / 2, 0, 0]} // Rotate to be horizontal
      position={[0, 0, 0]}
      receiveShadow
    >
      <planeGeometry 
        args={[
          20, // width
          20, // height
          quality.waterSubdivision, // width segments for smooth ripples
          quality.waterSubdivision  // height segments
        ]} 
      />
      <primitive object={shaderMaterial} attach="material" />
    </mesh>
  );
};
