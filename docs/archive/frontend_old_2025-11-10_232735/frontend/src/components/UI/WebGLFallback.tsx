import { motion } from 'framer-motion'
import { AlertTriangle, Monitor, RefreshCw } from 'lucide-react'
import type { WebGLCapabilities } from '../../utils/webglDetection'
import { getErrorMessage, getBrowserRecommendations } from '../../utils/webglDetection'

interface WebGLFallbackProps {
  capabilities: WebGLCapabilities
  onRetry?: () => void
}

/**
 * WebGL Fallback Component
 * Displays when WebGL is not supported or doesn't meet minimum requirements
 * Requirements: 6.5 - Provide graceful fallback for unsupported browsers
 */
export const WebGLFallback: React.FC<WebGLFallbackProps> = ({ capabilities, onRetry }) => {
  const errorMessage = getErrorMessage(capabilities)
  const recommendations = getBrowserRecommendations()

  return (
    <div className="fixed inset-0 bg-gradient-to-b from-[#0a1e3d] to-[#1e4d8b] flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-2xl w-full"
      >
        {/* Error Card */}
        <div className="bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 shadow-2xl">
          {/* Icon */}
          <div className="flex justify-center mb-6">
            <div className="w-20 h-20 rounded-full bg-orange-500/20 flex items-center justify-center">
              <AlertTriangle className="w-10 h-10 text-orange-400" />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-3xl font-light text-white text-center mb-4 tracking-wide">
            3D Experience Unavailable
          </h1>

          {/* Error Message */}
          <p className="text-white/80 text-center mb-8 text-lg">
            {errorMessage}
          </p>

          {/* Technical Details (collapsible) */}
          {capabilities.version !== null && (
            <details className="mb-6 bg-white/5 rounded-lg p-4">
              <summary className="text-white/60 text-sm cursor-pointer hover:text-white/80 transition-colors">
                Technical Details
              </summary>
              <div className="mt-4 space-y-2 text-sm text-white/60 font-mono">
                <div>WebGL Version: {capabilities.version || 'Not supported'}</div>
                {capabilities.renderer && <div>Renderer: {capabilities.renderer}</div>}
                {capabilities.vendor && <div>Vendor: {capabilities.vendor}</div>}
                {capabilities.maxTextureSize && (
                  <div>Max Texture Size: {capabilities.maxTextureSize}px</div>
                )}
              </div>
            </details>
          )}

          {/* Recommendations */}
          <div className="bg-white/5 rounded-lg p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <Monitor className="w-5 h-5 text-blue-400" />
              <h2 className="text-white font-medium">What can I do?</h2>
            </div>
            <ul className="space-y-3 text-white/70 text-sm">
              {recommendations.map((recommendation, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-blue-400 mt-1">•</span>
                  <span>{recommendation}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {onRetry && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={onRetry}
                className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-400/30 rounded-lg text-white transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </motion.button>
            )}
            
            <motion.a
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              href="https://get.webgl.org/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-lg text-white transition-colors"
            >
              <Monitor className="w-4 h-4" />
              <span>Learn More About WebGL</span>
            </motion.a>
          </div>

          {/* Alternative Access */}
          <div className="mt-8 pt-6 border-t border-white/10">
            <p className="text-white/50 text-sm text-center">
              You can still access Rose through our{' '}
              <a
                href="/text"
                className="text-blue-400 hover:text-blue-300 underline transition-colors"
              >
                text-only interface
              </a>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-white/40 text-xs">
            Rose the Healer Shaman requires WebGL for the immersive 3D experience
          </p>
        </div>
      </motion.div>
    </div>
  )
}
