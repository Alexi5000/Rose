/**
 * Refined Color Palette and Lighting Configuration
 * Task 22.1: Fine-tune colors and lighting
 * 
 * This file contains refined color values and lighting parameters
 * to exactly match the reference design and enhance visual realism.
 */

// Refined color palette with adjusted values for better visual harmony
export const refinedColorPalette = {
  // Ice Cave & Sky - Enhanced depth and richness
  deepBlue: '#0a1e3d',        // Deep night blue (unchanged - perfect)
  skyBlue: '#1e4d8b',         // Rich sky blue (unchanged - perfect)
  iceBlue: '#4d9fff',         // Bright ice blue (unchanged - perfect)
  
  // Warm Accents - Enhanced warmth and glow
  warmOrange: '#ff8c42',      // Warm sunset orange (unchanged - perfect)
  warmPink: '#ff6b9d',        // Soft pink horizon (unchanged - perfect)
  candleGlow: '#ff7a4d',      // Slightly brighter candle glow (was #ff6b42)
  
  // Aurora - Enhanced ethereal quality
  auroraBlue: '#5da8ff',      // Slightly brighter aurora blue (was #4d9fff)
  auroraPurple: '#a855ff',    // More vibrant purple (was #9d4dff)
  auroraGreen: '#52ffb8',     // Brighter green accent (was #4dffaa)
  
  // UI - Enhanced contrast
  white: '#ffffff',
  whiteTransparent: 'rgba(255, 255, 255, 0.12)',  // Slightly more visible (was 0.1)
  whiteBorder: 'rgba(255, 255, 255, 0.35)',       // Slightly more visible (was 0.3)
  
  // Additional refined colors for materials
  roseSilhouette: '#16182a',  // Slightly lighter for better depth (was #1a1a2e)
  waterDeep: '#0d2847',       // Deep water color for better gradient
  iceGlow: '#6db8ff',         // Brighter ice glow for rim lighting
} as const;

// Refined material configurations with enhanced realism
export const refinedMaterialColors = {
  // Ice materials - Enhanced translucency and glow
  ice: {
    color: refinedColorPalette.iceBlue,
    emissive: refinedColorPalette.deepBlue,
    emissiveIntensity: 0.25,      // Increased from 0.2 for more glow
    metalness: 0.05,              // Reduced from 0.1 for more natural ice
    roughness: 0.25,              // Reduced from 0.3 for more reflective ice
    transmission: 0.92,           // Increased from 0.9 for more translucency
    thickness: 0.6,               // Increased from 0.5 for better depth
    ior: 1.31,                    // Index of refraction for ice
  },
  
  // Igloo glow - Enhanced warmth and intensity
  igloo: {
    color: refinedColorPalette.warmOrange,
    emissive: refinedColorPalette.candleGlow,
    emissiveIntensity: 0.9,       // Increased from 0.8 for stronger glow
    roughness: 0.75,              // Increased from 0.7 for more diffuse glow
    metalness: 0,
  },
  
  // Rose silhouette - Enhanced depth and subtle glow
  rose: {
    color: refinedColorPalette.roseSilhouette,
    emissive: refinedColorPalette.iceBlue,
    emissiveIntensity: 0.15,      // Increased from 0.1 for more presence
    roughness: 0.95,              // Increased from 0.9 for more matte
    metalness: 0.05,              // Reduced from 0.1 for less reflection
  },
  
  // Water surface - Enhanced reflection and depth
  water: {
    color: refinedColorPalette.waterDeep,
    emissive: refinedColorPalette.deepBlue,
    emissiveIntensity: 0.05,      // Subtle self-illumination
    metalness: 0.95,              // Increased from 0.9 for more reflection
    roughness: 0.08,              // Reduced from 0.1 for smoother surface
    ior: 1.33,                    // Index of refraction for water
  },
} as const;

// Refined lighting configuration for enhanced atmosphere
export const refinedLightingConfig = {
  // Ambient light - Soft blue for overall illumination
  ambient: {
    color: refinedColorPalette.iceBlue,
    intensity: 0.35,              // Increased from 0.3 for better visibility
  },
  
  // Key light - Warm light from horizon (main light source)
  key: {
    color: refinedColorPalette.warmOrange,
    intensity: 1.6,               // Increased from 1.5 for stronger presence
    position: [0, 3, -10] as [number, number, number],  // Raised slightly
    castShadow: true,
    shadowConfig: {
      mapSize: 2048,
      bias: -0.0001,
      normalBias: 0.02,
      radius: 4,
    },
  },
  
  // Rim light - Cool blue from above (creates depth and separation)
  rim: {
    color: refinedColorPalette.iceGlow,  // Brighter blue for better rim
    intensity: 0.9,               // Increased from 0.8 for more definition
    position: [0, 10, 5] as [number, number, number],
  },
  
  // Fill light - Soft from left (reduces harsh shadows)
  fill: {
    color: refinedColorPalette.iceGlow,
    intensity: 0.6,               // Increased from 0.5 for better fill
    position: [-5, 3, 2] as [number, number, number],
    distance: 12,                 // Increased from 10 for wider coverage
    decay: 2,
  },
  
  // Igloo interior light - Warm volumetric glow
  iglooInterior: {
    color: refinedColorPalette.warmOrange,
    intensity: 2.2,               // Increased from 2.0 for stronger glow
    distance: 3.5,                // Increased from 3 for wider glow
    decay: 2,
  },
  
  // Igloo entrance light - Subtle warm fill
  iglooEntrance: {
    color: refinedColorPalette.candleGlow,
    intensity: 0.6,               // Increased from 0.5 for better visibility
    distance: 1.8,                // Increased from 1.5 for wider coverage
    decay: 2,
  },
} as const;

// Refined gradient definitions with smoother transitions
export const refinedGradients = {
  // Sky gradient - Enhanced color stops for smoother transition
  sky: {
    colors: [
      { stop: 0.0, color: refinedColorPalette.deepBlue },
      { stop: 0.35, color: refinedColorPalette.skyBlue },    // Earlier transition
      { stop: 0.65, color: refinedColorPalette.warmPink },   // Adjusted for smoother blend
      { stop: 1.0, color: refinedColorPalette.warmOrange },
    ],
  },
  
  // Water reflection gradient - Enhanced depth
  water: {
    colors: [
      { stop: 0.0, color: refinedColorPalette.waterDeep },
      { stop: 0.45, color: refinedColorPalette.iceBlue },    // Adjusted for better reflection
      { stop: 1.0, color: refinedColorPalette.warmOrange },
    ],
  },
} as const;

// Refined post-processing settings for enhanced cinematic look
export const refinedPostProcessing = {
  bloom: {
    intensity: 0.9,               // Increased from 0.8 for more glow
    luminanceThreshold: 0.25,     // Reduced from 0.3 for more bloom sources
    luminanceSmoothing: 0.95,     // Increased from 0.9 for smoother bloom
    radius: 0.85,                 // Increased for wider bloom spread
  },
  
  colorGrading: {
    brightness: 0.08,             // Increased from 0.05 for better visibility
    contrast: 1.15,               // Increased from 1.1 for more punch
    saturation: 1.25,             // Increased from 1.2 for richer colors
    temperature: 0.12,            // Increased from 0.1 for warmer feel
  },
  
  vignette: {
    offset: 0.35,                 // Increased from 0.3 for subtler vignette
    darkness: 0.45,               // Reduced from 0.5 for less aggressive darkening
  },
} as const;

// Refined fog settings for better atmospheric perspective
export const refinedFogConfig = {
  color: refinedColorPalette.warmPink,  // Matches horizon
  near: 25,                       // Reduced from 30 for earlier fog start
  far: 90,                        // Reduced from 100 for more atmospheric depth
} as const;

// Aurora shader color configuration
export const refinedAuroraColors = {
  color1: refinedColorPalette.auroraBlue,
  color2: refinedColorPalette.auroraPurple,
  color3: refinedColorPalette.auroraGreen,
  baseIntensity: 0.65,            // Increased from 0.6 for more presence
  maxIntensity: 1.3,              // Increased from 1.2 for stronger peaks
} as const;
