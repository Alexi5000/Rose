import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Group, Mesh } from 'three';
import { refinedMaterialColors } from '../../config/refinedColors';
import { refinedAmbientAnimations, refinedAudioReactiveAnimations } from '../../config/refinedAnimations';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface RoseAvatarProps {
  audioAmplitude?: number;
  animationScale?: number; // Scale for entry animation (0-1)
  reducedMotion?: boolean; // Reduced motion accessibility setting
}

/**
 * Rose avatar in meditation pose - silhouette figure centered on water surface
 * Features:
 * - Simple 3D figure in meditation pose
 * - Silhouette shader with soft edges
 * - Subtle glow effect
 * - Ambient breathing and floating animations
 * - Audio-reactive glow when speaking
 * - Mobile optimizations: simpler geometry, disabled shadows
 */
export const RoseAvatar = ({ audioAmplitude = 0, animationScale = 1, reducedMotion = false }: RoseAvatarProps) => {
  const groupRef = useRef<Group>(null);
  const roseRef = useRef<Mesh>(null);
  const baseY = 0.5; // Base Y position
  
  const { isMobile } = useResponsiveScene();
  
  // Reduced motion support - animations are simplified when enabled
  const animationMultiplier = reducedMotion ? 0.3 : 1.0;
  
  // Use lower geometry detail on mobile
  const geometrySegments = isMobile ? 8 : 16;

  // Ambient animations: breathing, floating, and gentle sway - refined timing
  // Audio-reactive: enhanced scale pulse and glow when speaking - refined response
  // Entry animation: scale from 0 to 1
  useFrame((state) => {
    if (!groupRef.current) return;

    const time = state.clock.elapsedTime;

    // Breathing motion - refined frequency and amplitude
    // Enhanced with audio amplitude for pulse effect when speaking
    // Combined with entry animation scale
    // Reduced when reducedMotion is enabled
    const breathingScale = 1 + Math.sin(time * refinedAmbientAnimations.breathing.frequency * Math.PI * 2) 
      * refinedAmbientAnimations.breathing.amplitude * animationMultiplier;
    
    // Refined audio pulse with better range
    const audioPulse = audioAmplitude * refinedAudioReactiveAnimations.roseScale.maxPulse;
    groupRef.current.scale.y = (breathingScale + audioPulse) * animationScale;
    groupRef.current.scale.x = (1 + audioPulse * 0.5) * animationScale;
    groupRef.current.scale.z = (1 + audioPulse * 0.5) * animationScale;

    // Gentle floating - refined frequency and amplitude
    const floatingOffset = Math.sin(time * refinedAmbientAnimations.floating.frequency * Math.PI * 2) 
      * refinedAmbientAnimations.floating.amplitude * animationMultiplier;
    groupRef.current.position.y = baseY + floatingOffset;

    // Subtle rotation sway - refined frequency and amplitude
    const swayRotation = Math.sin(time * refinedAmbientAnimations.sway.frequency * Math.PI * 2) 
      * refinedAmbientAnimations.sway.amplitude * animationMultiplier;
    groupRef.current.rotation.z = swayRotation;

    // Update emissive intensity based on audio amplitude - refined boost
    // Increase glow when Rose speaks
    const targetEmissiveIntensity = refinedAudioReactiveAnimations.roseGlow.baseIntensity 
      + audioAmplitude * refinedAudioReactiveAnimations.roseGlow.maxBoost;
    
    // Update all mesh materials in the group
    groupRef.current.traverse((child) => {
      if (child instanceof Mesh && child.material) {
        const material = child.material as any;
        if (material.emissiveIntensity !== undefined) {
          material.emissiveIntensity = targetEmissiveIntensity;
        }
      }
    });
  });

  return (
    <group ref={groupRef} position={[0, baseY, 0]}>
      {/* Main body - elongated sphere for torso - refined materials */}
      <mesh ref={roseRef} position={[0, 0, 0]} castShadow={!isMobile}>
        <sphereGeometry args={[0.3, geometrySegments, geometrySegments, 0, Math.PI * 2, 0, Math.PI * 0.6]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      {/* Head - refined materials */}
      <mesh position={[0, 0.4, 0]} castShadow={!isMobile}>
        <sphereGeometry args={[0.15, geometrySegments, geometrySegments]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      {/* Legs in meditation pose - crossed - refined materials */}
      <mesh position={[0.15, -0.3, 0.1]} rotation={[0, 0, -0.3]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.08, 0.08, 0.4, geometrySegments / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      <mesh position={[-0.15, -0.3, 0.1]} rotation={[0, 0, 0.3]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.08, 0.08, 0.4, geometrySegments / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      {/* Arms in meditation pose - resting on legs - refined materials */}
      <mesh position={[0.25, -0.05, 0.15]} rotation={[0.5, 0, 0.8]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.06, 0.06, 0.35, geometrySegments / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      <mesh position={[-0.25, -0.05, 0.15]} rotation={[0.5, 0, -0.8]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.06, 0.06, 0.35, geometrySegments / 2]} />
        <meshStandardMaterial
          color={refinedMaterialColors.rose.color}
          emissive={refinedMaterialColors.rose.emissive}
          emissiveIntensity={refinedMaterialColors.rose.emissiveIntensity}
          roughness={refinedMaterialColors.rose.roughness}
          metalness={refinedMaterialColors.rose.metalness}
        />
      </mesh>

      {/* Subtle glow sphere around Rose - enhanced opacity range */}
      <mesh position={[0, 0, 0]}>
        <sphereGeometry args={[0.6, geometrySegments, geometrySegments]} />
        <meshBasicMaterial
          color={refinedMaterialColors.rose.emissive}
          transparent
          opacity={0.06 + audioAmplitude * 0.12}
        />
      </mesh>
    </group>
  );
};
