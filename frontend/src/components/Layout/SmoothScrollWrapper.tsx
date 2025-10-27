import { ReactNode } from 'react';
import { useSmoothScroll } from '../../hooks/useSmoothScroll';

/**
 * SmoothScrollWrapper Component
 * 
 * Wraps the application with Lenis smooth scrolling functionality
 * Provides buttery-smooth momentum-based scrolling for enhanced UX
 * 
 * Note: For single-page immersive experiences, this may be optional.
 * Enable when you have scrollable content or multi-section layouts.
 * 
 * Requirements: 11.4
 */

interface SmoothScrollWrapperProps {
  children: ReactNode;
  enabled?: boolean; // Enable/disable smooth scrolling
}

export const SmoothScrollWrapper = ({ 
  children, 
  enabled = false // Disabled by default for single-page experience
}: SmoothScrollWrapperProps) => {
  // Initialize Lenis smooth scrolling
  useSmoothScroll({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    enabled,
  });

  return <>{children}</>;
};
