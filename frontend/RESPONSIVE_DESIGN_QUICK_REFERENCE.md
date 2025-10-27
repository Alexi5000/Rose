# Responsive Design Quick Reference

## Using the Responsive Scene Hook

```typescript
import { useResponsiveScene } from '../hooks/useResponsiveScene';

const MyComponent = () => {
  const {
    viewport,           // 'mobile' | 'tablet' | 'desktop' | 'ultrawide'
    cameraConfig,       // { position: [x, y, z], fov: number }
    quality,            // Quality settings object
    aspectRatio,        // Current aspect ratio (width/height)
    isMobile,           // boolean
    isTablet,           // boolean
    isDesktop,          // boolean
    isPortrait,         // boolean
    isLandscape,        // boolean
    enablePostProcessing, // boolean
    enableShadows,      // boolean
    particleCount,      // number
    waterSubdivision,   // number
  } = useResponsiveScene();
  
  // Use these values to adjust your component
};
```

## Breakpoints

```typescript
const breakpoints = {
  mobile: 768,      // < 768px
  tablet: 1024,     // 768px - 1024px
  desktop: 1440,    // 1024px - 1440px
  ultrawide: 1920,  // >= 1440px
};
```

## Quality Settings by Device

### Mobile
```typescript
{
  shadows: false,
  postProcessing: false,
  particleCount: 200,
  waterSubdivision: 32,
}
```

### Tablet
```typescript
{
  shadows: true,
  postProcessing: true,
  particleCount: 500,
  waterSubdivision: 64,
}
```

### Desktop
```typescript
{
  shadows: true,
  postProcessing: true,
  particleCount: 1000,
  waterSubdivision: 128,
}
```

## Camera Settings by Device

```typescript
const cameraSettings = {
  mobile: { position: [0, 2, 12], fov: 60 },
  tablet: { position: [0, 2, 10], fov: 55 },
  desktop: { position: [0, 2, 8], fov: 50 },
  ultrawide: { position: [0, 2, 8], fov: 45 },
};
```

## Conditional Rendering Examples

### Disable Shadows on Mobile
```typescript
<mesh castShadow={!isMobile} receiveShadow={!isMobile}>
  {/* geometry */}
</mesh>
```

### Use Simple Materials on Mobile
```typescript
{isMobile ? (
  <meshStandardMaterial {...simpleProps} />
) : (
  <shaderMaterial {...advancedProps} />
)}
```

### Adjust Geometry Detail
```typescript
const segments = isMobile ? 8 : 16;
<sphereGeometry args={[radius, segments, segments]} />
```

### Conditional Post-Processing
```typescript
const { enablePostProcessing } = useResponsiveScene();

if (!enablePostProcessing) return null;

return <EffectComposer>{/* effects */}</EffectComposer>;
```

## Touch Optimization Utilities

### Haptic Feedback
```typescript
import { triggerHapticFeedback } from '../utils/touchOptimization';

const handleTouch = () => {
  triggerHapticFeedback(10); // 10ms vibration
  // ... your logic
};
```

### Platform Detection
```typescript
import { isTouchDevice, isIOS, isAndroid } from '../utils/touchOptimization';

if (isTouchDevice()) {
  // Touch-specific logic
}

if (isIOS()) {
  // iOS-specific logic
}

if (isAndroid()) {
  // Android-specific logic
}
```

### Touch Target Sizes
```typescript
import { getOptimalTouchTargetSize } from '../utils/touchOptimization';

const size = getOptimalTouchTargetSize(); // 44 (iOS) or 48 (Android)
```

## Responsive Typography (Tailwind)

```typescript
// Small to large scaling
className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl"

// Letter spacing
className="tracking-[0.25em] sm:tracking-[0.3em]"

// Padding
className="px-4 py-8 sm:py-12"
```

## Performance Best Practices

### 1. Use LOD (Level of Detail)
```typescript
const count = isMobile ? 20 : isTablet ? 35 : 50;
```

### 2. Reduce Geometry Complexity
```typescript
const segments = isMobile ? 8 : 16;
```

### 3. Disable Expensive Effects on Mobile
```typescript
if (isMobile) return null; // Skip expensive component
```

### 4. Use Lower DPR on Mobile
```typescript
<Canvas dpr={isMobile ? [1, 1.5] : [1, 2]}>
```

### 5. Skip Animations on Mobile
```typescript
if (!isMobile) {
  // Perform animation
}
```

## Common Patterns

### Responsive 3D Object
```typescript
const MyObject = () => {
  const { isMobile } = useResponsiveScene();
  const segments = isMobile ? 8 : 16;
  
  return (
    <mesh castShadow={!isMobile}>
      <sphereGeometry args={[1, segments, segments]} />
      {isMobile ? (
        <meshStandardMaterial color="#fff" />
      ) : (
        <shaderMaterial {...customShader} />
      )}
    </mesh>
  );
};
```

### Responsive Particle System
```typescript
const Particles = () => {
  const { particleCount } = useResponsiveScene();
  
  return (
    <instancedMesh args={[undefined, undefined, particleCount]}>
      {/* particle geometry and material */}
    </instancedMesh>
  );
};
```

### Responsive UI Component
```typescript
const MyUI = () => {
  const { isMobile } = useResponsiveScene();
  
  return (
    <div className={`
      ${isMobile ? 'text-sm p-2' : 'text-lg p-4'}
      ${isMobile ? 'bottom-16' : 'bottom-20'}
    `}>
      {/* content */}
    </div>
  );
};
```

## Testing Checklist

- [ ] Test on mobile (< 768px)
- [ ] Test on tablet (768px - 1024px)
- [ ] Test on desktop (> 1024px)
- [ ] Test portrait orientation
- [ ] Test landscape orientation
- [ ] Verify FPS targets (30 mobile, 60 desktop)
- [ ] Check touch interactions
- [ ] Verify text readability
- [ ] Test on iOS Safari
- [ ] Test on Android Chrome
- [ ] Test on desktop browsers

## Debugging Tips

### Check Current Viewport
```typescript
const { viewport } = useResponsiveScene();
console.log('Current viewport:', viewport);
```

### Monitor Performance
```typescript
import { useFrame } from '@react-three/fiber';

useFrame((state) => {
  console.log('FPS:', 1 / state.clock.getDelta());
});
```

### Verify Quality Settings
```typescript
const { quality } = useResponsiveScene();
console.log('Quality settings:', quality);
```

## Resources

- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design Guidelines](https://material.io/design)
- [Three.js Performance Tips](https://threejs.org/docs/#manual/en/introduction/Performance-tips)
- [React Three Fiber Performance](https://docs.pmnd.rs/react-three-fiber/advanced/performance)
