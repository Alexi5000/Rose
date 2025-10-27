# WebGL Detection and Fallback

This module provides comprehensive WebGL detection and graceful fallback for browsers that don't support WebGL or don't meet minimum requirements.

## Features

### Detection (`webglDetection.ts`)

- **WebGL Version Detection**: Detects WebGL 2.0 and falls back to WebGL 1.0
- **Capability Analysis**: Retrieves detailed information about the graphics hardware
- **Minimum Requirements Check**: Validates that the browser meets minimum texture size requirements (2048x2048)
- **Browser-Specific Recommendations**: Provides tailored guidance based on the user's browser

### Hook (`useWebGLDetection.ts`)

The `useWebGLDetection` hook provides a React-friendly interface for WebGL detection:

```typescript
const { isSupported, isChecking, capabilities, retry } = useWebGLDetection()
```

- `isSupported`: Boolean indicating if WebGL meets minimum requirements
- `isChecking`: Boolean indicating if detection is in progress
- `capabilities`: Detailed WebGL capabilities object
- `retry`: Function to re-run detection

### Fallback UI (`WebGLFallback.tsx`)

A beautiful, user-friendly fallback screen that displays when WebGL is not supported:

- Clear error messaging
- Technical details (collapsible)
- Browser-specific recommendations
- Retry functionality
- Link to WebGL information
- Alternative text-only interface option

## Integration

The WebGL detection is integrated into `App.tsx` and runs before any 3D assets are loaded:

1. **Detection Phase**: Checks WebGL support on app load
2. **Fallback Display**: Shows `WebGLFallback` component if not supported
3. **Asset Loading**: Only loads 3D assets if WebGL is supported
4. **Scene Rendering**: Renders 3D scene only after successful detection

## Browser Support

### Supported Browsers

- Chrome 56+ (WebGL 2.0)
- Firefox 51+ (WebGL 2.0)
- Safari 15+ (WebGL 2.0)
- Edge 79+ (WebGL 2.0)

### Fallback Support

- Chrome 9+ (WebGL 1.0)
- Firefox 4+ (WebGL 1.0)
- Safari 8+ (WebGL 1.0)
- Edge Legacy (WebGL 1.0)

### Not Supported

- Internet Explorer (all versions)
- Very old mobile browsers
- Browsers with WebGL disabled

## Error Messages

The system provides context-aware error messages:

1. **WebGL Not Supported**: Browser doesn't support WebGL at all
2. **Insufficient Hardware**: Graphics hardware doesn't meet minimum requirements
3. **WebGL Disabled**: WebGL is available but disabled in browser settings

## Recommendations

The system provides browser-specific recommendations:

- **Chrome/Edge**: Check hardware acceleration, visit chrome://gpu
- **Firefox**: Check about:config for webgl.disabled setting
- **Safari**: Ensure Safari 15+ and hardware acceleration enabled
- **General**: Update graphics drivers, disable conflicting extensions

## Testing

To test the WebGL fallback:

1. **Disable WebGL in Chrome**: Visit `chrome://flags` and disable WebGL
2. **Firefox**: Set `webgl.disabled` to `true` in `about:config`
3. **Safari**: Disable WebGL in Develop menu (requires enabling Develop menu first)

## Requirements Fulfilled

This implementation fulfills **Requirement 6.5**:

- ✅ Detect WebGL support on load
- ✅ Provide graceful fallback for unsupported browsers
- ✅ Display clear error message with recommendations
