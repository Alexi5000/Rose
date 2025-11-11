# 3D Scene Components

## IceCaveScene

The main 3D scene container using React Three Fiber. This component orchestrates all 3D elements of the ice cave sanctuary.

### Usage

```tsx
import { IceCaveScene } from './components/Scene/IceCaveScene';

function App() {
  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <IceCaveScene />
    </div>
  );
}
```

### Features Implemented (Task 2)

- ✅ R3F Canvas with camera configuration
- ✅ Renderer settings (antialias, pixel ratio)
- ✅ Suspense boundaries for progressive loading
- ✅ Basic lighting rig (ambient, directional, point lights)
- ✅ Responsive camera system (mobile/tablet/desktop/ultrawide)
- ✅ Color palette constants and theme system
- ✅ Material color configurations

### Responsive Camera System

The scene automatically adjusts camera position and FOV based on viewport size:

- **Mobile** (< 768px): position [0, 2, 12], FOV 60°
- **Tablet** (768-1024px): position [0, 2, 10], FOV 55°
- **Desktop** (1024-1440px): position [0, 2, 8], FOV 50°
- **Ultrawide** (> 1440px): position [0, 2, 8], FOV 45°

### Color Palette

All colors from the design document are defined in `config/constants.ts`:

- Ice Cave & Sky: Deep blue (#0a1e3d), Sky blue (#1e4d8b), Ice blue (#4d9fff)
- Warm Accents: Orange (#ff8c42), Pink (#ff6b9d), Candle glow (#ff6b42)
- Aurora: Blue (#4d9fff), Purple (#9d4dff), Green (#4dffaa)

### Next Steps

The following components are placeholders and will be implemented in subsequent tasks:

- Task 3: WaterSurface with animated ripples
- Task 4: RoseAvatar with meditation pose
- Task 5: IceCaveEnvironment with icicles
- Task 6: Igloo with warm glow
- Task 7: OceanHorizon with gradient sky
- Task 8: AuroraEffect with flowing shader
- Task 9: ParticleSystem for atmosphere
- Task 11: PostProcessing effects

## Integration with Existing App

To integrate the 3D scene with the existing voice interaction system, the IceCaveScene should be used as a background layer with UI components overlaid on top.
