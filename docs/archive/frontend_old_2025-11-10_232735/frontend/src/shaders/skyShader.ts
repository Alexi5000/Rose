/**
 * Sky gradient shader for ocean horizon
 * Creates smooth vertical gradient from deep blue to warm orange/pink
 * Uses smoothstep for natural color blending as per design requirements
 * 
 * Requirements: 9.2, 9.3, 9.4, 9.5
 */

export const skyShader = {
  uniforms: {
    topColor: { value: null }, // Deep blue at top (#0a1e3d)
    midColor: { value: null }, // Sky blue in middle (#1e4d8b)
    horizonColor: { value: null }, // Warm pink at horizon (#ff6b9d)
    bottomColor: { value: null }, // Warm orange at bottom (#ff8c42)
  },
  
  vertexShader: `
    varying vec3 vWorldPosition;
    
    void main() {
      vec4 worldPosition = modelMatrix * vec4(position, 1.0);
      vWorldPosition = worldPosition.xyz;
      
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  
  fragmentShader: `
    uniform vec3 topColor;
    uniform vec3 midColor;
    uniform vec3 horizonColor;
    uniform vec3 bottomColor;
    
    varying vec3 vWorldPosition;
    
    void main() {
      // Normalize Y position for gradient (-1 to 1)
      float h = normalize(vWorldPosition).y;
      
      vec3 color;
      
      // Create smooth gradient with multiple color stops
      // Using smoothstep for natural color blending (Requirement 9.3)
      if (h > 0.4) {
        // Top section: deep blue to sky blue
        float t = smoothstep(0.4, 1.0, h);
        color = mix(midColor, topColor, t);
      } else if (h > 0.0) {
        // Middle section: sky blue to warm pink
        float t = smoothstep(0.0, 0.4, h);
        color = mix(horizonColor, midColor, t);
      } else {
        // Bottom section: warm pink to warm orange
        float t = smoothstep(-0.2, 0.0, h);
        color = mix(bottomColor, horizonColor, t);
      }
      
      gl_FragColor = vec4(color, 1.0);
    }
  `,
};
