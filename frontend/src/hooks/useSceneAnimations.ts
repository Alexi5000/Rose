import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { refinedEntryAnimation } from '../config/refinedAnimations';

/**
 * useSceneAnimations Hook
 * 
 * Centralizes GSAP timeline management for scene entry animations
 * Provides animation controls to components and handles cleanup on unmount
 * 
 * Task 22.2: Enhanced with refined animation timing and easing
 * 
 * This hook manages the entry animation sequence:
 * 1. Camera zoom from distance
 * 2. Rose avatar fade in with scale animation
 * 3. Water ripples starting
 * 4. Aurora effect fade in
 * 
 * Requirements: 1.5, 4.4, 4.5
 */

interface UseSceneAnimationsOptions {
  enabled?: boolean;
  duration?: number;
  onComplete?: () => void;
}

export const useSceneAnimations = (options: UseSceneAnimationsOptions = {}) => {
  const { enabled = true, duration = refinedEntryAnimation.totalDuration, onComplete } = options;
  const timelineRef = useRef<gsap.core.Timeline | null>(null);
  const hasPlayedRef = useRef(false);

  // Animation state values that components can read - use refined start values
  const [cameraZ, setCameraZ] = useState(refinedEntryAnimation.camera.startZ);
  const [roseScale, setRoseScale] = useState(refinedEntryAnimation.rose.startScale);
  const [waterRippleStrength, setWaterRippleStrength] = useState(refinedEntryAnimation.water.startStrength);
  const [auroraIntensity, setAuroraIntensity] = useState(refinedEntryAnimation.aurora.startIntensity);

  useEffect(() => {
    // Only play entry animation once
    if (!enabled || hasPlayedRef.current) return;

    // Create GSAP timeline for entry animations with refined timing
    const tl = gsap.timeline({
      defaults: {
        ease: refinedEntryAnimation.camera.ease,
      },
      onComplete: () => {
        if (onComplete) onComplete();
      },
    });

    // 1. Camera zoom from distance - refined easing for smoother deceleration
    tl.to(
      { z: refinedEntryAnimation.camera.startZ },
      {
        z: refinedEntryAnimation.camera.endZ,
        duration: refinedEntryAnimation.camera.duration,
        ease: refinedEntryAnimation.camera.ease,
        onUpdate: function () {
          setCameraZ(this.targets()[0].z);
        },
      },
      refinedEntryAnimation.camera.delay
    );

    // 2. Fade in Rose avatar with scale animation - refined bounce and timing
    tl.to(
      { scale: refinedEntryAnimation.rose.startScale },
      {
        scale: refinedEntryAnimation.rose.endScale,
        duration: refinedEntryAnimation.rose.duration,
        ease: refinedEntryAnimation.rose.ease,
        onUpdate: function () {
          setRoseScale(this.targets()[0].scale);
        },
      },
      refinedEntryAnimation.rose.delay
    );

    // 3. Animate water ripples starting - refined duration for smoother build
    tl.to(
      { strength: refinedEntryAnimation.water.startStrength },
      {
        strength: refinedEntryAnimation.water.endStrength,
        duration: refinedEntryAnimation.water.duration,
        ease: refinedEntryAnimation.water.ease,
        onUpdate: function () {
          setWaterRippleStrength(this.targets()[0].strength);
        },
      },
      refinedEntryAnimation.water.delay
    );

    // 4. Fade in aurora effect - refined intensity and timing
    tl.to(
      { intensity: refinedEntryAnimation.aurora.startIntensity },
      {
        intensity: refinedEntryAnimation.aurora.endIntensity,
        duration: refinedEntryAnimation.aurora.duration,
        ease: refinedEntryAnimation.aurora.ease,
        onUpdate: function () {
          setAuroraIntensity(this.targets()[0].intensity);
        },
      },
      refinedEntryAnimation.aurora.delay
    );

    timelineRef.current = tl;
    hasPlayedRef.current = true;

    // Cleanup function
    return () => {
      if (timelineRef.current) {
        timelineRef.current.kill();
        timelineRef.current = null;
      }
    };
  }, [enabled, duration, onComplete]);

  // Provide controls for the timeline
  const play = () => {
    if (timelineRef.current) {
      timelineRef.current.play();
    }
  };

  const pause = () => {
    if (timelineRef.current) {
      timelineRef.current.pause();
    }
  };

  const restart = () => {
    if (timelineRef.current) {
      hasPlayedRef.current = false;
      timelineRef.current.restart();
    }
  };

  const reverse = () => {
    if (timelineRef.current) {
      timelineRef.current.reverse();
    }
  };

  const skip = () => {
    if (timelineRef.current) {
      timelineRef.current.progress(1);
    }
  };

  return {
    // Animation state values
    cameraZ,
    roseScale,
    waterRippleStrength,
    auroraIntensity,
    
    // Timeline controls
    timeline: timelineRef.current,
    play,
    pause,
    restart,
    reverse,
    skip,
    
    // Status
    isAnimating: timelineRef.current?.isActive() ?? false,
    hasPlayed: hasPlayedRef.current,
  };
};
