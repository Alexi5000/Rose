import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { COLORS, LIGHTING, SCENE_LAYOUT, MATERIALS } from '../../config/designSystem';
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

  // 💡 Use design system lighting intensity (Uncle Bob approved!)
  const baseLightIntensity = LIGHTING.IGLOO_LIGHT_INTENSITY;

  // 🔥 Flickering animation constants (no magic numbers!)
  const FLICKER_SINE_FREQUENCY = 2.0;
  const FLICKER_SINE_AMPLITUDE = 0.05;
  const FLICKER_RANDOM_AMPLITUDE = 0.03;
  const AUDIO_PULSE_MULTIPLIER = 0.3;

  // Subtle flickering animation for candle-like effect
  // Enhanced with audio-reactive pulse during conversation
  useFrame((state) => {
    if (interiorLightRef.current) {
      // 🔥 Combine sine wave with small random variation for natural flicker
      const time = state.clock.elapsedTime;
      const sineFlicker = Math.sin(time * FLICKER_SINE_FREQUENCY) * FLICKER_SINE_AMPLITUDE;
      const randomFlicker = (Math.random() - 0.5) * FLICKER_RANDOM_AMPLITUDE;
      const flickerMultiplier = 1 + sineFlicker + randomFlicker;

      // 🎵 Add subtle audio-reactive pulse
      const audioPulse = 1 + audioAmplitude * AUDIO_PULSE_MULTIPLIER;

      // Apply flicker and audio pulse to light intensity
      interiorLightRef.current.intensity = baseLightIntensity * flickerMultiplier * audioPulse;
    }
  });

  // 📍 Position igloo in left third of composition (rule of thirds from design system)
  const iglooPosition: [number, number, number] = [
    SCENE_LAYOUT.IGLOO_POSITION_X,
    SCENE_LAYOUT.IGLOO_POSITION_Y,
    SCENE_LAYOUT.IGLOO_POSITION_Z,
  ];
  const iglooScale = SCENE_LAYOUT.IGLOO_SCALE;
  
  // Use lower geometry detail on mobile
  const geometrySegments = isMobile ? 8 : 16;
  
  return (
    <group ref={iglooRef} position={iglooPosition} scale={iglooScale}>
      {/* 🏠 Main igloo dome structure with warm glow */}
      <mesh castShadow={!isMobile} receiveShadow={!isMobile}>
        {/* Hemisphere for igloo dome */}
        <sphereGeometry args={[1, geometrySegments, geometrySegments, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial
          color={COLORS.IGLOO_STRUCTURE}
          emissive={COLORS.IGLOO_GLOW_CORE}
          emissiveIntensity={MATERIALS.IGLOO_EMISSIVE_INTENSITY}
          roughness={MATERIALS.IGLOO_ROUGHNESS}
          metalness={MATERIALS.IGLOO_METALNESS}
        />
      </mesh>

      {/* 🚪 Entrance tunnel with softer glow */}
      <mesh position={[0.7, 0.2, 0]} rotation={[0, 0, Math.PI / 2]} castShadow={!isMobile}>
        <cylinderGeometry args={[0.3, 0.3, 0.6, geometrySegments / 2]} />
        <meshStandardMaterial
          color={COLORS.IGLOO_STRUCTURE}
          emissive={COLORS.IGLOO_GLOW_OUTER}
          emissiveIntensity={MATERIALS.IGLOO_EMISSIVE_INTENSITY * 0.6}
          roughness={MATERIALS.IGLOO_ROUGHNESS}
          metalness={MATERIALS.IGLOO_METALNESS}
        />
      </mesh>

      {/* 🔥 Interior point light for warm volumetric glow */}
      <pointLight
        ref={interiorLightRef}
        position={[0, 0.4, 0]}
        color={LIGHTING.IGLOO_LIGHT_COLOR}
        intensity={baseLightIntensity}
        distance={LIGHTING.IGLOO_LIGHT_DISTANCE}
        decay={LIGHTING.IGLOO_LIGHT_DECAY}
        castShadow={false}
      />

      {/* 💡 Additional subtle fill light for the entrance */}
      <pointLight
        position={[0.7, 0.2, 0]}
        color={COLORS.IGLOO_GLOW_MID}
        intensity={1.0}
        distance={5}
        decay={2}
        castShadow={false}
      />
    </group>
  );
};
