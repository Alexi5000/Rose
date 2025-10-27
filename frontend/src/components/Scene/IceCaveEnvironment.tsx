import React, { useRef, useMemo, useEffect } from 'react';
import * as THREE from 'three';
import { useFrame } from '@react-three/fiber';
import { icicleShader } from '../../shaders/icicleShader';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';
import { refinedMaterialColors } from '../../config/refinedColors';
import { enableFrustumCulling, optimizeGeometry } from '../../utils/geometryOptimization';
import { disposeObject } from '../../utils/memoryManagement';

/**
 * Ice cave environment with icicles and cave walls
 * Creates dramatic framing with procedural icicles along the top edge
 * 
 * Task 22.4: Enhanced with subtle environmental details
 * - Small ice crystals scattered on ground
 * - Subtle rocks near igloo
 * - Enhanced depth and atmosphere
 * 
 * Implements LOD system for mobile performance optimization
 */
export const IceCaveEnvironment = () => {
  const iciclesRef = useRef<THREE.InstancedMesh>(null);
  const caveWallsRef = useRef<THREE.Group>(null);
  const icicleShaderRef = useRef<THREE.ShaderMaterial>(null);
  const wallShaderRefs = useRef<THREE.ShaderMaterial[]>([]);
  const iceCrystalsRef = useRef<THREE.InstancedMesh>(null);
  const rocksRef = useRef<THREE.InstancedMesh>(null);
  
  const { isMobile, isTablet } = useResponsiveScene();

  // Generate procedural icicle positions along top edge
  // Reduce count on mobile for better performance (LOD system)
  const icicleData = useMemo(() => {
    const count = isMobile ? 20 : isTablet ? 35 : 50;
    const data: Array<{
      position: [number, number, number];
      rotation: [number, number, number];
      scale: [number, number, number];
    }> = [];

    for (let i = 0; i < count; i++) {
      // Distribute along top edge (left to right)
      const x = (i / count) * 20 - 10;
      const y = 5 + Math.random() * 2; // Vary height slightly
      const z = -5 + Math.random() * 2; // Vary depth for natural look

      // Vary sizes for natural appearance
      const baseScale = 0.3 + Math.random() * 0.7;
      const length = 0.5 + Math.random() * 1.5;

      // Vary rotations slightly
      const rotationX = Math.random() * 0.2 - 0.1;
      const rotationY = Math.random() * 0.3 - 0.15;
      const rotationZ = Math.random() * 0.2 - 0.1;

      data.push({
        position: [x, y, z],
        rotation: [rotationX, rotationY, rotationZ],
        scale: [baseScale, length, baseScale],
      });
    }

    return data;
  }, [isMobile, isTablet]);

  // Set up instanced mesh matrices
  useMemo(() => {
    if (!iciclesRef.current) return;

    const dummy = new THREE.Object3D();
    icicleData.forEach((icicle, i) => {
      dummy.position.set(...icicle.position);
      dummy.rotation.set(...icicle.rotation);
      dummy.scale.set(...icicle.scale);
      dummy.updateMatrix();
      iciclesRef.current!.setMatrixAt(i, dummy.matrix);
    });
    iciclesRef.current.instanceMatrix.needsUpdate = true;
  }, [icicleData]);

  // Subtle animation for icicles (very gentle sway) and update shader time
  useFrame((state) => {
    const time = state.clock.elapsedTime;

    // Update shader time uniform for all ice materials (only on desktop/tablet)
    if (!isMobile) {
      if (icicleShaderRef.current) {
        icicleShaderRef.current.uniforms.time.value = time;
      }
      wallShaderRefs.current.forEach((shader) => {
        if (shader) {
          shader.uniforms.time.value = time;
        }
      });
    }

    // Animate icicles with very subtle sway (skip on mobile for performance)
    if (iciclesRef.current && !isMobile) {
      const dummy = new THREE.Object3D();

      icicleData.forEach((icicle, i) => {
        // Very subtle sway animation
        const swayX = Math.sin(time * 0.5 + i * 0.1) * 0.002;
        const swayZ = Math.cos(time * 0.3 + i * 0.15) * 0.002;

        dummy.position.set(
          icicle.position[0] + swayX,
          icicle.position[1],
          icicle.position[2] + swayZ
        );
        dummy.rotation.set(...icicle.rotation);
        dummy.scale.set(...icicle.scale);
        dummy.updateMatrix();
        iciclesRef.current!.setMatrixAt(i, dummy.matrix);
      });

      iciclesRef.current.instanceMatrix.needsUpdate = true;
    }
  });

  // Use simpler geometry on mobile for better performance
  const icicleGeometrySegments = isMobile ? 6 : 8;

  // Optimize geometries on mount
  const icicleGeometry = useMemo(() => {
    const geometry = new THREE.ConeGeometry(0.1, 1, icicleGeometrySegments);
    return optimizeGeometry(geometry);
  }, [icicleGeometrySegments]);

  // Enable frustum culling for performance optimization and cleanup
  useEffect(() => {
    const currentIcicles = iciclesRef.current;
    const currentWalls = caveWallsRef.current;
    const currentGeometry = icicleGeometry;

    if (currentIcicles) {
      enableFrustumCulling(currentIcicles);
    }
    if (currentWalls) {
      enableFrustumCulling(currentWalls);
    }

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up IceCaveEnvironment...');
      if (currentIcicles) {
        disposeObject(currentIcicles);
      }
      if (currentWalls) {
        disposeObject(currentWalls);
      }
      // Dispose optimized geometry
      if (currentGeometry) {
        currentGeometry.dispose();
      }
    };
  }, [icicleGeometry]);

  return (
    <group name="ice-cave-environment">
      {/* Icicles using instanced mesh for performance with custom ice shader */}
      <instancedMesh
        ref={iciclesRef}
        args={[icicleGeometry, undefined, icicleData.length]}
        castShadow={!isMobile} // Disable shadows on mobile for performance
        receiveShadow={!isMobile}
      >
        {isMobile ? (
          // Use simpler standard material on mobile
          <meshStandardMaterial
            color={refinedMaterialColors.ice.color}
            emissive={refinedMaterialColors.ice.emissive}
            emissiveIntensity={refinedMaterialColors.ice.emissiveIntensity}
            metalness={refinedMaterialColors.ice.metalness}
            roughness={refinedMaterialColors.ice.roughness}
            transparent
            opacity={0.8}
          />
        ) : (
          // Use advanced shader on desktop/tablet
          <shaderMaterial
            ref={icicleShaderRef}
            uniforms={icicleShader.uniforms}
            vertexShader={icicleShader.vertexShader}
            fragmentShader={icicleShader.fragmentShader}
            transparent
            side={THREE.DoubleSide}
          />
        )}
      </instancedMesh>

      {/* Cave walls - curved walls on sides for framing with custom ice shader */}
      <group ref={caveWallsRef} name="cave-walls">
        {/* Left cave wall */}
        <mesh position={[-8, 2, -3]} rotation={[0, 0.3, 0]} castShadow={!isMobile} receiveShadow={!isMobile}>
          <cylinderGeometry args={[3, 3, 8, isMobile ? 8 : 16, 1, true, 0, Math.PI * 0.5]} />
          {isMobile ? (
            <meshStandardMaterial
              color={refinedMaterialColors.ice.color}
              emissive={refinedMaterialColors.ice.emissive}
              emissiveIntensity={refinedMaterialColors.ice.emissiveIntensity}
              metalness={refinedMaterialColors.ice.metalness}
              roughness={refinedMaterialColors.ice.roughness}
              transparent
              opacity={0.7}
              side={THREE.DoubleSide}
            />
          ) : (
            <shaderMaterial
              ref={(ref) => {
                if (ref) wallShaderRefs.current[0] = ref;
              }}
              uniforms={{
                ...icicleShader.uniforms,
                translucency: { value: 0.7 },
              }}
              vertexShader={icicleShader.vertexShader}
              fragmentShader={icicleShader.fragmentShader}
              transparent
              side={THREE.DoubleSide}
            />
          )}
        </mesh>

        {/* Right cave wall */}
        <mesh position={[8, 2, -3]} rotation={[0, -0.3, 0]} castShadow={!isMobile} receiveShadow={!isMobile}>
          <cylinderGeometry args={[3, 3, 8, isMobile ? 8 : 16, 1, true, Math.PI * 0.5, Math.PI * 0.5]} />
          {isMobile ? (
            <meshStandardMaterial
              color={refinedMaterialColors.ice.color}
              emissive={refinedMaterialColors.ice.emissive}
              emissiveIntensity={refinedMaterialColors.ice.emissiveIntensity}
              metalness={refinedMaterialColors.ice.metalness}
              roughness={refinedMaterialColors.ice.roughness}
              transparent
              opacity={0.7}
              side={THREE.DoubleSide}
            />
          ) : (
            <shaderMaterial
              ref={(ref) => {
                if (ref) wallShaderRefs.current[1] = ref;
              }}
              uniforms={{
                ...icicleShader.uniforms,
                translucency: { value: 0.7 },
              }}
              vertexShader={icicleShader.vertexShader}
              fragmentShader={icicleShader.fragmentShader}
              transparent
              side={THREE.DoubleSide}
            />
          )}
        </mesh>

        {/* Top cave ceiling (behind icicles) */}
        <mesh position={[0, 6, -4]} rotation={[Math.PI * 0.1, 0, 0]} receiveShadow={!isMobile}>
          <planeGeometry args={[20, 4, isMobile ? 16 : 32, isMobile ? 8 : 16]} />
          {isMobile ? (
            <meshStandardMaterial
              color={refinedMaterialColors.ice.color}
              emissive={refinedMaterialColors.ice.emissive}
              emissiveIntensity={refinedMaterialColors.ice.emissiveIntensity}
              metalness={refinedMaterialColors.ice.metalness}
              roughness={refinedMaterialColors.ice.roughness}
              transparent
              opacity={0.6}
              side={THREE.DoubleSide}
            />
          ) : (
            <shaderMaterial
              ref={(ref) => {
                if (ref) wallShaderRefs.current[2] = ref;
              }}
              uniforms={{
                ...icicleShader.uniforms,
                translucency: { value: 0.6 },
              }}
              vertexShader={icicleShader.vertexShader}
              fragmentShader={icicleShader.fragmentShader}
              transparent
              side={THREE.DoubleSide}
            />
          )}
        </mesh>
      </group>

      {/* Subtle environmental details - Task 22.4 */}
      {!isMobile && (
        <>
          {/* Small ice crystals scattered on ground for depth */}
          <IceCrystals ref={iceCrystalsRef} count={isTablet ? 15 : 25} />
          
          {/* Subtle rocks near igloo for grounding */}
          <Rocks ref={rocksRef} count={isTablet ? 8 : 12} />
        </>
      )}
    </group>
  );
};

/**
 * Small ice crystals scattered on ground
 * Adds subtle detail and depth to the scene
 */
const IceCrystals = React.forwardRef<THREE.InstancedMesh, { count: number }>(
  ({ count }, ref) => {
    const crystalData = useMemo(() => {
      const data: Array<{
        position: [number, number, number];
        rotation: [number, number, number];
        scale: number;
      }> = [];

      for (let i = 0; i < count; i++) {
        // Scatter around the scene, avoiding center where Rose sits
        const angle = (i / count) * Math.PI * 2;
        const radius = 3 + Math.random() * 4;
        const x = Math.cos(angle) * radius + (Math.random() - 0.5) * 2;
        const z = Math.sin(angle) * radius + (Math.random() - 0.5) * 2;
        const y = 0.05; // Just above ground

        // Random rotations for natural look
        const rotX = Math.random() * Math.PI * 2;
        const rotY = Math.random() * Math.PI * 2;
        const rotZ = Math.random() * Math.PI * 2;

        // Vary sizes
        const scale = 0.05 + Math.random() * 0.1;

        data.push({
          position: [x, y, z],
          rotation: [rotX, rotY, rotZ],
          scale,
        });
      }

      return data;
    }, [count]);

    // Set up instanced mesh matrices
    useMemo(() => {
      if (!ref || typeof ref === 'function' || !ref.current) return;

      const dummy = new THREE.Object3D();
      crystalData.forEach((crystal, i) => {
        dummy.position.set(...crystal.position);
        dummy.rotation.set(...crystal.rotation);
        dummy.scale.setScalar(crystal.scale);
        dummy.updateMatrix();
        ref.current!.setMatrixAt(i, dummy.matrix);
      });
      ref.current.instanceMatrix.needsUpdate = true;
    }, [crystalData, ref]);

    return (
      <instancedMesh ref={ref} args={[undefined, undefined, count]}>
        <octahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color={refinedMaterialColors.ice.color}
          emissive={refinedMaterialColors.ice.emissive}
          emissiveIntensity={refinedMaterialColors.ice.emissiveIntensity * 0.5}
          metalness={refinedMaterialColors.ice.metalness}
          roughness={refinedMaterialColors.ice.roughness}
          transparent
          opacity={0.7}
        />
      </instancedMesh>
    );
  }
);

IceCrystals.displayName = 'IceCrystals';

/**
 * Subtle rocks near igloo
 * Adds grounding and natural detail to the scene
 */
const Rocks = React.forwardRef<THREE.InstancedMesh, { count: number }>(
  ({ count }, ref) => {
    const rockData = useMemo(() => {
      const data: Array<{
        position: [number, number, number];
        rotation: [number, number, number];
        scale: [number, number, number];
      }> = [];

      for (let i = 0; i < count; i++) {
        // Cluster near igloo area (left side)
        const x = -5 + (Math.random() - 0.5) * 3;
        const z = -1 + (Math.random() - 0.5) * 2;
        const y = 0.1; // Partially embedded in ground

        // Random rotations
        const rotX = Math.random() * Math.PI * 0.3;
        const rotY = Math.random() * Math.PI * 2;
        const rotZ = Math.random() * Math.PI * 0.3;

        // Vary sizes and proportions for natural look
        const baseScale = 0.15 + Math.random() * 0.25;
        const scaleX = baseScale * (0.8 + Math.random() * 0.4);
        const scaleY = baseScale * (0.6 + Math.random() * 0.4);
        const scaleZ = baseScale * (0.8 + Math.random() * 0.4);

        data.push({
          position: [x, y, z],
          rotation: [rotX, rotY, rotZ],
          scale: [scaleX, scaleY, scaleZ],
        });
      }

      return data;
    }, [count]);

    // Set up instanced mesh matrices
    useMemo(() => {
      if (!ref || typeof ref === 'function' || !ref.current) return;

      const dummy = new THREE.Object3D();
      rockData.forEach((rock, i) => {
        dummy.position.set(...rock.position);
        dummy.rotation.set(...rock.rotation);
        dummy.scale.set(...rock.scale);
        dummy.updateMatrix();
        ref.current!.setMatrixAt(i, dummy.matrix);
      });
      ref.current.instanceMatrix.needsUpdate = true;
    }, [rockData, ref]);

    return (
      <instancedMesh ref={ref} args={[undefined, undefined, count]} receiveShadow castShadow>
        <dodecahedronGeometry args={[1, 0]} />
        <meshStandardMaterial
          color="#3a4a5a"
          roughness={0.9}
          metalness={0.1}
        />
      </instancedMesh>
    );
  }
);

Rocks.displayName = 'Rocks';
