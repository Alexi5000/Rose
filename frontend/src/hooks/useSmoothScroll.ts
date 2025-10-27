import { useEffect, useRef } from 'react';
import Lenis from 'lenis';

/**
 * useSmoothScroll Hook
 * 
 * Sets up Lenis smooth scrolling with momentum-based physics
 * Integrates with React lifecycle for proper cleanup
 * 
 * Requirements: 11.4
 */

interface UseSmoothScrollOptions {
  duration?: number; // Animation duration in seconds
  easing?: (t: number) => number; // Easing function
  enabled?: boolean; // Enable/disable smooth scrolling
}

export const useSmoothScroll = (options: UseSmoothScrollOptions = {}) => {
  const {
    duration = 1.2,
    easing = (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    enabled = true,
  } = options;

  const lenisRef = useRef<Lenis | null>(null);
  const rafIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) return;

    // Initialize Lenis with basic options
    // Note: Lenis v1.3.11 has limited TypeScript support
    // Using minimal configuration for compatibility
    const lenis = new Lenis({
      duration,
      easing,
    } as any);

    lenisRef.current = lenis;

    // Request animation frame loop
    const raf = (time: number) => {
      lenis.raf(time);
      rafIdRef.current = requestAnimationFrame(raf);
    };

    rafIdRef.current = requestAnimationFrame(raf);

    // Cleanup function
    return () => {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
      }
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
    };
  }, [duration, easing, enabled]);

  // Provide Lenis instance and control methods
  const scrollTo = (target: string | number | HTMLElement, options?: any) => {
    if (lenisRef.current) {
      lenisRef.current.scrollTo(target, options);
    }
  };

  const start = () => {
    if (lenisRef.current) {
      lenisRef.current.start();
    }
  };

  const stop = () => {
    if (lenisRef.current) {
      lenisRef.current.stop();
    }
  };

  return {
    lenis: lenisRef.current,
    scrollTo,
    start,
    stop,
  };
};
