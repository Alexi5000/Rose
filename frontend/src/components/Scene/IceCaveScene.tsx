import { Canvas } from '@react-three/fiber';
import { Suspense } from 'react';
import { PerspectiveCamera } from '@react-three/drei';
import { IceCaveEnvironment } from './IceCaveEnvironment';
import { RoseAvatar } from './RoseAvatar';
import { WaterSurface } from './WaterSurface';
import { Igloo } from './Igloo';
import { OceanHorizon } from './OceanHorizon';
import { AuroraEffect } from './AuroraEffect';
import { LightingRig } from '../Effects/LightingRig';
import { ParticleSystem } from '../Effects/ParticleSystem';
import { PostProcessing } from '../Effects/PostProcessing';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';
import { useSceneAnimations } from '../../hooks/useSceneAnimations';
import { usePerformanceMonitor } from '../../hooks/usePerformanceMonitor';

interface IceCaveSceneProps {
  audioAmplitude?: number; // Audio amplitude from analyzer (0-1)
  voiceState?: 'idle' | 'listening' | 'processing' | 'speaking';
  enableEntryAnimation?: boolean; // Enable/disable entry animation
  reducedMotion?: boolean; // Reduced motion accessibility setting
}

/**
 * Main 3D scene container using React Three Fiber
 * Orchestrates all 3D elements of the ice cave sanctuary with entry animations
 */
/**
 * Scene Content Component
 * Separated to allow performance monitoring inside Canvas context
 */
const SceneContent = ({
  audioAmplitude,
  voiceState,
  enableEntryAnimation,
  reducedMotion,
  cameraConfig,
  isMobile,
}: IceCaveSceneProps & {
  cameraConfig: any;
  isMobile: boolean;
}) => {
  // Performance monitoring - target 60fps on desktop, 30fps on mobile
  const { qualityLevel, isPerformanceGood } = usePerformanceMonitor({
    targetFPS: isMobile ? 30 : 60,
    enableAdaptiveQuality: true,
    logInterval: 5000, // Log every 5 seconds
    onPerformanceChange: (metrics) => {
      if (!isPerformanceGood) {
        console.warn('Performance degraded:', metrics);
      }
    },
  });
  
  // Entry animations using GSAP timeline
  const {
    cameraZ,
    roseScale,
    waterRippleStrength,
    auroraIntensity,
    isAnimating,
  } = useSceneAnimations({
    enabled: enableEntryAnimation,
    duration: 3,
    onComplete: () => {
      console.log('Entry animation complete');
    },
  });

  // Use animated camera Z position during entry animation, then use responsive config
  const finalCameraZ = isAnimating ? cameraZ : cameraConfig.position[2];

  return (
    <>
      {/* Animated camera with entry zoom and responsive positioning */}
      <PerspectiveCamera
        makeDefault
        position={[cameraConfig.position[0], cameraConfig.position[1], finalCameraZ]}
        fov={cameraConfig.fov}
        near={0.1}
        far={1000}
      />

      <Suspense fallback={null}>
        {/* Dynamic lighting rig with audio-reactive adjustments */}
        <LightingRig voiceState={voiceState} audioAmplitude={audioAmplitude} />
        
        {/* Scene elements - pass audio amplitude and animation values for reactive effects */}
        <IceCaveEnvironment />
        <RoseAvatar 
          audioAmplitude={audioAmplitude} 
          animationScale={roseScale}
          reducedMotion={reducedMotion}
        />
        <WaterSurface 
          audioAmplitude={audioAmplitude} 
          rosePosition={[0, 0]}
          rippleStrength={waterRippleStrength}
        />
        <Igloo audioAmplitude={audioAmplitude} />
        <OceanHorizon />
        <AuroraEffect 
          audioAmplitude={audioAmplitude}
          baseIntensity={auroraIntensity}
          reducedMotion={reducedMotion}
        />
        <ParticleSystem reducedMotion={reducedMotion} />
        
        {/* Post-processing effects - disable if performance is poor */}
        <PostProcessing enabled={!reducedMotion && qualityLevel !== 'low'} />
      </Suspense>
    </>
  );
};

export const IceCaveScene = ({ 
  audioAmplitude = 0, 
  voiceState = 'idle',
  enableEntryAnimation = true,
  reducedMotion = false
}: IceCaveSceneProps) => {
  const { cameraConfig, isMobile } = useResponsiveScene();
  return (
    <Canvas
      gl={{
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
      }}
      dpr={isMobile ? [1, 1.5] : [1, 2]} // Lower DPR on mobile for better performance
      shadows
      style={{ touchAction: 'none' }} // Prevent default touch behaviors for better interaction
      frameloop="always" // Ensure continuous rendering for performance monitoring
    >
      <SceneContent
        audioAmplitude={audioAmplitude}
        voiceState={voiceState}
        enableEntryAnimation={enableEntryAnimation}
        reducedMotion={reducedMotion}
        cameraConfig={cameraConfig}
        isMobile={isMobile}
      />
    </Canvas>
  );
};
