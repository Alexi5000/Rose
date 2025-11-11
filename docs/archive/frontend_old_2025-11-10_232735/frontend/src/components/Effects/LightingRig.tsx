import { useRef } from 'react';
import { DirectionalLight } from 'three';
import { useFrame } from '@react-three/fiber';
import { LIGHTING } from '../../config/designSystem';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';

interface LightingRigProps {
  voiceState?: 'idle' | 'listening' | 'processing' | 'speaking';
  audioAmplitude?: number;
}

/**
 * Comprehensive lighting rig for the ice cave scene
 * Provides ambient, key, rim, and fill lights with dynamic adjustments
 * Supports shadow casting and audio-reactive intensity changes
 * 
 * Task 22.1: Enhanced with refined lighting configuration for better realism
 */
export const LightingRig = ({ voiceState = 'idle', audioAmplitude = 0 }: LightingRigProps) => {
  const keyLightRef = useRef<DirectionalLight>(null);
  const rimLightRef = useRef<DirectionalLight>(null);
  const fillLightRef = useRef<any>(null);
  
  const { quality } = useResponsiveScene();
  const shadowsEnabled = quality.shadows;

  // 💡 Use design system lighting intensities (Uncle Bob approved - no magic numbers!)
  const baseIntensities = {
    ambient: LIGHTING.AMBIENT_INTENSITY,
    key: LIGHTING.KEY_LIGHT_INTENSITY,
    rim: LIGHTING.AURORA_LIGHT_INTENSITY,
    fill: LIGHTING.FILL_LIGHT_INTENSITY,
  };

  // Dynamic lighting adjustments based on voice state
  useFrame(() => {
    if (!keyLightRef.current || !rimLightRef.current || !fillLightRef.current) return;

    // Calculate intensity multipliers based on voice state
    let intensityMultiplier = 1.0;
    let warmthBoost = 0;

    switch (voiceState) {
      case 'listening':
        // Subtle increase in cool lighting when listening
        intensityMultiplier = 1.1;
        rimLightRef.current.intensity = baseIntensities.rim * 1.2;
        break;
      case 'speaking':
        // Enhance warm lighting when Rose speaks
        intensityMultiplier = 1.15;
        warmthBoost = 0.2;
        // Pulse with audio amplitude
        const pulse = 1 + audioAmplitude * 0.15;
        keyLightRef.current.intensity = baseIntensities.key * intensityMultiplier * pulse;
        fillLightRef.current.intensity = baseIntensities.fill * (1 + warmthBoost) * pulse;
        break;
      case 'processing':
        // Maintain calm lighting during processing
        intensityMultiplier = 1.05;
        break;
      default:
        // Idle state - base lighting
        keyLightRef.current.intensity = baseIntensities.key;
        rimLightRef.current.intensity = baseIntensities.rim;
        fillLightRef.current.intensity = baseIntensities.fill;
        return;
    }

    // Apply smooth transitions to avoid jarring changes
    if (voiceState !== 'speaking') {
      keyLightRef.current.intensity = baseIntensities.key * intensityMultiplier;
      fillLightRef.current.intensity = baseIntensities.fill * (1 + warmthBoost);
    }
  });

  return (
    <>
      {/* 🌙 Ambient light - soft blue for overall illumination */}
      <ambientLight
        color={LIGHTING.AMBIENT_COLOR}
        intensity={baseIntensities.ambient}
      />

      {/* ☀️ Key light - moonlight/horizon light (main light source) */}
      <directionalLight
        ref={keyLightRef}
        position={[5, 10, 5]}
        color={LIGHTING.KEY_LIGHT_COLOR}
        intensity={baseIntensities.key}
        castShadow={shadowsEnabled}
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-bias={-0.0001}
        shadow-normalBias={0.02}
        shadow-radius={4}
      />

      {/* 🌌 Rim light - aurora light from above (creates depth and separation) */}
      <directionalLight
        ref={rimLightRef}
        position={[0, 15, -10]}
        color={LIGHTING.AURORA_LIGHT_COLOR}
        intensity={baseIntensities.rim}
      />

      {/* 💡 Fill light - soft cyan from left (reduces harsh shadows) */}
      <pointLight
        ref={fillLightRef}
        position={[-8, 5, 3]}
        color={LIGHTING.FILL_LIGHT_COLOR}
        intensity={baseIntensities.fill}
        distance={30}
        decay={2}
      />
    </>
  );
};
