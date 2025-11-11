import { motion, AnimatePresence } from 'framer-motion';
import { Keyboard, X } from 'lucide-react';
import { useState, useEffect } from 'react';

/**
 * KeyboardHelp Component
 * 
 * Displays keyboard shortcuts and navigation help for accessibility.
 * Can be toggled with '?' key or by clicking the help button.
 * 
 * Requirements: 5.5 - Keyboard accessibility
 */

export const KeyboardHelp = () => {
  const [isOpen, setIsOpen] = useState(false);

  // Handle keyboard shortcut to open help (? key)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && !isOpen) {
        e.preventDefault();
        setIsOpen(true);
      } else if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <>
      {/* Help button */}
      <motion.button
        className="absolute bottom-6 right-6 z-10 w-10 h-10 rounded-full 
                   bg-white/10 backdrop-blur-md border border-white/20 
                   flex items-center justify-center
                   focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50
                   transition-all duration-300"
        whileHover={{ scale: 1.05, opacity: 1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Show keyboard shortcuts"
        title="Keyboard shortcuts (?)"
      >
        <Keyboard className="w-5 h-5 text-white/80" />
      </motion.button>

      {/* Help modal */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Modal content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50
                         w-full max-w-md bg-white/10 backdrop-blur-md
                         border border-white/20 rounded-lg p-6 shadow-2xl"
              role="dialog"
              aria-labelledby="keyboard-help-title"
              aria-modal="true"
            >
              {/* Header */}
              <div className="flex items-center justify-between mb-4">
                <h2
                  id="keyboard-help-title"
                  className="text-white text-lg font-light tracking-wide flex items-center gap-2"
                >
                  <Keyboard className="w-5 h-5" />
                  Keyboard Shortcuts
                </h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 rounded hover:bg-white/10 transition-colors
                           focus:outline-none focus-visible:ring-2 focus-visible:ring-white/50"
                  aria-label="Close keyboard shortcuts"
                >
                  <X className="w-5 h-5 text-white/80" />
                </button>
              </div>

              {/* Shortcuts list */}
              <div className="space-y-4">
                {/* Voice interaction */}
                <div>
                  <h3 className="text-white/90 text-sm font-medium mb-2">
                    Voice Interaction
                  </h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Start recording</span>
                      <div className="flex gap-1">
                        <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                          Space
                        </kbd>
                        <span className="text-white/50">or</span>
                        <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                          Enter
                        </kbd>
                      </div>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Stop recording</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Release key
                      </kbd>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Cancel recording</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Escape
                      </kbd>
                    </li>
                  </ul>
                </div>

                {/* Navigation */}
                <div className="border-t border-white/10 pt-4">
                  <h3 className="text-white/90 text-sm font-medium mb-2">
                    Navigation
                  </h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Move between elements</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Tab
                      </kbd>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Move backwards</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Shift + Tab
                      </kbd>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Activate button</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Enter
                      </kbd>
                    </li>
                  </ul>
                </div>

                {/* Help */}
                <div className="border-t border-white/10 pt-4">
                  <h3 className="text-white/90 text-sm font-medium mb-2">
                    Help
                  </h3>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Show this help</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        ?
                      </kbd>
                    </li>
                    <li className="flex items-center justify-between">
                      <span className="text-white/70">Close dialogs</span>
                      <kbd className="px-2 py-1 bg-white/10 rounded text-white/80 text-xs">
                        Escape
                      </kbd>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Footer note */}
              <div className="mt-6 pt-4 border-t border-white/10">
                <p className="text-white/50 text-xs leading-relaxed">
                  All interactive elements can be accessed using keyboard navigation.
                  Press <kbd className="px-1 py-0.5 bg-white/10 rounded text-white/60">Tab</kbd> to
                  move between elements.
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
};
