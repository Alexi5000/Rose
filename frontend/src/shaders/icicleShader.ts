import * as THREE from 'three';

/**
 * 🧊 Custom ice shader with subsurface scattering, Fresnel effect, and refraction
 * Creates realistic ice appearance with translucency and edge glow
 * Colors match design system - bright glowing blue icicles
 */
export const icicleShader = {
  uniforms: {
    time: { value: 0 },
    lightPosition: { value: new THREE.Vector3(0, 10, 5) },
    baseColor: { value: new THREE.Color('#4d9fff') }, // COLORS.ICICLE_BRIGHT from design system
    emissiveColor: { value: new THREE.Color('#5dadff') }, // COLORS.ICICLE_HIGHLIGHT
    translucency: { value: 0.9 },
    subsurfaceStrength: { value: 0.6 }, // Increased for more glow
    fresnelPower: { value: 2.5 }, // Reduced for more visible glow
    glowIntensity: { value: 0.5 }, // Increased glow intensity
    refractionStrength: { value: 0.1 },
  },

  vertexShader: `
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec3 vViewPosition;
    varying vec2 vUv;
    
    void main() {
      vUv = uv;
      vNormal = normalize(normalMatrix * normal);
      vPosition = (modelMatrix * vec4(position, 1.0)).xyz;
      
      vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
      vViewPosition = -mvPosition.xyz;
      
      gl_Position = projectionMatrix * mvPosition;
    }
  `,

  fragmentShader: `
    uniform float time;
    uniform vec3 lightPosition;
    uniform vec3 baseColor;
    uniform vec3 emissiveColor;
    uniform float translucency;
    uniform float subsurfaceStrength;
    uniform float fresnelPower;
    uniform float glowIntensity;
    uniform float refractionStrength;
    
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec3 vViewPosition;
    varying vec2 vUv;
    
    // Simple noise function for surface detail
    float noise(vec2 st) {
      return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
    }
    
    void main() {
      // Normalize vectors
      vec3 normal = normalize(vNormal);
      vec3 viewDir = normalize(vViewPosition);
      vec3 lightDir = normalize(lightPosition - vPosition);
      
      // Fresnel effect for edge glow
      float fresnel = pow(1.0 - max(0.0, dot(normal, viewDir)), fresnelPower);
      
      // Subsurface scattering approximation
      // Light passing through the ice
      float subsurface = max(0.0, dot(-lightDir, normal));
      subsurface = pow(subsurface, 2.0) * subsurfaceStrength;
      
      // Add surface detail using noise
      float surfaceNoise = noise(vUv * 10.0 + time * 0.1) * 0.1;
      
      // Combine base color with subsurface and fresnel
      vec3 iceColor = baseColor;
      iceColor += subsurface * vec3(0.3, 0.6, 1.0); // Blue subsurface tint
      iceColor += fresnel * vec3(0.5, 0.8, 1.0) * glowIntensity; // Edge glow
      
      // Add emissive glow
      vec3 emissive = emissiveColor * 0.2;
      
      // Final color
      vec3 finalColor = iceColor + emissive + surfaceNoise;
      
      // Calculate opacity with fresnel for translucency
      float alpha = mix(translucency, 1.0, fresnel * 0.5);
      
      gl_FragColor = vec4(finalColor, alpha);
    }
  `,
};
