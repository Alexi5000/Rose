/**
 * Refined Animation Configuration
 * Task 22.2: Refine animations and timing
 * 
 * This file contains refined animation timing, easing functions, and durations
 * to create smoother, more natural animations throughout the experience.
 */

/**
 * Entry Animation Configuration
 * Orchestrates the initial scene reveal sequence
 */
export const refinedEntryAnimation = {
  // Overall duration of entry sequence
  totalDuration: 3.5,           // Increased from 3 for more graceful entry
  
  // Camera zoom animation
  camera: {
    startZ: 15,
    endZ: 8,
    duration: 3.5,              // Matches total duration
    ease: 'power2.inOut',       // Changed from power2.out for smoother deceleration
    delay: 0,
  },
  
  // Rose avatar fade-in and scale
  rose: {
    startScale: 0,
    endScale: 1,
    duration: 2.2,              // Increased from 2 for more graceful appearance
    ease: 'back.out(1.4)',      // Reduced bounce from 1.7 for subtler effect
    delay: 1.0,                 // Start after camera begins moving
  },
  
  // Water ripples starting
  water: {
    startStrength: 0,
    endStrength: 0.5,
    duration: 2.5,              // Increased from 2 for smoother build
    ease: 'power2.out',
    delay: 1.2,                 // Start slightly after Rose
  },
  
  // Aurora fade-in
  aurora: {
    startIntensity: 0,
    endIntensity: 0.65,         // Use refined base intensity
    duration: 3.2,              // Increased from 3 for more gradual reveal
    ease: 'power1.inOut',
    delay: 0.8,                 // Start early for atmospheric build
  },
} as const;

/**
 * Ambient Animation Configuration
 * Subtle, continuous animations for living scene
 */
export const refinedAmbientAnimations = {
  // Rose breathing animation
  breathing: {
    amplitude: 0.02,            // Scale variation
    frequency: 0.5,             // Cycles per second (unchanged - natural breathing rate)
    ease: 'sine.inOut',
  },
  
  // Rose floating animation
  floating: {
    amplitude: 0.05,            // Vertical movement in units
    frequency: 0.3,             // Slower than breathing for gentle float
    ease: 'sine.inOut',
  },
  
  // Rose gentle sway
  sway: {
    amplitude: 0.02,            // Rotation in radians
    frequency: 0.4,             // Slightly faster than floating
    ease: 'sine.inOut',
  },
  
  // Igloo light flickering
  flickering: {
    baseIntensity: 2.2,
    sineAmplitude: 0.1,
    sineFrequency: 3,           // Unchanged - natural candle flicker
    randomAmplitude: 0.05,
  },
  
  // Water ripple base animation
  waterRipples: {
    speed: 2.0,                 // Unchanged - natural water movement
    frequency: 20.0,            // Ripple density
    fadeDistance: 2.0,          // Distance-based fade
  },
  
  // Aurora flowing animation
  auroraFlow: {
    speed: 1.0,                 // Time multiplier (unchanged)
    noiseScale: 2.0,            // Pattern scale
    flowDirection: [0.1, 0.15], // Subtle directional flow
  },
  
  // Particle floating
  particles: {
    minSpeed: 0.008,            // Reduced from 0.01 for slower, more graceful fall
    maxSpeed: 0.018,            // Reduced from 0.02
    driftAmplitude: 0.004,      // Reduced from 0.005 for subtler drift
    resetHeight: 12,
    minHeight: -1,
  },
} as const;

/**
 * Audio-Reactive Animation Configuration
 * Responsive animations triggered by voice interaction
 */
export const refinedAudioReactiveAnimations = {
  // Water ripple response to audio
  waterRipples: {
    amplitudeMultiplier: 1.8,   // Increased from 1.5 for more visible response
    transitionDuration: 0.25,   // Reduced from 0.3 for snappier response
    ease: 'power2.out',
  },
  
  // Rose glow response to audio
  roseGlow: {
    baseIntensity: 0.15,
    maxBoost: 0.6,              // Increased from 0.5 for more dramatic glow
    transitionDuration: 0.25,   // Reduced from 0.3 for snappier response
    ease: 'power2.out',
  },
  
  // Rose scale pulse with audio
  roseScale: {
    basePulse: 0.05,
    maxPulse: 0.08,             // Increased from 0.05 for more visible pulse
    transitionDuration: 0.2,    // Quick response
    ease: 'power2.out',
  },
  
  // Aurora intensity response
  aurora: {
    baseIntensity: 0.65,
    maxBoost: 0.65,             // Total max: 1.3 (matches refined config)
    transitionDuration: 0.3,
    ease: 'power2.out',
  },
  
  // Lighting intensity response
  lighting: {
    keyLightBoost: 0.15,
    fillLightBoost: 0.2,
    transitionDuration: 0.3,
    ease: 'power2.out',
  },
  
  // Igloo light pulse
  iglooLight: {
    pulseMultiplier: 1.15,
    transitionDuration: 0.25,
    ease: 'power2.out',
  },
} as const;

/**
 * UI Animation Configuration
 * Animations for user interface elements
 */
export const refinedUIAnimations = {
  // Hero title fade-in
  heroTitle: {
    duration: 1.8,              // Increased from 1.5 for more elegant entrance
    ease: 'easeOut',
    delay: 0.5,                 // Slight delay after scene starts
    yOffset: -20,
  },
  
  // Voice button states
  voiceButton: {
    // Idle pulsing
    idle: {
      scale: [1, 1.05, 1],
      duration: 2.5,            // Increased from 2 for slower, calmer pulse
      ease: 'easeInOut',
      repeat: Infinity,
    },
    
    // Hover state
    hover: {
      scale: 1.1,
      duration: 0.25,           // Reduced from 0.3 for snappier response
      ease: 'easeOut',
    },
    
    // Tap/press state
    tap: {
      scale: 0.95,
      duration: 0.15,           // Quick press feedback
      ease: 'easeOut',
    },
    
    // Listening state
    listening: {
      scale: 1.12,              // Increased from 1.1 for more emphasis
      glowIntensity: 0.8,
      duration: 0.3,
      ease: 'easeOut',
    },
    
    // Speaking state (pulsing)
    speaking: {
      scale: [1, 1.06, 1],      // Increased from 1.05 for more visible pulse
      duration: 1.2,            // Increased from 1 for slower, calmer pulse
      ease: 'easeInOut',
      repeat: Infinity,
    },
  },
  
  // Loading screen
  loadingScreen: {
    fadeOut: {
      duration: 1.2,            // Increased from 1 for smoother exit
      ease: 'easeInOut',
    },
    
    spinner: {
      duration: 1.5,            // Rotation speed
      ease: 'linear',
      repeat: Infinity,
    },
    
    progressBar: {
      duration: 0.4,            // Increased from 0.3 for smoother updates
      ease: 'easeOut',
    },
  },
  
  // Settings panel
  settingsPanel: {
    slideIn: {
      duration: 0.35,           // Increased from 0.3 for smoother slide
      ease: 'easeOut',
    },
    
    slideOut: {
      duration: 0.3,
      ease: 'easeIn',
    },
  },
  
  // Keyboard help overlay
  keyboardHelp: {
    fadeIn: {
      duration: 0.3,
      ease: 'easeOut',
    },
    
    fadeOut: {
      duration: 0.25,
      ease: 'easeIn',
    },
  },
} as const;

/**
 * Transition Configuration
 * State transitions and interpolation settings
 */
export const refinedTransitions = {
  // Voice state transitions
  voiceState: {
    duration: 0.3,
    ease: 'power2.out',
  },
  
  // Quality level transitions (performance adaptation)
  qualityLevel: {
    duration: 1.0,              // Slow transition to avoid jarring changes
    ease: 'power1.inOut',
  },
  
  // Camera position transitions (responsive)
  camera: {
    duration: 0.8,              // Increased from 0.5 for smoother viewport changes
    ease: 'power2.inOut',
  },
  
  // Material property transitions
  material: {
    duration: 0.5,
    ease: 'power2.out',
  },
} as const;

/**
 * Easing Functions Reference
 * Common easing functions used throughout the application
 */
export const easingFunctions = {
  // Standard easings
  linear: 'none',
  easeIn: 'power2.in',
  easeOut: 'power2.out',
  easeInOut: 'power2.inOut',
  
  // Specialized easings
  smoothStart: 'power1.in',
  smoothEnd: 'power1.out',
  smooth: 'power1.inOut',
  
  // Elastic and bounce
  elastic: 'elastic.out(1, 0.5)',
  bounce: 'bounce.out',
  backOut: 'back.out(1.4)',     // Refined from 1.7
  
  // Sine wave (natural motion)
  sineIn: 'sine.in',
  sineOut: 'sine.out',
  sineInOut: 'sine.inOut',
  
  // Exponential (dramatic)
  expoIn: 'expo.in',
  expoOut: 'expo.out',
  expoInOut: 'expo.inOut',
} as const;

/**
 * Performance-Based Animation Scaling
 * Adjust animation complexity based on device performance
 */
export const performanceScaling = {
  high: {
    animationMultiplier: 1.0,
    particleAnimations: true,
    complexEasing: true,
    audioReactivity: 'full',
  },
  
  medium: {
    animationMultiplier: 1.0,
    particleAnimations: true,
    complexEasing: true,
    audioReactivity: 'full',
  },
  
  low: {
    animationMultiplier: 0.7,   // Reduce animation frequency
    particleAnimations: false,  // Disable particle animations
    complexEasing: false,       // Use linear easing
    audioReactivity: 'reduced', // Simplified audio response
  },
} as const;

/**
 * Reduced Motion Configuration
 * Simplified animations for accessibility
 */
export const reducedMotionConfig = {
  // Disable or simplify these animations
  disableEntryAnimation: false,     // Keep entry but simplify
  entryDurationMultiplier: 0.5,     // Faster entry
  ambientAnimationMultiplier: 0.3,  // Reduce ambient motion
  disableParticles: true,           // Remove particle motion
  disableAuroraFlow: true,          // Static aurora
  simplifyEasing: true,             // Use linear easing
  audioReactivityMultiplier: 0.5,   // Reduce audio response
} as const;
