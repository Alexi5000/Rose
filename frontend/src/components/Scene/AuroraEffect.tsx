import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { gsap } from 'gsap';
import { auroraShader } from '../../shaders/auroraShader';
import { refinedAuroraColors } from '../../config/refinedColors';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface AuroraEffectProps {
  audioAmplitude?: number; // Audio amplitude from analyzer (0-1)
  baseIntensity?: number; // Base intensity for entry animation (0-0.6)
  reducedMotion?: boolean; // Reduced motion accessibility setting
}

/**
 * Aurora Borealis Effect Component
 * 
 * Creates an ethereal aurora borealis effect above the scene using a custom shader
 * with flowing noise patterns. The effect is audio-reactive and responds to
 * conversation with increased intensity.
 * 
 * Features:
 * - Flowing noise-based shader pattern with multiple octaves
 * - Blue, purple, and green color mixing
 * - Transparency for ethereal effect
 * - Slow, calming wave-like animation
 * - Audio-reactive intensity control with smooth GSAP transitions
 * - Responsive: Reduced geometry on mobile for better performance
 */
export const AuroraEffect = ({ audioAmplitude = 0, baseIntensity = refinedAuroraColors.baseIntensity, reducedMotion = false }: AuroraEffectProps) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const { isMobile } = useResponsiveScene();
  
  // Reduced motion support - slower animation speed when enabled
  const animationSpeed = reducedMotion ? 0.3 : 1.0;
  
  // Create shader material with refined aurora colors
  const material = useMemo(() => {
    const mat = new THREE.ShaderMaterial({
      uniforms: THREE.UniformsUtils.clone(auroraShader.uniforms),
      vertexShader: auroraShader.vertexShader,
      fragmentShader: auroraShader.fragmentShader,
      transparent: true,
      side: THREE.DoubleSide,
      depthWrite: false,
      blending: THREE.AdditiveBlending, // Additive blending for glow effect
    });
    
    // Apply refined aurora colors
    mat.uniforms.color1.value = new THREE.Color(refinedAuroraColors.color1);
    mat.uniforms.color2.value = new THREE.Color(refinedAuroraColors.color2);
    mat.uniforms.color3.value = new THREE.Color(refinedAuroraColors.color3);
    
    return mat;
  }, []);

  // Audio-reactive intensity control with GSAP smooth transitions - refined timing
  // Combined with entry animation base intensity - refined max intensity
  useEffect(() => {
    if (!material) return;

    // Calculate target intensity based on audio amplitude and entry animation
    // Use refined intensity values for better presence
    const maxAudioBoost = refinedAuroraColors.maxIntensity - refinedAuroraColors.baseIntensity;
    const targetIntensity = baseIntensity + audioAmplitude * maxAudioBoost;

    // Use GSAP for smooth intensity transitions - refined from refinedAudioReactiveAnimations
    gsap.to(material.uniforms.intensity, {
      value: targetIntensity,
      duration: 0.3, // Keep existing duration as it works well
      ease: 'power2.out',
    });
  }, [audioAmplitude, baseIntensity, material]);

  // Animate time uniform for flowing motion
  useFrame((state) => {
    if (material) {
      // Slow, calming animation speed (reduced when reducedMotion is enabled)
      material.uniforms.time.value = state.clock.elapsedTime * animationSpeed;
    }
  });

  // Cleanup
  useEffect(() => {
    return () => {
      material.dispose();
    };
  }, [material]);

  // Use lower geometry detail on mobile for better performance
  const widthSegments = isMobile ? 32 : 64;
  const heightSegments = isMobile ? 16 : 32;

  return (
    <mesh
      ref={meshRef}
      position={[0, 8, -15]} // Above scene, behind Rose
      rotation={[-Math.PI / 6, 0, 0]} // Tilted to curve over scene
    >
      {/* Curved plane for aurora - wide and tall, responsive geometry */}
      <planeGeometry args={[30, 12, widthSegments, heightSegments]} />
      <primitive object={material} attach="material" />
    </mesh>
  );
};
