import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { refinedAmbientAnimations } from '../../config/refinedAnimations';
import { useResponsiveScene } from '../../hooks/useResponsiveScene';
import { disposeObject } from '../../utils/memoryManagement';

interface Particle {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  speed: number;
  size: number;
  drift: number;
}

interface ParticleSystemProps {
  reducedMotion?: boolean; // Reduced motion accessibility setting
}

/**
 * Atmospheric particle system for mist/snow effect
 * Uses instanced meshes for optimal performance
 * Implements gentle floating animation with depth-based opacity
 * 
 * Task 22.4: Enhanced particle density and behavior for better atmosphere
 */
export const ParticleSystem = ({ reducedMotion = false }: ParticleSystemProps) => {
  const meshRef = useRef<THREE.InstancedMesh>(null);
  const { quality } = useResponsiveScene();
  
  // Get particle count based on device performance - refined for better density
  // Reduce particle count further when reducedMotion is enabled
  const baseCount = quality.particleCount;
  const particleCount = reducedMotion ? Math.floor(baseCount * 0.5) : baseCount;
  
  // Create particle data with varying sizes and speeds - refined values
  const particles = useMemo<Particle[]>(() => {
    const temp: Particle[] = [];
    
    const { minSpeed, maxSpeed, driftAmplitude, resetHeight } = refinedAmbientAnimations.particles;
    
    for (let i = 0; i < particleCount; i++) {
      temp.push({
        position: new THREE.Vector3(
          (Math.random() - 0.5) * 20,  // X: spread across scene
          Math.random() * resetHeight,  // Y: height (refined)
          (Math.random() - 0.5) * 20    // Z: depth
        ),
        velocity: new THREE.Vector3(0, 0, 0),
        speed: minSpeed + Math.random() * (maxSpeed - minSpeed),  // Refined fall speeds
        size: 0.02 + Math.random() * 0.05,   // Varying particle sizes
        drift: (Math.random() - 0.5) * driftAmplitude // Refined horizontal drift
      });
    }
    
    return temp;
  }, [particleCount]);
  
  // Dummy object for matrix updates
  const dummy = useMemo(() => new THREE.Object3D(), []);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (meshRef.current) {
        console.log('Cleaning up ParticleSystem...');
        disposeObject(meshRef.current);
      }
    };
  }, []);
  
  // Animate particles with gentle floating motion - refined timing
  useFrame((state) => {
    if (!meshRef.current) return;
    
    const camera = state.camera;
    const { resetHeight, minHeight } = refinedAmbientAnimations.particles;
    
    particles.forEach((particle, i) => {
      // Gentle downward floating motion (refined speeds applied in particle creation)
      particle.position.y -= particle.speed;
      
      // Subtle horizontal drift (refined amplitude applied in particle creation)
      particle.position.x += particle.drift;
      
      // Reset particles at top when they reach bottom - refined heights
      if (particle.position.y < minHeight) {
        particle.position.y = resetHeight;
        particle.position.x = (Math.random() - 0.5) * 20;
        particle.position.z = (Math.random() - 0.5) * 20;
      }
      
      // Calculate distance from camera for depth-based opacity
      const distance = camera.position.distanceTo(particle.position);
      
      // Fade particles based on distance (atmospheric depth effect)
      // Closer particles are more visible, distant ones fade out
      const maxDistance = 15;
      const opacity = Math.max(0, 1 - (distance / maxDistance));
      
      // Update instance matrix
      dummy.position.copy(particle.position);
      dummy.scale.setScalar(particle.size * opacity); // Scale affects visibility
      dummy.updateMatrix();
      
      meshRef.current!.setMatrixAt(i, dummy.matrix);
    });
    
    // Mark instance matrix as needing update
    meshRef.current.instanceMatrix.needsUpdate = true;
  });
  
  return (
    <instancedMesh ref={meshRef} args={[undefined, undefined, particleCount]}>
      {/* Simple sphere geometry for particles */}
      <sphereGeometry args={[1, 8, 8]} />
      
      {/* Semi-transparent white material with additive blending for ethereal effect */}
      <meshBasicMaterial
        color="#ffffff"
        transparent
        opacity={0.6}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </instancedMesh>
  );
};
