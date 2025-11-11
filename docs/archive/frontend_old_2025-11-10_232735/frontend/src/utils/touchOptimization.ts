/**
 * Touch optimization utilities for mobile devices
 * Provides helpers for better touch interactions on iOS and Android
 */

/**
 * Trigger haptic feedback on supported devices
 * @param duration - Duration in milliseconds (default: 10ms)
 */
export const triggerHapticFeedback = (duration: number = 10): void => {
  if ('vibrate' in navigator) {
    navigator.vibrate(duration);
  }
};

/**
 * Prevent default touch behaviors that interfere with custom interactions
 * @param element - HTML element to apply prevention to
 */
export const preventDefaultTouchBehaviors = (element: HTMLElement): void => {
  // Prevent context menu on long press
  element.addEventListener('contextmenu', (e) => e.preventDefault());
  
  // Prevent text selection
  element.style.userSelect = 'none';
  (element.style as any).webkitUserSelect = 'none';
  
  // Prevent tap highlight on iOS
  (element.style as any).webkitTapHighlightColor = 'transparent';
  
  // Prevent callout on iOS
  (element.style as any).webkitTouchCallout = 'none';
};

/**
 * Detect if the device is touch-enabled
 */
export const isTouchDevice = (): boolean => {
  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    (navigator as any).msMaxTouchPoints > 0
  );
};

/**
 * Detect if the device is iOS
 */
export const isIOS = (): boolean => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) && !(window as any).MSStream;
};

/**
 * Detect if the device is Android
 */
export const isAndroid = (): boolean => {
  return /Android/.test(navigator.userAgent);
};

/**
 * Get optimal touch target size based on platform guidelines
 * iOS: 44x44pt minimum, Android: 48x48dp minimum
 */
export const getOptimalTouchTargetSize = (): number => {
  if (isIOS()) {
    return 44; // iOS Human Interface Guidelines
  } else if (isAndroid()) {
    return 48; // Material Design Guidelines
  }
  return 44; // Default to iOS size
};

/**
 * Add passive event listeners for better scroll performance
 * @param element - Element to add listener to
 * @param event - Event name
 * @param handler - Event handler
 */
export const addPassiveEventListener = (
  element: HTMLElement | Window,
  event: string,
  handler: EventListener
): void => {
  element.addEventListener(event, handler, { passive: true });
};

/**
 * Debounce touch events to prevent multiple rapid triggers
 * @param func - Function to debounce
 * @param wait - Wait time in milliseconds
 */
export const debounceTouchEvent = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: number | null = null;
  
  return (...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = window.setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle touch events for performance
 * @param func - Function to throttle
 * @param limit - Time limit in milliseconds
 */
export const throttleTouchEvent = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean = false;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};
