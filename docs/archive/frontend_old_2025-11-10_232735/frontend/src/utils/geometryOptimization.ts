import * as THREE from 'three';

/**
 * Geometry Optimization Utilities
 * 
 * Provides utilities for optimizing 3D geometry and materials:
 * - Geometry merging for reduced draw calls
 * - Frustum culling helpers
 * - Material disposal and cleanup
 * - Polygon count reduction
 * 
 * Requirements: 6.2, 6.3
 */

/**
 * Merge multiple geometries into a single geometry
 * Reduces draw calls significantly for static objects
 * Note: Requires BufferGeometryUtils from three/examples/jsm/utils/BufferGeometryUtils
 */
export const mergeGeometries = (
  geometries: THREE.BufferGeometry[],
  materials?: THREE.Material[]
): { geometry: THREE.BufferGeometry; material?: THREE.Material } => {
  if (geometries.length === 0) {
    throw new Error('No geometries provided for merging');
  }

  // For now, return first geometry
  // In production, import BufferGeometryUtils from three/examples/jsm/utils/BufferGeometryUtils
  console.warn('Geometry merging not fully implemented. Import BufferGeometryUtils for production use.');
  
  return {
    geometry: geometries[0],
    material: materials?.[0],
  };
};

/**
 * Optimize geometry by removing unnecessary data
 * and computing efficient bounds
 */
export const optimizeGeometry = (geometry: THREE.BufferGeometry): THREE.BufferGeometry => {
  // Compute bounding sphere for frustum culling
  geometry.computeBoundingSphere();
  geometry.computeBoundingBox();

  // Compute vertex normals if not present
  if (!geometry.attributes.normal) {
    geometry.computeVertexNormals();
  }

  return geometry;
};

/**
 * Reduce polygon count of geometry using simplification
 * Note: This is a basic implementation. For production, consider using
 * three-mesh-bvh or similar libraries for better results
 */
export const simplifyGeometry = (
  geometry: THREE.BufferGeometry,
  _targetReduction: number = 0.5
): THREE.BufferGeometry => {
  // For now, return original geometry
  // In production, implement or use a library like SimplifyModifier
  console.warn('Geometry simplification not fully implemented');
  return geometry;
};

/**
 * Setup frustum culling for a mesh or group
 * Automatically hides objects outside camera view
 */
export const enableFrustumCulling = (object: THREE.Object3D): void => {
  object.frustumCulled = true;

  // Recursively enable for children
  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.frustumCulled = true;

      // Ensure geometry has proper bounds for culling
      if (child.geometry) {
        child.geometry.computeBoundingSphere();
        child.geometry.computeBoundingBox();
      }
    }
  });
};

/**
 * Disable frustum culling for objects that should always be visible
 */
export const disableFrustumCulling = (object: THREE.Object3D): void => {
  object.frustumCulled = false;

  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.frustumCulled = false;
    }
  });
};

/**
 * Calculate total polygon count for an object
 */
export const getPolygonCount = (object: THREE.Object3D): number => {
  let count = 0;

  object.traverse((child) => {
    if (child instanceof THREE.Mesh && child.geometry) {
      const geometry = child.geometry;
      if (geometry.index) {
        count += geometry.index.count / 3;
      } else if (geometry.attributes.position) {
        count += geometry.attributes.position.count / 3;
      }
    }
  });

  return Math.floor(count);
};

/**
 * Dispose of geometry and materials to free memory
 */
export const disposeObject = (object: THREE.Object3D): void => {
  object.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      // Dispose geometry
      if (child.geometry) {
        child.geometry.dispose();
      }

      // Dispose materials
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((material) => disposeMaterial(material));
        } else {
          disposeMaterial(child.material);
        }
      }
    }
  });
};

/**
 * Dispose of a single material and its textures
 */
export const disposeMaterial = (material: THREE.Material): void => {
  // Dispose textures
  Object.keys(material).forEach((key) => {
    const value = (material as any)[key];
    if (value && value instanceof THREE.Texture) {
      value.dispose();
    }
  });

  // Dispose material
  material.dispose();
};

/**
 * Create instanced mesh from array of transforms
 * Significantly improves performance for repeated geometry
 */
export const createInstancedMesh = (
  geometry: THREE.BufferGeometry,
  material: THREE.Material,
  transforms: Array<{
    position: [number, number, number];
    rotation?: [number, number, number];
    scale?: [number, number, number] | number;
  }>
): THREE.InstancedMesh => {
  const count = transforms.length;
  const instancedMesh = new THREE.InstancedMesh(geometry, material, count);

  const dummy = new THREE.Object3D();

  transforms.forEach((transform, i) => {
    dummy.position.set(...transform.position);

    if (transform.rotation) {
      dummy.rotation.set(...transform.rotation);
    }

    if (transform.scale) {
      if (typeof transform.scale === 'number') {
        dummy.scale.setScalar(transform.scale);
      } else {
        dummy.scale.set(...transform.scale);
      }
    }

    dummy.updateMatrix();
    instancedMesh.setMatrixAt(i, dummy.matrix);
  });

  instancedMesh.instanceMatrix.needsUpdate = true;

  return instancedMesh;
};

/**
 * Level of Detail (LOD) helper
 * Returns appropriate geometry detail level based on distance
 */
export const getLODGeometry = (
  distance: number,
  geometries: {
    high: THREE.BufferGeometry;
    medium: THREE.BufferGeometry;
    low: THREE.BufferGeometry;
  }
): THREE.BufferGeometry => {
  if (distance < 5) return geometries.high;
  if (distance < 15) return geometries.medium;
  return geometries.low;
};

/**
 * Batch draw calls by grouping objects with same material
 */
export const batchByMaterial = (
  objects: THREE.Mesh[]
): Map<THREE.Material, THREE.Mesh[]> => {
  const batches = new Map<THREE.Material, THREE.Mesh[]>();

  objects.forEach((mesh) => {
    const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;

    if (!batches.has(material)) {
      batches.set(material, []);
    }

    batches.get(material)!.push(mesh);
  });

  return batches;
};

/**
 * Calculate optimal geometry segments based on screen size
 */
export const getOptimalSegments = (
  baseSegments: number,
  screenWidth: number
): number => {
  if (screenWidth < 768) return Math.floor(baseSegments * 0.5); // Mobile
  if (screenWidth < 1024) return Math.floor(baseSegments * 0.75); // Tablet
  return baseSegments; // Desktop
};
