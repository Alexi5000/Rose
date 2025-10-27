import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { colorPalette } from '../../config/constants';

/**
 * LoadingScreen Component
 * 
 * Beautiful loading screen with gradient background, animated loader icon,
 * progress bar, and "Entering the sanctuary..." message.
 * Implements fade-out transition when loading is complete.
 * Shows detailed asset loading progress with emoji indicators.
 * 
 * Requirements: 6.1, 10.1, 10.2, 10.3, 10.4
 */

interface LoadingScreenProps {
  isLoading: boolean;
  progress?: number; // 0-100
  currentAsset?: string; // Currently loading asset
  phase?: 'critical' | 'secondary' | 'effects' | 'complete'; // Loading phase
}

/**
 * Get emoji for asset type based on file extension or phase
 */
const getAssetEmoji = (assetPath?: string, phase?: string): string => {
  if (!assetPath) {
    // Phase-based emojis
    if (phase === 'critical') return '🎨';
    if (phase === 'secondary') return '🎭';
    if (phase === 'effects') return '✨';
    return '📦';
  }

  const ext = assetPath.split('.').pop()?.toLowerCase();
  if (ext === 'css') return '🎨';
  if (ext === 'glb' || ext === 'gltf') return '🎭';
  if (ext === 'jpg' || ext === 'png' || ext === 'webp') return '🎭';
  if (ext === 'mp3' || ext === 'wav' || ext === 'ogg') return '🎵';
  return '📦';
};

/**
 * Get user-friendly phase name
 */
const getPhaseName = (phase?: string): string => {
  if (phase === 'critical') return 'Loading essential elements';
  if (phase === 'secondary') return 'Loading environmental details';
  if (phase === 'effects') return 'Preparing visual effects';
  if (phase === 'complete') return 'Ready';
  return 'Entering the sanctuary';
};

/**
 * Get asset name from path (filename without extension)
 */
const getAssetName = (assetPath?: string): string => {
  if (!assetPath) return '';
  const filename = assetPath.split('/').pop() || '';
  const nameWithoutExt = filename.split('.')[0];
  // Convert kebab-case or snake_case to Title Case
  return nameWithoutExt
    .replace(/[-_]/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

export const LoadingScreen = ({ 
  isLoading, 
  progress = 0, 
  currentAsset,
  phase 
}: LoadingScreenProps) => {
  const emoji = getAssetEmoji(currentAsset, phase);
  const phaseName = getPhaseName(phase);
  const assetName = getAssetName(currentAsset);

  return (
    <AnimatePresence>
      {isLoading && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1, ease: 'easeInOut' }}
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{
            background: `linear-gradient(to bottom, ${colorPalette.deepBlue} 0%, ${colorPalette.skyBlue} 100%)`,
          }}
        >
          <div className="text-center px-4 max-w-md">
            {/* Animated loader icon */}
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
              className="flex justify-center mb-6"
            >
              <Loader2 className="w-12 h-12 text-white/60 animate-spin" />
            </motion.div>

            {/* Loading message with phase */}
            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="text-white/60 text-sm tracking-wide mb-2"
            >
              {phaseName}
            </motion.p>

            {/* Current asset being loaded with emoji */}
            {assetName && (
              <motion.p
                key={currentAsset} // Re-animate when asset changes
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                transition={{ duration: 0.3 }}
                className="text-white/40 text-xs tracking-wide mb-6 flex items-center justify-center gap-2"
              >
                <span className="text-base">{emoji}</span>
                <span>{assetName}</span>
              </motion.p>
            )}

            {/* Progress bar */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="w-64 h-1 bg-white/10 rounded-full overflow-hidden mx-auto"
            >
              <motion.div
                className="h-full bg-white/40 rounded-full"
                initial={{ width: '0%' }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3, ease: 'easeOut' }}
              />
            </motion.div>

            {/* Progress percentage */}
            {progress > 0 && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.7, duration: 0.5 }}
                className="text-white/40 text-xs mt-3 tracking-wider"
              >
                {Math.round(progress)}%
              </motion.p>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
