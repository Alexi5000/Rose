import { useMemo } from 'react';
import * as THREE from 'three';
import { refinedGradients, refinedFogConfig, refinedMaterialColors } from '../../config/refinedColors';
import { skyShader } from '../../shaders/skyShader';

/**
 * Ocean horizon with gradient sky
 * Creates the background environment with:
 * - Large sphere/dome for gradient sky (blue to orange/pink)
 * - Distant water plane for ocean
 * - Atmospheric fog for depth perception
 * 
 * Requirements: 1.3, 9.1, 9.2, 9.3, 1.5, 11.5, 9.4, 9.5
 */
export const OceanHorizon = () => {
  // Create custom shader material for sky gradient - refined colors
  // Uses smoothstep for natural color blending between deep blue and warm tones
  const skyMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      uniforms: {
        topColor: { value: new THREE.Color(refinedGradients.sky.colors[0].color) },
        midColor: { value: new THREE.Color(refinedGradients.sky.colors[1].color) },
        horizonColor: { value: new THREE.Color(refinedGradients.sky.colors[2].color) },
        bottomColor: { value: new THREE.Color(refinedGradients.sky.colors[3].color) },
      },
      vertexShader: skyShader.vertexShader,
      fragmentShader: skyShader.fragmentShader,
      side: THREE.BackSide, // Render inside of sphere
      depthWrite: false, // Don't write to depth buffer (background element)
    });
  }, []);

  // Create ocean water material with refined properties
  // Enhanced reflection and smoother surface
  const oceanMaterial = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: refinedMaterialColors.water.color,
      emissive: refinedMaterialColors.water.emissive,
      emissiveIntensity: refinedMaterialColors.water.emissiveIntensity,
      metalness: refinedMaterialColors.water.metalness,
      roughness: refinedMaterialColors.water.roughness,
      envMapIntensity: 1.5,
    });
  }, []);

  // Use refined fog color for better atmospheric integration
  const fogColor = useMemo(() => {
    return new THREE.Color(refinedFogConfig.color);
  }, []);

  return (
    <group>
      {/* Sky dome - large sphere for gradient background */}
      {/* Creates vertical gradient from deep blue to warm orange/pink */}
      <mesh material={skyMaterial} renderOrder={-1}>
        <sphereGeometry args={[500, 32, 32]} />
      </mesh>

      {/* Distant ocean plane */}
      {/* Positioned far back to create depth and atmospheric perspective */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.5, -50]}
        material={oceanMaterial}
        receiveShadow
      >
        <planeGeometry args={[1000, 1000, 1, 1]} />
      </mesh>

      {/* Atmospheric fog for depth perception - refined distances */}
      {/* Fog color matches horizon gradient for seamless blending */}
      {/* Refined near/far values for better atmospheric depth */}
      <fog attach="fog" args={[fogColor, refinedFogConfig.near, refinedFogConfig.far]} />
    </group>
  );
};
