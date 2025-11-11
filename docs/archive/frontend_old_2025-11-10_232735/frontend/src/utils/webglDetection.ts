/**
 * WebGL Detection Utility
 * Detects WebGL support and provides detailed information about capabilities
 */

export interface WebGLCapabilities {
  supported: boolean
  version: 1 | 2 | null
  renderer: string | null
  vendor: string | null
  maxTextureSize: number | null
  error: string | null
}

/**
 * Detect WebGL support and capabilities
 * Requirements: 6.5 - Provide graceful fallback for unsupported browsers
 */
export const detectWebGL = (): WebGLCapabilities => {
  const canvas = document.createElement('canvas')
  
  // Try WebGL 2.0 first
  let gl: WebGLRenderingContext | WebGL2RenderingContext | null = null
  let version: 1 | 2 | null = null
  
  try {
    gl = canvas.getContext('webgl2') as WebGL2RenderingContext
    if (gl) {
      version = 2
    }
  } catch (e) {
    // WebGL 2.0 not supported, try WebGL 1.0
  }
  
  // Fallback to WebGL 1.0
  if (!gl) {
    try {
      gl = canvas.getContext('webgl') as WebGLRenderingContext || 
           canvas.getContext('experimental-webgl') as WebGLRenderingContext
      if (gl) {
        version = 1
      }
    } catch (e) {
      // WebGL not supported at all
    }
  }
  
  // If no WebGL support at all
  if (!gl || !version) {
    return {
      supported: false,
      version: null,
      renderer: null,
      vendor: null,
      maxTextureSize: null,
      error: 'WebGL is not supported in your browser'
    }
  }
  
  // Get detailed information
  let renderer: string | null = null
  let vendor: string | null = null
  let maxTextureSize: number | null = null
  
  try {
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info')
    if (debugInfo) {
      renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
      vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL)
    }
    
    maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE)
  } catch (e) {
    console.warn('Could not retrieve WebGL debug info:', e)
  }
  
  // Check if WebGL context is functional
  try {
    gl.clearColor(0, 0, 0, 1)
    gl.clear(gl.COLOR_BUFFER_BIT)
  } catch (e) {
    return {
      supported: false,
      version: null,
      renderer,
      vendor,
      maxTextureSize,
      error: 'WebGL context is not functional'
    }
  }
  
  return {
    supported: true,
    version,
    renderer,
    vendor,
    maxTextureSize,
    error: null
  }
}

/**
 * Check if the detected WebGL capabilities meet minimum requirements
 * Requirements: 6.5 - Detect WebGL support on load
 */
export const meetsMinimumRequirements = (capabilities: WebGLCapabilities): boolean => {
  if (!capabilities.supported) {
    return false
  }
  
  // Require at least WebGL 1.0
  if (!capabilities.version) {
    return false
  }
  
  // Check minimum texture size (at least 2048x2048)
  if (capabilities.maxTextureSize && capabilities.maxTextureSize < 2048) {
    console.warn('WebGL texture size is below minimum requirements:', capabilities.maxTextureSize)
    return false
  }
  
  return true
}

/**
 * Get user-friendly error message based on capabilities
 * Requirements: 6.5 - Display clear error message with recommendations
 */
export const getErrorMessage = (capabilities: WebGLCapabilities): string => {
  if (!capabilities.supported) {
    return capabilities.error || 'WebGL is not supported in your browser'
  }
  
  if (capabilities.maxTextureSize && capabilities.maxTextureSize < 2048) {
    return 'Your graphics hardware does not meet the minimum requirements for this experience'
  }
  
  return 'An unknown error occurred while initializing 3D graphics'
}

/**
 * Get browser-specific recommendations
 * Requirements: 6.5 - Display clear error message with recommendations
 */
export const getBrowserRecommendations = (): string[] => {
  const userAgent = navigator.userAgent.toLowerCase()
  const recommendations: string[] = []
  
  // Detect browser
  const isChrome = userAgent.includes('chrome') && !userAgent.includes('edge')
  const isFirefox = userAgent.includes('firefox')
  const isSafari = userAgent.includes('safari') && !userAgent.includes('chrome')
  const isEdge = userAgent.includes('edge') || userAgent.includes('edg/')
  const isIE = userAgent.includes('trident') || userAgent.includes('msie')
  
  if (isIE) {
    recommendations.push('Internet Explorer is not supported. Please use a modern browser.')
    recommendations.push('Recommended browsers: Chrome, Firefox, Safari, or Edge')
  } else if (isSafari) {
    recommendations.push('Make sure you are using Safari 15 or later')
    recommendations.push('Check that hardware acceleration is enabled in Safari preferences')
  } else if (isFirefox) {
    recommendations.push('Make sure you are using Firefox 90 or later')
    recommendations.push('Check that WebGL is enabled in about:config (webgl.disabled should be false)')
  } else if (isChrome || isEdge) {
    recommendations.push('Make sure you are using the latest version of your browser')
    recommendations.push('Check that hardware acceleration is enabled in browser settings')
    recommendations.push('Try visiting chrome://gpu to see if WebGL is blocked')
  } else {
    recommendations.push('Please use a modern browser such as Chrome, Firefox, Safari, or Edge')
    recommendations.push('Make sure your browser is up to date')
  }
  
  // General recommendations
  recommendations.push('Update your graphics drivers to the latest version')
  recommendations.push('Try disabling browser extensions that might block WebGL')
  
  return recommendations
}
