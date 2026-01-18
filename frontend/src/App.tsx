/**
 * 🌹 Rose - AI Grief Counselor
 *
 * Main application component integrating:
 * - WebGL shader background with audio reactivity
 * - Voice session management
 * - Error handling
 * - Dev settings panel (Ctrl+Shift+D)
 */

import { useState, useEffect } from 'react';
import ShaderBackgroundWrapper from '@/components/ui/shader-background-wrapper';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Slider } from '@/components/ui/slider';

function App() {
  // 🚨 Error state
  const [error, setError] = useState<string | null>(null);

  // 🛠️ Dev panel state
  const [showDevPanel, setShowDevPanel] = useState(false);
  const [devSettings, setDevSettings] = useState({
    activationThreshold: 0.02,
    deactivationThreshold: 0.01,
    inactivityTimeout: 20,
  });

  // 🔑 Keyboard shortcut for dev panel (Ctrl+Shift+D)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        console.log('🛠️ Dev panel toggled');
        setShowDevPanel((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // 🔄 Auto-dismiss error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Main voice interface with shader background */}
      <ShaderBackgroundWrapper onError={setError}>
        {/* Phase 8: Error alert with retry button */}
        {error && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 w-full max-w-md pointer-events-auto z-50 px-4">
            <Alert variant="destructive" className="relative">
              <AlertTitle className="flex items-center gap-2">
                <span>⚠️</span>
                <span>Error</span>
              </AlertTitle>
              <AlertDescription className="flex flex-col gap-2">
                <span>{error}</span>
                <button
                  onClick={() => setError(null)}
                  className="self-start text-sm underline hover:no-underline opacity-80 hover:opacity-100 transition-opacity"
                >
                  Dismiss
                </button>
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Dev Settings Dialog */}
        <Dialog open={showDevPanel} onOpenChange={setShowDevPanel}>
          <DialogContent className="sm:max-w-[425px] pointer-events-auto">
            <DialogHeader>
              <DialogTitle>Developer Settings</DialogTitle>
              <DialogDescription>
                Adjust voice detection parameters. Press Ctrl+Shift+D to toggle.
              </DialogDescription>
            </DialogHeader>

            <div className="grid gap-4 py-4">
              {/* Activation Threshold */}
              <div className="grid gap-2">
                <label htmlFor="activation-threshold" className="text-sm font-medium">
                  Activation Threshold: {devSettings.activationThreshold.toFixed(3)}
                </label>
                <Slider
                  id="activation-threshold"
                  min={0.01}
                  max={0.1}
                  step={0.001}
                  value={[devSettings.activationThreshold]}
                  onValueChange={(value) =>
                    setDevSettings((prev) => ({
                      ...prev,
                      activationThreshold: value[0],
                    }))
                  }
                />
                <p className="text-xs text-muted-foreground">
                  Minimum amplitude to detect speech
                </p>
              </div>

              {/* Deactivation Threshold */}
              <div className="grid gap-2">
                <label htmlFor="deactivation-threshold" className="text-sm font-medium">
                  Deactivation Threshold: {devSettings.deactivationThreshold.toFixed(3)}
                </label>
                <Slider
                  id="deactivation-threshold"
                  min={0.001}
                  max={0.05}
                  step={0.001}
                  value={[devSettings.deactivationThreshold]}
                  onValueChange={(value) =>
                    setDevSettings((prev) => ({
                      ...prev,
                      deactivationThreshold: value[0],
                    }))
                  }
                />
                <p className="text-xs text-muted-foreground">
                  Maximum amplitude to consider as silence
                </p>
              </div>

              {/* Inactivity Timeout */}
              <div className="grid gap-2">
                <label htmlFor="inactivity-timeout" className="text-sm font-medium">
                  Inactivity Timeout: {devSettings.inactivityTimeout}s
                </label>
                <Slider
                  id="inactivity-timeout"
                  min={5}
                  max={60}
                  step={5}
                  value={[devSettings.inactivityTimeout]}
                  onValueChange={(value) =>
                    setDevSettings((prev) => ({
                      ...prev,
                      inactivityTimeout: value[0],
                    }))
                  }
                />
                <p className="text-xs text-muted-foreground">
                  Seconds before auto-stop if no speech detected
                </p>
              </div>

              <div className="text-xs text-muted-foreground mt-2">
                <p className="font-medium mb-1">Note:</p>
                <p>
                  Settings are for development only and won't persist. Reload page to
                  reset to defaults.
                </p>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </ShaderBackgroundWrapper>
    </div>
  );
}

export default App;
