import { useState, useEffect, useRef, useCallback } from 'react';
import { useFrame, useThree } from '@react-three/fiber';

/**
 * Performance Monitoring Hook
 * 
 * Monitors and manages frame rate and performance metrics:
 * - Target 60fps on desktop, 30fps on mobile
 * - Adaptive quality based on performance
 * - Performance metrics logging
 * 
 * Requirements: 6.2
 */

export interface PerformanceMetrics {
  fps: number;
  frameTime: number; // ms
  drawCalls: number;
  triangles: number;
  geometries: number;
  textures: number;
  programs: number;
  memory?: {
    geometries: number;
    textures: number;
  };
}

export interface PerformanceMonitorOptions {
  targetFPS?: number; // Target frame rate (60 for desktop, 30 for mobile)
  enableAdaptiveQuality?: boolean; // Automatically adjust quality based on performance
  logInterval?: number; // How often to log metrics (ms), 0 to disable
  onPerformanceChange?: (metrics: PerformanceMetrics) => void;
}

export const usePerformanceMonitor = (options: PerformanceMonitorOptions = {}) => {
  const {
    targetFPS = 60,
    enableAdaptiveQuality = true,
    logInterval = 5000,
    onPerformanceChange,
  } = options;

  const { gl } = useThree();
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    frameTime: 16.67,
    drawCalls: 0,
    triangles: 0,
    geometries: 0,
    textures: 0,
    programs: 0,
  });

  const [qualityLevel, setQualityLevel] = useState<'high' | 'medium' | 'low'>('high');
  const [isPerformanceGood, setIsPerformanceGood] = useState(true);

  const frameTimesRef = useRef<number[]>([]);
  const lastLogTimeRef = useRef<number>(0);
  const lastFrameTimeRef = useRef<number>(0);

  // Calculate average FPS from frame times
  const calculateFPS = useCallback((frameTimes: number[]): number => {
    if (frameTimes.length === 0) return 60;

    const avgFrameTime = frameTimes.reduce((a, b) => a + b, 0) / frameTimes.length;
    return Math.round(1000 / avgFrameTime);
  }, []);

  // Get renderer info
  const getRendererInfo = useCallback((): Partial<PerformanceMetrics> => {
    const info = gl.info;

    return {
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      geometries: info.memory.geometries,
      textures: info.memory.textures,
      programs: info.programs?.length || 0,
      memory: {
        geometries: info.memory.geometries,
        textures: info.memory.textures,
      },
    };
  }, [gl]);

  // Determine quality level based on FPS
  const determineQualityLevel = useCallback(
    (fps: number): 'high' | 'medium' | 'low' => {
      const targetThreshold = targetFPS * 0.8; // 80% of target

      if (fps >= targetThreshold) {
        return 'high';
      } else if (fps >= targetFPS * 0.5) {
        return 'medium';
      } else {
        return 'low';
      }
    },
    [targetFPS]
  );

  // Monitor frame rate
  useFrame((_state, delta) => {
    const currentTime = performance.now();
    const frameTime = delta * 1000; // Convert to ms

    // Store frame time
    frameTimesRef.current.push(frameTime);

    // Keep only last 60 frames for FPS calculation
    if (frameTimesRef.current.length > 60) {
      frameTimesRef.current.shift();
    }

    // Update metrics periodically
    if (logInterval > 0 && currentTime - lastLogTimeRef.current >= logInterval) {
      const fps = calculateFPS(frameTimesRef.current);
      const avgFrameTime =
        frameTimesRef.current.reduce((a, b) => a + b, 0) / frameTimesRef.current.length;

      const rendererInfo = getRendererInfo();

      const newMetrics: PerformanceMetrics = {
        fps,
        frameTime: avgFrameTime,
        drawCalls: rendererInfo.drawCalls || 0,
        triangles: rendererInfo.triangles || 0,
        geometries: rendererInfo.geometries || 0,
        textures: rendererInfo.textures || 0,
        programs: rendererInfo.programs || 0,
        memory: rendererInfo.memory,
      };

      setMetrics(newMetrics);

      // Check if performance is good
      const performanceGood = fps >= targetFPS * 0.8;
      setIsPerformanceGood(performanceGood);

      // Adaptive quality adjustment
      if (enableAdaptiveQuality) {
        const newQualityLevel = determineQualityLevel(fps);
        if (newQualityLevel !== qualityLevel) {
          console.log(`Performance: Adjusting quality from ${qualityLevel} to ${newQualityLevel}`);
          setQualityLevel(newQualityLevel);
        }
      }

      // Callback
      onPerformanceChange?.(newMetrics);

      // Log metrics
      console.log('Performance Metrics:', {
        fps: `${fps} fps`,
        frameTime: `${avgFrameTime.toFixed(2)} ms`,
        drawCalls: rendererInfo.drawCalls,
        triangles: rendererInfo.triangles,
        geometries: rendererInfo.geometries,
        textures: rendererInfo.textures,
      });

      lastLogTimeRef.current = currentTime;
    }

    lastFrameTimeRef.current = currentTime;
  });

  // Reset renderer info on unmount
  useEffect(() => {
    return () => {
      gl.info.reset();
    };
  }, [gl]);

  return {
    metrics,
    qualityLevel,
    isPerformanceGood,
    targetFPS,
  };
};

/**
 * Simple FPS counter hook (lighter weight alternative)
 */
export const useFPSCounter = (updateInterval: number = 1000) => {
  const [fps, setFps] = useState(60);
  const frameCountRef = useRef(0);
  const lastUpdateRef = useRef(performance.now());

  useFrame(() => {
    frameCountRef.current++;

    const now = performance.now();
    const elapsed = now - lastUpdateRef.current;

    if (elapsed >= updateInterval) {
      const currentFps = Math.round((frameCountRef.current * 1000) / elapsed);
      setFps(currentFps);

      frameCountRef.current = 0;
      lastUpdateRef.current = now;
    }
  });

  return fps;
};

/**
 * Performance stats component data hook
 * Provides formatted stats for display
 */
export const usePerformanceStats = () => {
  const { gl } = useThree();
  const [stats, setStats] = useState({
    fps: 60,
    drawCalls: 0,
    triangles: 0,
    memory: '0 MB',
  });

  useFrame(() => {
    const info = gl.info;

    // Estimate memory usage (rough approximation)
    const geometryMemory = info.memory.geometries * 0.1; // ~100KB per geometry
    const textureMemory = info.memory.textures * 0.5; // ~500KB per texture
    const totalMemory = geometryMemory + textureMemory;

    setStats({
      fps: Math.round(1000 / 16.67), // Will be updated by frame timing
      drawCalls: info.render.calls,
      triangles: info.render.triangles,
      memory: `${totalMemory.toFixed(1)} MB`,
    });
  });

  return stats;
};
