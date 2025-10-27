import { useRef } from 'react';
import { DirectionalLight } from 'three';
import { useFrame } from '@react-three/fiber';
import { refinedLightingConfig } from '../../config/refinedColors';
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

  // Use refined lighting intensities for enhanced atmosphere
  const baseIntensities = {
    ambient: refinedLightingConfig.ambient.intensity,
    key: refinedLightingConfig.key.intensity,
    rim: refinedLightingConfig.rim.intensity,
    fill: refinedLightingConfig.fill.intensity,
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
      {/* Ambient light - soft blue for overall illumination (refined intensity) */}
      <ambientLight 
        color={refinedLightingConfig.ambient.color} 
        intensity={baseIntensities.ambient} 
      />

      {/* Key light - warm light from horizon (main light source, refined position and intensity) */}
      <directionalLight
        ref={keyLightRef}
        position={refinedLightingConfig.key.position}
        color={refinedLightingConfig.key.color}
        intensity={baseIntensities.key}
        castShadow={shadowsEnabled && refinedLightingConfig.key.castShadow}
        shadow-mapSize-width={refinedLightingConfig.key.shadowConfig.mapSize}
        shadow-mapSize-height={refinedLightingConfig.key.shadowConfig.mapSize}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-bias={refinedLightingConfig.key.shadowConfig.bias}
        shadow-normalBias={refinedLightingConfig.key.shadowConfig.normalBias}
        shadow-radius={refinedLightingConfig.key.shadowConfig.radius}
      />

      {/* Rim light - cool blue from above (creates depth and separation, enhanced color) */}
      <directionalLight
        ref={rimLightRef}
        position={refinedLightingConfig.rim.position}
        color={refinedLightingConfig.rim.color}
        intensity={baseIntensities.rim}
      />

      {/* Fill light - soft from left (reduces harsh shadows, enhanced coverage) */}
      <pointLight
        ref={fillLightRef}
        position={refinedLightingConfig.fill.position}
        color={refinedLightingConfig.fill.color}
        intensity={baseIntensities.fill}
        distance={refinedLightingConfig.fill.distance}
        decay={refinedLightingConfig.fill.decay}
      />
    </>
  );
};
