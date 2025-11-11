import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Volume2, VolumeX, Accessibility, X } from 'lucide-react';
import { useState } from 'react';

/**
 * SettingsPanel Component
 * 
 * Minimal, non-intrusive settings panel with subtle icon that fades when not in use.
 * Includes ambient audio volume control and accessibility options.
 * 
 * Requirements: 8.2, 8.3, 8.4, 8.5, 8.6
 */

interface SettingsPanelProps {
  ambientVolume: number;
  onAmbientVolumeChange: (volume: number) => void;
  reducedMotion: boolean;
  onReducedMotionChange: (enabled: boolean) => void;
}

export const SettingsPanel = ({
  ambientVolume,
  onAmbientVolumeChange,
  reducedMotion,
  onReducedMotionChange,
}: SettingsPanelProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const isMuted = ambientVolume === 0;

  const toggleMute = () => {
    onAmbientVolumeChange(isMuted ? 0.5 : 0);
  };

  // Handle keyboard events for settings panel
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape' && isOpen) {
      e.preventDefault();
      setIsOpen(false);
    }
  };

  return (
    <div className="absolute top-6 right-6 z-10" onKeyDown={handleKeyDown}>
      {/* Settings icon button - fades when not in use */}
      <motion.button
        className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-md
                   border border-white/20 flex items-center justify-center
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50
                   transition-all duration-300"
        animate={{
          opacity: isOpen || isHovered ? 1 : 0.3,
        }}
        whileHover={{ scale: 1.05, opacity: 1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        aria-label={isOpen ? 'Close settings' : 'Open settings'}
        aria-expanded={isOpen}
        aria-controls="settings-panel"
      >
        {isOpen ? (
          <X className="w-5 h-5 text-white/80" />
        ) : (
          <Settings className="w-5 h-5 text-white/80" />
        )}
      </motion.button>

      {/* Settings panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            id="settings-panel"
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            className="absolute top-14 right-0 w-72 bg-white/10 backdrop-blur-md
                       border border-white/20 rounded-lg p-4 shadow-xl"
            role="region"
            aria-label="Settings panel"
          >
            <h3 className="text-white text-sm font-light tracking-wide mb-4">
              Settings
            </h3>

            {/* Ambient audio volume control */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <label
                  htmlFor="ambient-volume"
                  className="text-white/80 text-xs tracking-wide"
                >
                  Ambient Audio
                </label>
                <button
                  onClick={toggleMute}
                  className="p-1 rounded hover:bg-white/10 transition-colors
                           focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
                  aria-label={isMuted ? 'Unmute ambient audio' : 'Mute ambient audio'}
                  tabIndex={0}
                >
                  {isMuted ? (
                    <VolumeX className="w-4 h-4 text-white/60" />
                  ) : (
                    <Volume2 className="w-4 h-4 text-white/80" />
                  )}
                </button>
              </div>
              <input
                id="ambient-volume"
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={ambientVolume}
                onChange={(e) => onAmbientVolumeChange(parseFloat(e.target.value))}
                className="w-full h-1 bg-white/20 rounded-lg appearance-none cursor-pointer
                         [&::-webkit-slider-thumb]:appearance-none
                         [&::-webkit-slider-thumb]:w-3
                         [&::-webkit-slider-thumb]:h-3
                         [&::-webkit-slider-thumb]:rounded-full
                         [&::-webkit-slider-thumb]:bg-white
                         [&::-webkit-slider-thumb]:cursor-pointer
                         [&::-moz-range-thumb]:w-3
                         [&::-moz-range-thumb]:h-3
                         [&::-moz-range-thumb]:rounded-full
                         [&::-moz-range-thumb]:bg-white
                         [&::-moz-range-thumb]:border-0
                         [&::-moz-range-thumb]:cursor-pointer"
                aria-label="Ambient audio volume"
              />
              <div className="flex justify-between text-white/40 text-xs mt-1">
                <span>0%</span>
                <span>{Math.round(ambientVolume * 100)}%</span>
                <span>100%</span>
              </div>
            </div>

            {/* Accessibility options */}
            <div className="border-t border-white/10 pt-4">
              <div className="flex items-center mb-2">
                <Accessibility className="w-4 h-4 text-white/60 mr-2" />
                <h4 className="text-white/80 text-xs tracking-wide">
                  Accessibility
                </h4>
              </div>

              {/* Reduced motion toggle */}
              <label className="flex items-center justify-between cursor-pointer group">
                <span className="text-white/70 text-xs">Reduce Motion</span>
                <div className="relative">
                  <input
                    type="checkbox"
                    checked={reducedMotion}
                    onChange={(e) => onReducedMotionChange(e.target.checked)}
                    className="sr-only peer"
                    aria-label="Enable reduced motion"
                  />
                  <div
                    className="w-10 h-5 bg-white/20 rounded-full peer
                               peer-checked:bg-blue-400/50
                               peer-focus:ring-2 peer-focus:ring-white/40
                               transition-colors duration-200"
                  />
                  <div
                    className="absolute left-0.5 top-0.5 w-4 h-4 bg-white rounded-full
                               peer-checked:translate-x-5
                               transition-transform duration-200"
                  />
                </div>
              </label>
              <p className="text-white/40 text-xs mt-1 ml-0">
                Simplifies animations for better accessibility
              </p>
            </div>

            {/* Info text */}
            <div className="mt-4 pt-4 border-t border-white/10">
              <p className="text-white/40 text-xs leading-relaxed">
                Press <kbd className="px-1 py-0.5 bg-white/10 rounded text-white/60">Space</kbd> or{' '}
                <kbd className="px-1 py-0.5 bg-white/10 rounded text-white/60">Enter</kbd> to
                activate voice interaction.{' '}
                Press <kbd className="px-1 py-0.5 bg-white/10 rounded text-white/60">?</kbd> for
                more keyboard shortcuts.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
