import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { refinedMaterialColors, refinedLightingConfig } from '../../config/refinedColors';
import { refinedAmbientAnimations, refinedAudioReactiveAnimations } from '../../config/refinedAnimations';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface IglooProps {
  audioAmplitude?: number; // Audio amplitude from analyzer (0-1)
}

/**
 * Glowing igloo with warm interior light
 * Positioned in the left third of the composition
 * Features emissive material with orange glow and subtle flickering
 * Audio-reactive: pulses with audio during conversation
 * Responsive: Reduced geometry and disabled shadows on mobile
 */
export const Igloo = ({ audioAmplitude = 0 }: IglooProps) => {
  const iglooRef = useRef<THREE.Group>(null);
  const interiorLightRef = useRef<THREE.PointLight>(null);
  const { isMobile } = useResponsiveScene();
  
  // Use refined lighting intensity for enhanced glow
  const baseLightIntensity = refinedLightingConfig.iglooInterior.intensity;
  
  // Subtle flickering animation for candle-like effect - refined timing
  // Enhanced with audio-reactive pulse during conversation
  useFrame((state) => {
    if (interiorLightRef.current) {
      // Combine sine wave with small random variation for natural flicker - refined values
      const time = state.clock.elapsedTime;
      const sineFlicker = Math.sin(time * refinedAmbientAnimations.flickering.sineFrequency) 
        * refinedAmbientAnimations.flickering.sineAmplitude;
      const randomFlicker = (Math.random() - 0.5) * refinedAmbientAnimations.flickering.randomAmplitude;
      const flickerMultiplier = 1 + sineFlicker + randomFlicker;
      
      // Add subtle audio-reactive pulse - refined multiplier
      const audioPulse = 1 + audioAmplitude * (refinedAudioReactiveAnimations.iglooLight.pulseMultiplier - 1);
      
      // Apply flicker and audio pulse to light intensity
      interiorLightRef.current.intensity = baseLightIntensity * flickerMultiplier * audioPulse;
    }
  });
  
  // Position igloo in left third of composition (rule of thirds)
  // Slightly behind and to the left of Rose
  const iglooPosition: [number, number, number] = [-4, 0.8, -2];
  const iglooScale = 0.8;
  
  // Use lower geometry detail on mobile
  const geometrySegments = isMobile ? 8 : 16;
  
  return (
    <group ref={iglooRef} position={iglooPosition} scale={iglooScale}>
      {/* Main igloo dome structure - refined materials for enhanced glow */}
      <mesh castShadow={!isMobile} receiveShadow={!isMobile}>
        {/* Hemisphere for igloo dome */}
        <sphereGeometry args={[1, geometrySegments, geometrySegments, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.igloo.color}
          emissive={refinedMaterialColors.igloo.emissive}
          emissiveIntensity={refinedMaterialColors.igloo.emissiveIntensity}
          roughness={refinedMaterialColors.igloo.roughness}
          metalness={refinedMaterialColors.igloo.metalness}
        />
      </mesh>
      
      {/* Entrance tunnel - refined materials */}
      <mesh position={[0.7, 0.2, 0]} rotation={[0, 0, Math.PI / 2]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.3, 0.3, 0.6, geometrySegments / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.igloo.color}
          emissive={refinedMaterialColors.igloo.emissive}
          emissiveIntensity={refinedMaterialColors.igloo.emissiveIntensity * 0.6}
          roughness={refinedMaterialColors.igloo.roughness}
          metalness={refinedMaterialColors.igloo.metalness}
        />
      </mesh>
      
      {/* Interior point light for warm volumetric glow - enhanced intensity and distance */}
      <pointLight
        ref={interiorLightRef}
        position={[0, 0.4, 0]}
        color={refinedLightingConfig.iglooInterior.color}
        intensity={baseLightIntensity}
        distance={refinedLightingConfig.iglooInterior.distance}
        decay={refinedLightingConfig.iglooInterior.decay}
        castShadow={false}
      />
      
      {/* Additional subtle fill light for the entrance - enhanced */}
      <pointLight
        position={[0.7, 0.2, 0]}
        color={refinedLightingConfig.iglooEntrance.color}
        intensity={refinedLightingConfig.iglooEntrance.intensity}
        distance={refinedLightingConfig.iglooEntrance.distance}
        decay={refinedLightingConfig.iglooEntrance.decay}
        castShadow={false}
      />
    </group>
  );
};
