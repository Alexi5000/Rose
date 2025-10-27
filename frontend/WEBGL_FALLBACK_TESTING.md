# WebGL Fallback Testing Guide

## Manual Testing Instructions

### Test 1: Normal Operation (WebGL Supported)

**Expected Behavior:**
1. App loads with loading screen
2. WebGL detection completes (~100ms)
3. Assets begin loading
4. 3D scene renders normally

**How to Test:**
1. Open the app in a modern browser (Chrome, Firefox, Safari, Edge)
2. Verify the 3D scene loads and renders
3. Check browser console for: `WebGL Detection: { supported: true, version: 2, ... }`

### Test 2: WebGL Disabled in Chrome

**Steps:**
1. Open Chrome
2. Navigate to `chrome://flags`
3. Search for "WebGL"
4. Disable "WebGL" and "WebGL 2.0"
5. Restart Chrome
6. Open the app

**Expected Behavior:**
- WebGLFallback component displays
- Shows error: "WebGL is not supported in your browser"
- Displays Chrome-specific recommendations
- "Try Again" button is available
- "Learn More About WebGL" link works

### Test 3: WebGL Disabled in Firefox

**Steps:**
1. Open Firefox
2. Navigate to `about:config`
3. Search for `webgl.disabled`
4. Set to `true`
5. Reload the app

**Expected Behavior:**
- WebGLFallback component displays
- Shows Firefox-specific recommendations about about:config
- Technical details show WebGL version as "Not supported"

### Test 4: WebGL Disabled in Safari

**Steps:**
1. Open Safari
2. Enable Develop menu (Preferences → Advanced → Show Develop menu)
3. Develop → Experimental Features → Disable WebGL
4. Reload the app

**Expected Behavior:**
- WebGLFallback component displays
- Shows Safari-specific recommendations
- Suggests checking Safari version and hardware acceleration

### Test 5: Retry Functionality

**Steps:**
1. Disable WebGL (any method above)
2. Load the app → WebGLFallback displays
3. Re-enable WebGL in browser settings
4. Click "Try Again" button

**Expected Behavior:**
- Detection runs again
- If WebGL is now available, app proceeds to load 3D scene
- If still unavailable, fallback remains with updated detection

### Test 6: Technical Details

**Steps:**
1. Trigger WebGLFallback (disable WebGL)
2. Click on "Technical Details" section

**Expected Behavior:**
- Section expands
- Shows:
  - WebGL Version
  - Renderer (if available)
  - Vendor (if available)
  - Max Texture Size (if available)

### Test 7: Mobile Browsers

**Test on:**
- iOS Safari
- Chrome Mobile (Android)
- Firefox Mobile (Android)

**Expected Behavior:**
- Modern mobile browsers should support WebGL
- 3D scene should load (may have reduced quality)
- If WebGL not supported, fallback displays correctly on mobile

### Test 8: Internet Explorer

**Steps:**
1. Open Internet Explorer 11 (if available)
2. Load the app

**Expected Behavior:**
- WebGLFallback displays
- Shows specific message: "Internet Explorer is not supported. Please use a modern browser."
- Recommends Chrome, Firefox, Safari, or Edge

## Automated Testing Checklist

### Visual Regression
- [ ] Fallback screen matches design
- [ ] Responsive on mobile, tablet, desktop
- [ ] Animations work smoothly (fade in)
- [ ] Buttons have proper hover states

### Functionality
- [ ] WebGL detection completes in < 200ms
- [ ] Retry button triggers re-detection
- [ ] External links open in new tab
- [ ] Technical details expand/collapse
- [ ] All text is readable and properly formatted

### Accessibility
- [ ] Keyboard navigation works
- [ ] Screen reader announces error message
- [ ] Focus states are visible
- [ ] Color contrast meets WCAG AA standards

### Browser Compatibility
- [ ] Chrome 56+ (WebGL 2.0)
- [ ] Firefox 51+ (WebGL 2.0)
- [ ] Safari 15+ (WebGL 2.0)
- [ ] Edge 79+ (WebGL 2.0)
- [ ] Graceful fallback for older browsers

## Console Logging

When WebGL is supported, you should see:
```
WebGL Detection: {
  supported: true,
  version: 2,
  renderer: "ANGLE (Intel, Intel(R) UHD Graphics...)",
  vendor: "Google Inc. (Intel)",
  maxTextureSize: 16384,
  meetsRequirements: true
}
```

When WebGL is not supported:
```
WebGL Detection: {
  supported: false,
  version: null,
  renderer: null,
  vendor: null,
  maxTextureSize: null,
  meetsRequirements: false
}
```

## Performance Metrics

Expected performance impact:

| Metric | Value |
|--------|-------|
| Detection Time | < 200ms |
| Bundle Size Increase | ~3KB minified |
| Runtime Overhead | None (runs once) |
| Memory Impact | Negligible |

## Known Issues

### Issue: WebGL Context Lost
**Symptom:** 3D scene stops rendering after some time
**Solution:** Not related to fallback; handled by Three.js context restoration

### Issue: False Negative on Some GPUs
**Symptom:** WebGL detected but scene doesn't render
**Solution:** Check minimum texture size requirement (2048x2048)

### Issue: Slow Detection on Some Systems
**Symptom:** Detection takes > 500ms
**Solution:** Normal on some systems; loading screen covers this

## Success Criteria

✅ All tests pass
✅ No console errors
✅ Fallback UI matches design
✅ Browser recommendations are accurate
✅ Retry functionality works
✅ Build completes without errors
✅ TypeScript has no errors
✅ Accessible via keyboard
✅ Responsive on all screen sizes

## Reporting Issues

If you encounter issues during testing:

1. Note the browser and version
2. Check browser console for errors
3. Capture screenshot of fallback screen
4. Note any console warnings
5. Test retry functionality
6. Check if WebGL is actually disabled/unsupported
