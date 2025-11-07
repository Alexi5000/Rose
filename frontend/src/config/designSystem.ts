/**
 * 🎨 ROSE HEALER SHAMAN - DESIGN SYSTEM
 *
 * Single source of truth for all design tokens.
 * Extracted from reference design with precision.
 * Uncle Bob approved - Zero magic numbers!
 *
 * Color naming convention: [element]_[property]_[variant?]
 */

// ========================================
// 🌈 COLOR PALETTE
// ========================================

export const COLORS = {
  // Background Gradient (Top → Bottom)
  BACKGROUND_TOP: '#0a1e3d',      // Deep navy blue (top of scene)
  BACKGROUND_MID: '#1e4d8b',      // Medium ocean blue (middle)
  BACKGROUND_BOTTOM: '#4d9fff',   // Bright cyan/teal (bottom/water)

  // Ice Cave & Icicles
  ICICLE_BRIGHT: '#4d9fff',       // Bright glowing blue
  ICICLE_HIGHLIGHT: '#5dadff',    // Lighter blue for highlights
  ICICLE_SHADOW: '#2a5f9f',       // Darker blue for depth
  CAVE_AMBIENT: '#1e3a5f',        // Cave walls ambient color

  // Igloo Warm Glow
  IGLOO_GLOW_CORE: '#ff8c42',     // Warm orange core
  IGLOO_GLOW_MID: '#ffa564',      // Mid-range glow
  IGLOO_GLOW_OUTER: '#ffc188',    // Outer soft glow
  IGLOO_STRUCTURE: '#e8d4c8',     // Igloo brick color

  // Water & Reflections
  WATER_SURFACE: '#4d9fff',       // Bright cyan water
  WATER_DEEP: '#2a6fbb',          // Deeper water color
  WATER_RIPPLE: '#7db9ff',        // Lighter ripple highlights
  WATER_REFLECTION: '#3d7fcc',    // Reflection tint

  // Aurora Effect
  AURORA_BLUE: '#4d9fff',         // Primary aurora blue
  AURORA_PURPLE: '#9d4dff',       // Aurora purple accent
  AURORA_CYAN: '#4dffaa',         // Aurora cyan/green tint

  // Rose Avatar (Meditation Figure)
  FIGURE_ROBE_LIGHT: '#e8f4ff',   // Light blue/white robe
  FIGURE_ROBE_SHADOW: '#a8c8e8',  // Robe shadow areas
  FIGURE_SILHOUETTE: '#2a4a6a',   // Dark silhouette base
  FIGURE_SKIN_TONE: '#d4a88e',    // Subtle skin tone

  // Environment
  TREE_SILHOUETTE: '#1a2332',     // Dark tree silhouette
  GRASS_DARK: '#2a4a3a',          // Dark grass/shore
  GRASS_HIGHLIGHT: '#4a7a5a',     // Grass highlights
  ROCKS_DARK: '#3a4a5a',          // Dark rocks
  HORIZON_SKY: '#7db9ff',         // Ocean horizon sky

  // UI Elements
  TEXT_PRIMARY: '#ffffff',        // Main title text
  TEXT_SHADOW: 'rgba(0, 0, 0, 0.5)', // Text shadow for depth
  BUTTON_GLOW: '#4d9fff',         // Voice button glow

} as const;

// ========================================
// 🎭 LIGHTING CONFIGURATION
// ========================================

export const LIGHTING = {
  // Ambient Lighting
  AMBIENT_INTENSITY: 0.4,
  AMBIENT_COLOR: COLORS.BACKGROUND_MID,

  // Igloo Warm Light
  IGLOO_LIGHT_INTENSITY: 2.5,
  IGLOO_LIGHT_COLOR: COLORS.IGLOO_GLOW_CORE,
  IGLOO_LIGHT_DISTANCE: 15,
  IGLOO_LIGHT_DECAY: 2,

  // Aurora Overhead Light
  AURORA_LIGHT_INTENSITY: 1.2,
  AURORA_LIGHT_COLOR: COLORS.AURORA_BLUE,

  // Water Reflection Light
  WATER_LIGHT_INTENSITY: 0.8,
  WATER_LIGHT_COLOR: COLORS.WATER_SURFACE,

  // Moonlight/Key Light
  KEY_LIGHT_INTENSITY: 1.5,
  KEY_LIGHT_COLOR: '#c8e4ff',

  // Fill Light (soft overall)
  FILL_LIGHT_INTENSITY: 0.6,
  FILL_LIGHT_COLOR: COLORS.BACKGROUND_BOTTOM,
} as const;

// ========================================
// 📐 SCENE COMPOSITION
// ========================================

export const SCENE_LAYOUT = {
  // Camera Settings
  CAMERA_FOV: 50,
  CAMERA_POSITION_X: 0,
  CAMERA_POSITION_Y: 2,
  CAMERA_POSITION_Z: 12,
  CAMERA_LOOK_AT_Y: 1,

  // Igloo Position (Left side)
  IGLOO_POSITION_X: -6,
  IGLOO_POSITION_Y: 0.5,
  IGLOO_POSITION_Z: -2,
  IGLOO_SCALE: 1.2,

  // Rose Avatar (Center on water)
  ROSE_POSITION_X: 0,
  ROSE_POSITION_Y: 0,
  ROSE_POSITION_Z: 0,
  ROSE_SCALE: 1.0,

  // Water Surface
  WATER_POSITION_Y: -0.2,
  WATER_SCALE: 20,

  // Tree Position (Right side)
  TREE_POSITION_X: 8,
  TREE_POSITION_Y: 0,
  TREE_POSITION_Z: -1,
  TREE_SCALE: 1.5,

  // Icicles (Top of scene)
  ICICLE_START_Y: 8,
  ICICLE_COUNT: 12,
  ICICLE_SPREAD_X: 15,

  // Ocean Horizon
  HORIZON_POSITION_Z: -30,
  HORIZON_SCALE_X: 50,
} as const;

// ========================================
// ✨ MATERIAL PROPERTIES
// ========================================

export const MATERIALS = {
  // Icicle Material
  ICICLE_OPACITY: 0.7,
  ICICLE_METALNESS: 0.1,
  ICICLE_ROUGHNESS: 0.2,
  ICICLE_TRANSMISSION: 0.6,      // Glass-like transmission

  // Water Material
  WATER_OPACITY: 0.85,
  WATER_METALNESS: 0.9,
  WATER_ROUGHNESS: 0.1,
  WATER_REFLECTION_STRENGTH: 0.8,

  // Igloo Material
  IGLOO_ROUGHNESS: 0.8,
  IGLOO_METALNESS: 0.0,
  IGLOO_EMISSIVE_INTENSITY: 1.5,  // Glowing from inside

  // Figure Material
  FIGURE_ROUGHNESS: 0.6,
  FIGURE_METALNESS: 0.0,
} as const;

// ========================================
// 🎬 ANIMATION TIMINGS
// ========================================

export const ANIMATIONS = {
  // Entry Animation
  ENTRY_DURATION_SECONDS: 3,
  CAMERA_ZOOM_DURATION: 2.5,
  FADE_IN_DURATION: 1.5,

  // Idle Animations
  WATER_RIPPLE_SPEED: 0.3,
  AURORA_FLOW_SPEED: 0.15,
  ICICLE_GLOW_PULSE_SPEED: 0.8,
  FIGURE_BREATHING_SPEED: 0.5,

  // Audio Reactive
  AUDIO_RESPONSE_SMOOTHING: 0.1,
  AUDIO_AMPLITUDE_MULTIPLIER: 2.0,
} as const;

// ========================================
// 📱 RESPONSIVE BREAKPOINTS
// ========================================

export const BREAKPOINTS = {
  MOBILE_MAX_WIDTH: 768,
  TABLET_MAX_WIDTH: 1024,
  DESKTOP_MAX_WIDTH: 1440,
  ULTRAWIDE_MIN_WIDTH: 1920,
} as const;

// ========================================
// 🎯 ACCESSIBILITY
// ========================================

export const ACCESSIBILITY = {
  REDUCED_MOTION_ANIMATION_SCALE: 0.3,
  MIN_CONTRAST_RATIO: 4.5,
  FOCUS_OUTLINE_COLOR: COLORS.AURORA_CYAN,
  FOCUS_OUTLINE_WIDTH: 3,
} as const;

// ========================================
// 📊 TYPE EXPORTS
// ========================================

export type ColorKey = keyof typeof COLORS;
export type LightingKey = keyof typeof LIGHTING;
export type SceneLayoutKey = keyof typeof SCENE_LAYOUT;

// ========================================
// 🔍 HELPER FUNCTIONS
// ========================================

/**
 * 🎨 Convert hex color to Three.js Color object
 */
export const hexToThreeColor = (hex: string) => {
  // Used in Three.js components - import THREE in component, not here
  return hex;
};

/**
 * 📐 Get responsive scale factor based on screen width
 */
export const getResponsiveScale = (screenWidth: number): number => {
  if (screenWidth <= BREAKPOINTS.MOBILE_MAX_WIDTH) return 0.7;
  if (screenWidth <= BREAKPOINTS.TABLET_MAX_WIDTH) return 0.85;
  if (screenWidth >= BREAKPOINTS.ULTRAWIDE_MIN_WIDTH) return 1.2;
  return 1.0;
};

/**
 * 🌈 Create CSS gradient string for background
 */
export const getBackgroundGradient = (): string => {
  return `linear-gradient(
    to bottom,
    ${COLORS.BACKGROUND_TOP} 0%,
    ${COLORS.BACKGROUND_MID} 50%,
    ${COLORS.BACKGROUND_BOTTOM} 100%
  )`;
};

/**
 * 💡 Log design system initialization
 */
export const logDesignSystemInit = (): void => {
  console.log('🎨 Design System initialized');
  console.log('🌈 Color palette loaded:', Object.keys(COLORS).length, 'colors');
  console.log('💡 Lighting presets loaded:', Object.keys(LIGHTING).length, 'configs');
  console.log('📐 Scene layout defined:', Object.keys(SCENE_LAYOUT).length, 'positions');
};