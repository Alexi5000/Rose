import * as THREE from 'three';

/**
 * Memory Management Utilities
 * 
 * Provides utilities for proper memory cleanup and management:
 * - Dispose geometries and materials on unmount
 * - Clean up event listeners and timers
 * - Manage texture memory usage
 * - Prevent memory leaks
 * 
 * Requirements: 6.3
 */

/**
 * Dispose of a Three.js object and all its children
 * Recursively cleans up geometries, materials, and textures
 */
export const disposeObject = (object: THREE.Object3D): void => {
  if (!object) return;

  // Traverse all children
  object.traverse((child) => {
    // Dispose geometry
    if (child instanceof THREE.Mesh) {
      if (child.geometry) {
        child.geometry.dispose();
      }

      // Dispose materials
      if (child.material) {
        disposeMaterial(child.material);
      }
    }

    // Dispose lights
    if (child instanceof THREE.Light) {
      if ((child as any).dispose) {
        (child as any).dispose();
      }
    }
  });

  // Remove from parent
  if (object.parent) {
    object.parent.remove(object);
  }
};

/**
 * Dispose of material(s) and their textures
 */
export const disposeMaterial = (material: THREE.Material | THREE.Material[]): void => {
  const materials = Array.isArray(material) ? material : [material];

  materials.forEach((mat) => {
    // Dispose all textures in the material
    Object.keys(mat).forEach((key) => {
      const value = (mat as any)[key];

      if (value && value instanceof THREE.Texture) {
        value.dispose();
      }
    });

    // Dispose the material itself
    mat.dispose();
  });
};

/**
 * Dispose of geometry
 */
export const disposeGeometry = (geometry: THREE.BufferGeometry): void => {
  if (geometry) {
    geometry.dispose();
  }
};

/**
 * Dispose of texture
 */
export const disposeTexture = (texture: THREE.Texture): void => {
  if (texture) {
    texture.dispose();
  }
};

/**
 * Clean up event listeners
 */
export const cleanupEventListeners = (
  element: Window | HTMLElement | Document,
  listeners: Array<{ event: string; handler: EventListener }>
): void => {
  listeners.forEach(({ event, handler }) => {
    element.removeEventListener(event, handler);
  });
};

/**
 * Clean up timers and intervals
 */
export const cleanupTimers = (timers: Array<number | ReturnType<typeof setTimeout>>): void => {
  timers.forEach((timer) => {
    if (typeof timer === 'number') {
      clearTimeout(timer);
      clearInterval(timer);
    } else {
      clearTimeout(timer);
      clearInterval(timer);
    }
  });
};

/**
 * Memory usage tracker
 */
export class MemoryTracker {
  private geometries = new Set<THREE.BufferGeometry>();
  private materials = new Set<THREE.Material>();
  private textures = new Set<THREE.Texture>();

  /**
   * Register a geometry for tracking
   */
  trackGeometry(geometry: THREE.BufferGeometry): void {
    this.geometries.add(geometry);
  }

  /**
   * Register a material for tracking
   */
  trackMaterial(material: THREE.Material): void {
    this.materials.add(material);
  }

  /**
   * Register a texture for tracking
   */
  trackTexture(texture: THREE.Texture): void {
    this.textures.add(texture);
  }

  /**
   * Get memory statistics
   */
  getStats(): {
    geometries: number;
    materials: number;
    textures: number;
    estimatedMemoryMB: number;
  } {
    let estimatedMemory = 0;

    // Estimate geometry memory (rough approximation)
    this.geometries.forEach((geometry) => {
      const positions = geometry.attributes.position;
      if (positions) {
        estimatedMemory += positions.count * positions.itemSize * 4; // 4 bytes per float
      }
    });

    // Estimate texture memory
    this.textures.forEach((texture) => {
      const image = texture.image as HTMLImageElement;
      if (image && image.width && image.height) {
        // RGBA = 4 bytes per pixel
        estimatedMemory += image.width * image.height * 4;

        // Account for mipmaps (~33% more)
        if (texture.generateMipmaps) {
          estimatedMemory *= 1.33;
        }
      }
    });

    return {
      geometries: this.geometries.size,
      materials: this.materials.size,
      textures: this.textures.size,
      estimatedMemoryMB: estimatedMemory / (1024 * 1024),
    };
  }

  /**
   * Dispose all tracked resources
   */
  disposeAll(): void {
    this.geometries.forEach((geometry) => geometry.dispose());
    this.materials.forEach((material) => disposeMaterial(material));
    this.textures.forEach((texture) => texture.dispose());

    this.geometries.clear();
    this.materials.clear();
    this.textures.clear();
  }

  /**
   * Clear tracking without disposing
   */
  clear(): void {
    this.geometries.clear();
    this.materials.clear();
    this.textures.clear();
  }
}

/**
 * Create a cleanup function for React components
 * Returns a function that can be called in useEffect cleanup
 */
export const createCleanupFunction = (
  objects: THREE.Object3D[],
  timers: Array<number | ReturnType<typeof setTimeout>> = [],
  listeners: Array<{ element: Window | HTMLElement | Document; event: string; handler: EventListener }> = []
): (() => void) => {
  return () => {
    // Dispose objects
    objects.forEach((object) => disposeObject(object));

    // Clean up timers
    cleanupTimers(timers);

    // Clean up event listeners
    listeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler);
    });
  };
};

/**
 * Hook-friendly memory manager
 * Use in React components for automatic cleanup
 */
export class ComponentMemoryManager {
  private tracker = new MemoryTracker();
  private timers: Array<number | ReturnType<typeof setTimeout>> = [];
  private listeners: Array<{
    element: Window | HTMLElement | Document;
    event: string;
    handler: EventListener;
  }> = [];

  /**
   * Track a geometry
   */
  trackGeometry(geometry: THREE.BufferGeometry): THREE.BufferGeometry {
    this.tracker.trackGeometry(geometry);
    return geometry;
  }

  /**
   * Track a material
   */
  trackMaterial(material: THREE.Material): THREE.Material {
    this.tracker.trackMaterial(material);
    return material;
  }

  /**
   * Track a texture
   */
  trackTexture(texture: THREE.Texture): THREE.Texture {
    this.tracker.trackTexture(texture);
    return texture;
  }

  /**
   * Track a timer
   */
  trackTimer(timer: number | ReturnType<typeof setTimeout>): number | ReturnType<typeof setTimeout> {
    this.timers.push(timer);
    return timer;
  }

  /**
   * Track an event listener
   */
  trackListener(
    element: Window | HTMLElement | Document,
    event: string,
    handler: EventListener
  ): void {
    this.listeners.push({ element, event, handler });
    element.addEventListener(event, handler);
  }

  /**
   * Get memory statistics
   */
  getStats() {
    return this.tracker.getStats();
  }

  /**
   * Clean up all tracked resources
   */
  cleanup(): void {
    // Dispose tracked resources
    this.tracker.disposeAll();

    // Clean up timers
    cleanupTimers(this.timers);
    this.timers = [];

    // Clean up event listeners
    this.listeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler);
    });
    this.listeners = [];
  }
}

/**
 * Detect memory leaks by comparing before/after snapshots
 */
export const detectMemoryLeaks = (
  before: { geometries: number; materials: number; textures: number },
  after: { geometries: number; materials: number; textures: number }
): boolean => {
  const geometryLeak = after.geometries > before.geometries;
  const materialLeak = after.materials > before.materials;
  const textureLeak = after.textures > before.textures;

  if (geometryLeak || materialLeak || textureLeak) {
    console.warn('Potential memory leak detected:', {
      geometries: after.geometries - before.geometries,
      materials: after.materials - before.materials,
      textures: after.textures - before.textures,
    });
    return true;
  }

  return false;
};

/**
 * Force garbage collection (if available in dev tools)
 */
export const forceGarbageCollection = (): void => {
  if ((window as any).gc) {
    (window as any).gc();
    console.log('Forced garbage collection');
  } else {
    console.warn('Garbage collection not available. Run Chrome with --expose-gc flag.');
  }
};
