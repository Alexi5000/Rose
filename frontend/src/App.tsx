/**
 * Rose - AI Companion
 *
 * Main application component:
 * - WebGL shader background with audio reactivity
 * - Voice session management
 * - Error handling with auto-dismiss
 */

import { useState, useEffect } from 'react';
import ShaderBackgroundWrapper from '@/components/ui/shader-background-wrapper';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

function App() {
  const [error, setError] = useState<string | null>(null);

  // Auto-dismiss error after 5 seconds
  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <ShaderBackgroundWrapper onError={setError}>
        {error && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 w-full max-w-md pointer-events-auto z-50 px-4">
            <Alert variant="destructive" className="relative">
              <AlertTitle>Error</AlertTitle>
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
      </ShaderBackgroundWrapper>
    </div>
  );
}

export default App;
