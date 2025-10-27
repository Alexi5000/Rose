// Custom water surface shader with ripples, reflection, and refraction
import * as THREE from 'three';

export const waterShader = {
  uniforms: {
    time: { value: 0 },
    rippleCenter: { value: new THREE.Vector2(0.5, 0.5) }, // Rose's position in UV space
    rippleStrength: { value: 0.5 },
    skyColorTop: { value: new THREE.Color('#0a1e3d') },
    skyColorHorizon: { value: new THREE.Color('#ff8c42') },
    waterColorDeep: { value: new THREE.Color('#0a1e3d') },
    waterColorShallow: { value: new THREE.Color('#4d9fff') },
  },

  vertexShader: `
    uniform float time;
    uniform vec2 rippleCenter;
    uniform float rippleStrength;
    
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying float vElevation;
    varying float vDistanceFromCenter;
    
    void main() {
      vUv = uv;
      vNormal = normal;
      
      // Calculate distance from ripple center (Rose's position)
      vec2 centeredUv = uv - rippleCenter;
      float dist = length(centeredUv);
      vDistanceFromCenter = dist;
      
      // Create concentric ripples emanating from Rose's position
      // Multiple frequencies for natural wave interference
      float ripple1 = sin(dist * 20.0 - time * 2.0) * rippleStrength;
      float ripple2 = sin(dist * 15.0 - time * 1.5) * rippleStrength * 0.5;
      float ripple3 = sin(dist * 10.0 - time * 1.0) * rippleStrength * 0.3;
      
      // Smooth distance-based fade using exponential decay
      // Ripples fade naturally as they move away from Rose
      float fade = exp(-dist * 2.5);
      float smoothFade = smoothstep(0.0, 0.1, fade) * fade;
      
      // Combine ripples with smooth fade
      float totalRipple = (ripple1 + ripple2 + ripple3) * smoothFade;
      
      // Add subtle ambient wave motion for realism
      float baseWave = sin(uv.x * 5.0 + time * 0.5) * 0.02;
      baseWave += sin(uv.y * 3.0 + time * 0.3) * 0.02;
      
      // Displace vertices to create 3D ripple effect
      vec3 newPosition = position;
      newPosition.z += totalRipple * 0.15 + baseWave;
      
      vElevation = totalRipple * 0.15 + baseWave;
      vPosition = newPosition;
      
      gl_Position = projectionMatrix * modelViewMatrix * vec4(newPosition, 1.0);
    }
  `,

  fragmentShader: `
    uniform float time;
    uniform vec3 skyColorTop;
    uniform vec3 skyColorHorizon;
    uniform vec3 waterColorDeep;
    uniform vec3 waterColorShallow;
    
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying float vElevation;
    varying float vDistanceFromCenter;
    
    void main() {
      // Calculate view direction for Fresnel effect
      vec3 viewDirection = normalize(cameraPosition - vPosition);
      
      // Fresnel effect - more reflection at grazing angles
      float fresnel = pow(1.0 - dot(viewDirection, vec3(0.0, 0.0, 1.0)), 2.0);
      
      // Sky reflection gradient based on UV
      vec3 skyReflection = mix(skyColorHorizon, skyColorTop, vUv.y);
      
      // Water color based on depth (elevation) and distance from center
      float depthFactor = smoothstep(-0.1, 0.1, vElevation);
      vec3 waterColor = mix(waterColorDeep, waterColorShallow, depthFactor);
      
      // Enhance color near ripple center (Rose's position)
      float centerGlow = exp(-vDistanceFromCenter * 3.0) * 0.2;
      waterColor = mix(waterColor, waterColorShallow, centerGlow);
      
      // Mix water color and sky reflection based on Fresnel
      vec3 finalColor = mix(waterColor, skyReflection, fresnel * 0.6);
      
      // Add subtle shimmer effect
      float shimmer = sin(vUv.x * 50.0 + time * 2.0) * sin(vUv.y * 50.0 + time * 1.5);
      shimmer = shimmer * 0.05 + 0.95;
      finalColor *= shimmer;
      
      // Add foam/highlights at wave peaks
      float foam = smoothstep(0.08, 0.12, vElevation);
      finalColor = mix(finalColor, vec3(1.0), foam * 0.3);
      
      // Slight transparency for realism
      float alpha = 0.95 + fresnel * 0.05;
      
      gl_FragColor = vec4(finalColor, alpha);
    }
  `,
};
