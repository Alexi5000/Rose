import { useEffect, useRef } from 'react';
import { ComponentMemoryManager } from '../utils/memoryManagement';

/**
 * Memory Management Hook
 * 
 * Provides automatic memory cleanup for React components
 * Tracks and disposes of Three.js resources, timers, and event listeners
 * 
 * Requirements: 6.3
 */

export const useMemoryManagement = () => {
  const managerRef = useRef<ComponentMemoryManager | null>(null);

  // Initialize manager
  if (!managerRef.current) {
    managerRef.current = new ComponentMemoryManager();
  }

  const manager = managerRef.current;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (managerRef.current) {
        console.log('Cleaning up component memory...');
        const stats = managerRef.current.getStats();
        console.log('Memory stats before cleanup:', stats);
        
        managerRef.current.cleanup();
        managerRef.current = null;
      }
    };
  }, []);

  return {
    trackGeometry: manager.trackGeometry.bind(manager),
    trackMaterial: manager.trackMaterial.bind(manager),
    trackTexture: manager.trackTexture.bind(manager),
    trackTimer: manager.trackTimer.bind(manager),
    trackListener: manager.trackListener.bind(manager),
    getStats: manager.getStats.bind(manager),
  };
};

/**
 * Simpler hook for basic cleanup
 */
export const useCleanup = (cleanup: () => void) => {
  useEffect(() => {
    return cleanup;
  }, [cleanup]);
};
