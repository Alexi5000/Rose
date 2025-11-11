import { motion } from 'framer-motion';

/**
 * HeroTitle Component
 * 
 * Displays "ROSE THE HEALER SHAMAN" typography at the top center of the viewport.
 * Features clean sans-serif font with wide letter spacing and fade-in animation.
 * Fully responsive with optimized sizing for mobile, tablet, and desktop.
 * 
 * Requirements: 8.1, 8.7, 5.1, 5.5
 */
export const HeroTitle = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
      className="absolute top-8 sm:top-12 left-1/2 -translate-x-1/2 z-10 pointer-events-none px-4"
    >
      <h1 className="text-white text-center select-none">
        <div className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-light tracking-[0.25em] sm:tracking-[0.3em] mb-1 sm:mb-2 drop-shadow-lg">
          ROSE
        </div>
        <div className="text-base sm:text-lg md:text-xl lg:text-2xl xl:text-3xl font-light tracking-[0.15em] sm:tracking-[0.2em] opacity-90 drop-shadow-md">
          THE HEALER SHAMAN
        </div>
      </h1>
    </motion.div>
  );
};
