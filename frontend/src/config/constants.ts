// Environment variables and configuration constants
// In production (Docker): Frontend served from same origin, so use relative path
// In development (Vite): Proxy handles forwarding to backend on port 8000
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
export const ASSET_CDN_URL = import.meta.env.VITE_ASSET_CDN_URL || '/assets';
export const ENABLE_ANALYTICS = import.meta.env.VITE_ENABLE_ANALYTICS === 'true';
export const ENABLE_DEBUG = import.meta.env.VITE_ENABLE_DEBUG === 'true';

// Performance settings
export const TARGET_FPS = parseInt(import.meta.env.VITE_TARGET_FPS || '60', 10);
export const MOBILE_TARGET_FPS = parseInt(import.meta.env.VITE_MOBILE_TARGET_FPS || '30', 10);

// Color palette from design document
export const colorPalette = {
  // Ice Cave & Sky
  deepBlue: '#0a1e3d',
  skyBlue: '#1e4d8b',
  iceBlue: '#4d9fff',
  
  // Warm Accents
  warmOrange: '#ff8c42',
  warmPink: '#ff6b9d',
  candleGlow: '#ff6b42',
  
  // Aurora
  auroraBlue: '#4d9fff',
  auroraPurple: '#9d4dff',
  auroraGreen: '#4dffaa',
  
  // UI
  white: '#ffffff',
  whiteTransparent: 'rgba(255, 255, 255, 0.1)',
  whiteBorder: 'rgba(255, 255, 255, 0.3)',
} as const;

// Gradient definitions for sky and water
export const gradients = {
  // Sky gradient (vertical) - from deep blue to warm orange/pink
  sky: {
    colors: [
      { stop: 0.0, color: colorPalette.deepBlue },
      { stop: 0.4, color: colorPalette.skyBlue },
      { stop: 0.7, color: colorPalette.warmPink },
      { stop: 1.0, color: colorPalette.warmOrange },
    ],
  },
  
  // Water reflection gradient (inverted sky)
  water: {
    colors: [
      { stop: 0.0, color: colorPalette.deepBlue },
      { stop: 0.5, color: colorPalette.iceBlue },
      { stop: 1.0, color: colorPalette.warmOrange },
    ],
  },
} as const;

// Material color configurations
export const materialColors = {
  // Ice materials
  ice: {
    color: colorPalette.iceBlue,
    emissive: colorPalette.deepBlue,
    emissiveIntensity: 0.2,
    metalness: 0.1,
    roughness: 0.3,
    transmission: 0.9,
    thickness: 0.5,
  },
  
  // Igloo glow
  igloo: {
    color: colorPalette.warmOrange,
    emissive: colorPalette.candleGlow,
    emissiveIntensity: 0.8,
    roughness: 0.7,
  },
  
  // Rose silhouette
  rose: {
    color: '#1a1a2e',
    emissive: colorPalette.iceBlue,
    emissiveIntensity: 0.1,
  },
  
  // Water surface
  water: {
    color: colorPalette.iceBlue,
    metalness: 0.9,
    roughness: 0.1,
  },
} as const;

// Responsive breakpoints
export const breakpoints = {
  mobile: 768,
  tablet: 1024,
  desktop: 1440,
  ultrawide: 1920,
} as const;

// Camera settings per viewport
export const cameraSettings = {
  mobile: { position: [0, 2, 12] as [number, number, number], fov: 60 },
  tablet: { position: [0, 2, 10] as [number, number, number], fov: 55 },
  desktop: { position: [0, 2, 8] as [number, number, number], fov: 50 },
  ultrawide: { position: [0, 2, 8] as [number, number, number], fov: 45 },
} as const;

// Quality settings per device type
export const qualitySettings = {
  mobile: {
    shadows: false,
    postProcessing: false,
    particleCount: 200,
    waterSubdivision: 32,
  },
  tablet: {
    shadows: true,
    postProcessing: true,
    particleCount: 500,
    waterSubdivision: 64,
  },
  desktop: {
    shadows: true,
    postProcessing: true,
    particleCount: 1000,
    waterSubdivision: 128,
  },
} as const;
