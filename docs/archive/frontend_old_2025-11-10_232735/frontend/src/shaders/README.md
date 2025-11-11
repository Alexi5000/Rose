# Shader Documentation

## Water Shader (`waterShader.ts`)

### Overview
Custom GLSL shader for realistic water surface with concentric ripples, sky reflection, and audio-reactive effects.

### Uniforms

| Uniform | Type | Description | Default |
|---------|------|-------------|---------|
| `time` | float | Animation time in seconds | 0 |
| `rippleCenter` | vec2 | UV coordinates of ripple origin (Rose's position) | (0.5, 0.5) |
| `rippleStrength` | float | Intensity of ripple effect | 0.5 |
| `skyColorTop` | vec3 | Top color of sky gradient | #0a1e3d |
| `skyColorHorizon` | vec3 | Horizon color of sky gradient | #ff8c42 |
| `waterColorDeep` | vec3 | Deep water color | #0a1e3d |
| `waterColorShallow` | vec3 | Shallow water color | #4d9fff |

### Vertex Shader Features

#### Concentric Ripple System
```glsl
// Three overlapping sine waves for natural interference
float ripple1 = sin(dist * 20.0 - time * 2.0) * rippleStrength;
float ripple2 = sin(dist * 15.0 - time * 1.5) * rippleStrength * 0.5;
float ripple3 = sin(dist * 10.0 - time * 1.0) * rippleStrength * 0.3;
```

**Wave Frequencies:**
- Primary: 20 cycles, speed 2.0
- Secondary: 15 cycles, speed 1.5, 50% amplitude
- Tertiary: 10 cycles, speed 1.0, 30% amplitude

#### Distance-Based Fade
```glsl
float fade = exp(-dist * 2.5);
float smoothFade = smoothstep(0.0, 0.1, fade) * fade;
```

**Fade Characteristics:**
- Exponential decay for natural dissipation
- Smooth transition at edges
- Ripples visible up to ~1.5 units from center

#### Ambient Wave Motion
```glsl
float baseWave = sin(uv.x * 5.0 + time * 0.5) * 0.02;
baseWave += sin(uv.y * 3.0 + time * 0.3) * 0.02;
```

**Purpose:** Adds subtle background motion for realism when no ripples are active.

### Fragment Shader Features

#### Fresnel Effect
```glsl
float fresnel = pow(1.0 - dot(viewDirection, vec3(0.0, 0.0, 1.0)), 2.0);
```

**Effect:** More sky reflection at grazing angles, more water color when looking straight down.

#### Sky Reflection
```glsl
vec3 skyReflection = mix(skyColorHorizon, skyColorTop, vUv.y);
```

**Gradient:** Vertical gradient from warm horizon to cool sky top.

#### Center Glow
```glsl
float centerGlow = exp(-vDistanceFromCenter * 3.0) * 0.2;
waterColor = mix(waterColor, waterColorShallow, centerGlow);
```

**Effect:** Subtle glow around Rose's position for visual focus.

#### Shimmer Effect
```glsl
float shimmer = sin(vUv.x * 50.0 + time * 2.0) * sin(vUv.y * 50.0 + time * 1.5);
shimmer = shimmer * 0.05 + 0.95;
```

**Effect:** Subtle animated sparkle across water surface.

#### Foam Highlights
```glsl
float foam = smoothstep(0.08, 0.12, vElevation);
finalColor = mix(finalColor, vec3(1.0), foam * 0.3);
```

**Effect:** White highlights at wave peaks for realism.

### Performance Considerations

- **Vertex Displacement:** Calculated per vertex, scales with geometry subdivision
- **Fragment Calculations:** Optimized for mobile GPUs
- **No Texture Lookups:** All effects procedural for better performance
- **Minimal Branching:** Shader uses mix() instead of if/else

### Audio-Reactive Integration

The shader responds to audio through the `rippleStrength` uniform:

```typescript
// In WaterSurface component
const targetStrength = rippleStrength * (1 + audioAmplitude * 1.5);
```

**Response Curve:**
- Silent (amplitude = 0): Base ripple strength
- Speaking (amplitude = 0.5): 1.75x ripple strength
- Loud (amplitude = 1.0): 2.5x ripple strength

### Visual Quality Settings

Subdivision levels affect ripple smoothness:

| Device | Subdivision | Vertices | Performance |
|--------|-------------|----------|-------------|
| Mobile | 32x32 | 1,024 | 30 FPS |
| Tablet | 64x64 | 4,096 | 45 FPS |
| Desktop | 128x128 | 16,384 | 60 FPS |

### Color Palette

```typescript
// Deep water (no ripples)
waterColorDeep: #0a1e3d (RGB: 10, 30, 61)

// Shallow water (ripple peaks)
waterColorShallow: #4d9fff (RGB: 77, 159, 255)

// Sky reflection top
skyColorTop: #0a1e3d (RGB: 10, 30, 61)

// Sky reflection horizon
skyColorHorizon: #ff8c42 (RGB: 255, 140, 66)
```

### Usage Example

```typescript
import { WaterSurface } from './components/Scene/WaterSurface';

<WaterSurface
  rippleStrength={0.5}
  rosePosition={[0, 0]}
  audioAmplitude={0.7}
/>
```

### Future Enhancements

Potential improvements for future iterations:
- [ ] Normal map for micro-detail
- [ ] Caustics effect on cave floor
- [ ] Foam texture for wave peaks
- [ ] Underwater refraction for objects
- [ ] Dynamic reflection probe for environment
- [ ] Multiple ripple sources for conversations

### Debugging

Enable shader debugging in development:

```typescript
// Add to WaterSurface component
if (import.meta.env.DEV) {
  console.log('Ripple Strength:', material.uniforms.rippleStrength.value);
  console.log('Ripple Center:', material.uniforms.rippleCenter.value);
}
```

### References

- [Three.js ShaderMaterial](https://threejs.org/docs/#api/en/materials/ShaderMaterial)
- [GLSL Smoothstep](https://thebookofshaders.com/glossary/?search=smoothstep)
- [Fresnel Effect](https://en.wikipedia.org/wiki/Fresnel_equations)
- [Water Rendering Techniques](https://developer.nvidia.com/gpugems/gpugems/part-i-natural-effects/chapter-1-effective-water-simulation-physical-models)


## Sky Shader (`skyShader.ts`)

### Overview
Custom GLSL shader for creating a smooth vertical gradient sky that transitions from deep blue at the top to warm orange/pink tones at the horizon.

### Uniforms

| Uniform | Type | Description | Default |
|---------|------|-------------|---------|
| `topColor` | vec3 | Deep blue color at the top of the sky | #0a1e3d |
| `midColor` | vec3 | Sky blue color in the middle section | #1e4d8b |
| `horizonColor` | vec3 | Warm pink color at the horizon | #ff6b9d |
| `bottomColor` | vec3 | Warm orange color at the bottom | #ff8c42 |

### Vertex Shader Features

#### World Position Calculation
```glsl
vec4 worldPosition = modelMatrix * vec4(position, 1.0);
vWorldPosition = worldPosition.xyz;
```

**Purpose:** Passes world-space position to fragment shader for gradient calculation based on actual Y position in the scene.

### Fragment Shader Features

#### Multi-Stop Gradient System
```glsl
float h = normalize(vWorldPosition).y; // -1 to 1 range

if (h > 0.4) {
  // Top section: deep blue to sky blue
  float t = smoothstep(0.4, 1.0, h);
  color = mix(midColor, topColor, t);
} else if (h > 0.0) {
  // Middle section: sky blue to warm pink
  float t = smoothstep(0.0, 0.4, h);
  color = mix(horizonColor, midColor, t);
} else {
  // Bottom section: warm pink to warm orange
  float t = smoothstep(-0.2, 0.0, h);
  color = mix(bottomColor, horizonColor, t);
}
```

**Gradient Zones:**
- **Top (h > 0.4):** Deep blue (#0a1e3d) → Sky blue (#1e4d8b)
- **Middle (0.0 < h ≤ 0.4):** Sky blue (#1e4d8b) → Warm pink (#ff6b9d)
- **Bottom (h ≤ 0.0):** Warm pink (#ff6b9d) → Warm orange (#ff8c42)

#### Smoothstep Blending
```glsl
float t = smoothstep(min, max, h);
```

**Effect:** Creates natural, smooth color transitions without visible banding. The smoothstep function provides an S-curve interpolation that looks more organic than linear blending.

### Material Configuration

```typescript
const skyMaterial = new THREE.ShaderMaterial({
  uniforms: { /* color uniforms */ },
  vertexShader: skyShader.vertexShader,
  fragmentShader: skyShader.fragmentShader,
  side: THREE.BackSide, // Render inside of sphere
  depthWrite: false, // Don't write to depth buffer
});
```

**Key Settings:**
- `side: THREE.BackSide` - Renders the inside of the sky sphere so it's visible from within
- `depthWrite: false` - Ensures sky is always rendered behind other objects
- `renderOrder: -1` - Renders first in the render queue

### Geometry Setup

```typescript
<sphereGeometry args={[500, 32, 32]} />
```

**Parameters:**
- **Radius:** 500 units (large enough to encompass entire scene)
- **Width Segments:** 32 (sufficient detail for smooth gradient)
- **Height Segments:** 32 (vertical resolution for gradient transitions)

### Color Palette

```typescript
// Gradient colors from design document
topColor: #0a1e3d     // Deep blue (top of sky)
midColor: #1e4d8b     // Sky blue (middle)
horizonColor: #ff6b9d // Warm pink (horizon)
bottomColor: #ff8c42  // Warm orange (bottom)
```

**Color Theory:**
- Cool blues at top create sense of vastness and calm
- Warm tones at horizon evoke twilight/aurora atmosphere
- Smooth transitions maintain meditative mood

### Performance Considerations

- **No Texture Lookups:** Fully procedural gradient for optimal performance
- **Simple Math:** Only basic interpolation and smoothstep operations
- **Static Geometry:** Sky sphere doesn't animate, reducing GPU load
- **Depth Optimization:** `depthWrite: false` prevents unnecessary depth buffer writes

### Integration with Scene

The sky shader works in harmony with other scene elements:

1. **Water Reflection:** Water shader samples similar colors for realistic reflection
2. **Atmospheric Fog:** Fog color matches horizon color for seamless blending
3. **Lighting:** Warm key light from horizon direction reinforces gradient
4. **Aurora Effect:** Aurora colors complement the blue/purple tones in the sky

### Usage Example

```typescript
import { OceanHorizon } from './components/Scene/OceanHorizon';

// In IceCaveScene
<OceanHorizon />
```

The component automatically:
- Creates sky dome with gradient shader
- Adds distant ocean plane
- Configures atmospheric fog
- Matches colors from design palette

### Visual Quality

The shader produces:
- **Smooth Transitions:** No visible color banding
- **Natural Atmosphere:** Mimics real twilight/aurora sky
- **Depth Perception:** Gradient enhances sense of space
- **Emotional Tone:** Warm/cool balance creates peaceful mood

### Debugging

Enable shader debugging in development:

```typescript
// Check gradient colors
console.log('Sky Colors:', {
  top: material.uniforms.topColor.value,
  mid: material.uniforms.midColor.value,
  horizon: material.uniforms.horizonColor.value,
  bottom: material.uniforms.bottomColor.value,
});
```

### Future Enhancements

Potential improvements for future iterations:
- [ ] Time-of-day transitions (day/night cycle)
- [ ] Dynamic cloud layer with noise
- [ ] Star field for night mode
- [ ] Sun/moon disc rendering
- [ ] Atmospheric scattering for more realism
- [ ] HDR environment map generation

### References

- [Three.js ShaderMaterial](https://threejs.org/docs/#api/en/materials/ShaderMaterial)
- [GLSL Smoothstep](https://thebookofshaders.com/glossary/?search=smoothstep)
- [Sky Rendering Techniques](https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-16-accurate-atmospheric-scattering)
- [Color Theory in 3D Environments](https://www.gamedeveloper.com/design/color-theory-for-game-designers)


## Aurora Shader (`auroraShader.ts`)

### Overview
Custom GLSL shader for creating an ethereal aurora borealis effect with flowing noise patterns, color mixing, and audio-reactive intensity control.

### Uniforms

| Uniform | Type | Description | Default |
|---------|------|-------------|---------|
| `time` | float | Animation time in seconds | 0 |
| `intensity` | float | Overall brightness/visibility of aurora | 0.6 |
| `color1` | vec3 | Primary aurora color (blue) | #4d9fff |
| `color2` | vec3 | Secondary aurora color (purple) | #9d4dff |
| `color3` | vec3 | Tertiary aurora color (green) | #4dffaa |

### Vertex Shader Features

#### Simple Pass-Through
```glsl
vUv = uv;
vPosition = position;
gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
```

**Purpose:** Passes UV coordinates and position to fragment shader for pattern generation.

### Fragment Shader Features

#### Simplex Noise Function
The shader includes a complete 3D simplex noise implementation for organic, flowing patterns. Simplex noise provides:
- Smooth, continuous gradients
- No directional artifacts
- Better performance than Perlin noise
- Natural-looking aurora waves

#### Multi-Octave Noise Layers
```glsl
vec3 noiseCoord1 = vec3(vUv * 2.0, time * 0.1);
vec3 noiseCoord2 = vec3(vUv * 3.0, time * 0.15);
vec3 noiseCoord3 = vec3(vUv * 1.5, time * 0.08);

float noise1 = snoise(noiseCoord1);
float noise2 = snoise(noiseCoord2);
float noise3 = snoise(noiseCoord3);

float combinedNoise = noise1 * 0.5 + noise2 * 0.3 + noise3 * 0.2;
```

**Noise Layers:**
- **Layer 1:** Scale 2.0, speed 0.1, weight 50% - Primary large-scale patterns
- **Layer 2:** Scale 3.0, speed 0.15, weight 30% - Medium detail
- **Layer 3:** Scale 1.5, speed 0.08, weight 20% - Subtle variation

**Effect:** Creates complex, organic aurora patterns with multiple scales of detail.

#### Wave-Like Flowing Motion
```glsl
float wave = sin(vUv.x * 3.0 + time * 0.2) * 0.3;
wave += sin(vUv.y * 2.0 - time * 0.15) * 0.2;
```

**Wave Characteristics:**
- Horizontal waves: 3 cycles, speed 0.2, amplitude 0.3
- Vertical waves: 2 cycles, speed 0.15, amplitude 0.2
- Opposite directions create flowing curtain effect

**Purpose:** Adds directional flow to simulate aurora movement across the sky.

#### Ethereal Edge Smoothing
```glsl
aurora = smoothstep(0.2, 0.8, aurora);
```

**Effect:** Creates soft, diffuse edges characteristic of real aurora borealis. No hard boundaries.

#### Vertical Gradient
```glsl
float verticalGradient = smoothstep(0.0, 0.5, vUv.y);
aurora *= verticalGradient;
```

**Effect:** Aurora is stronger at the top, fading toward the bottom for natural appearance.

#### Dynamic Color Mixing
```glsl
vec3 auroraColor = mix(color1, color2, noise1 * 0.5 + 0.5);
auroraColor = mix(auroraColor, color3, noise2 * 0.3 + 0.3);
```

**Color Blending:**
- Base mix between blue and purple based on first noise layer
- Green accent added based on second noise layer
- Creates shifting, iridescent color patterns

**Color Palette:**
- Blue (#4d9fff): Primary color, cool and calming
- Purple (#9d4dff): Secondary color, mystical and ethereal
- Green (#4dffaa): Accent color, adds vibrancy

#### Shimmer Effect
```glsl
float shimmer = sin(vUv.x * 20.0 + time * 2.0) * sin(vUv.y * 15.0 + time * 1.5);
shimmer = shimmer * 0.1 + 0.9;
auroraColor *= shimmer;
```

**Effect:** Subtle animated sparkle across aurora surface, mimicking atmospheric scintillation.

#### Edge Fade
```glsl
float edgeFade = smoothstep(0.0, 0.1, vUv.x) * smoothstep(1.0, 0.9, vUv.x);
alpha *= edgeFade;
```

**Effect:** Fades aurora at left and right edges for seamless blending with scene.

### Material Configuration

```typescript
const material = new THREE.ShaderMaterial({
  uniforms: auroraShader.uniforms,
  vertexShader: auroraShader.vertexShader,
  fragmentShader: auroraShader.fragmentShader,
  transparent: true,
  side: THREE.DoubleSide,
  depthWrite: false,
  blending: THREE.AdditiveBlending, // Key for glow effect
});
```

**Key Settings:**
- `transparent: true` - Enables alpha blending
- `side: THREE.DoubleSide` - Visible from both sides
- `depthWrite: false` - Doesn't occlude objects behind it
- `blending: THREE.AdditiveBlending` - Creates luminous glow effect

### Geometry Setup

```typescript
<planeGeometry args={[30, 12, 64, 32]} />
```

**Parameters:**
- **Width:** 30 units (spans scene width)
- **Height:** 12 units (tall enough for dramatic effect)
- **Width Segments:** 64 (smooth horizontal detail)
- **Height Segments:** 32 (smooth vertical detail)

**Position & Rotation:**
- Position: [0, 8, -15] (above scene, behind Rose)
- Rotation: [-π/6, 0, 0] (tilted to curve over scene)

### Performance Considerations

- **Noise Calculation:** Simplex noise is computationally intensive but necessary for quality
- **Fragment Shader:** All calculations per-pixel, optimized for modern GPUs
- **No Texture Lookups:** Fully procedural for better performance
- **Additive Blending:** Slightly more expensive than alpha blending but essential for glow

**Performance Impact:**
- Desktop: Negligible (~1-2 FPS)
- Mobile: Moderate (~3-5 FPS) - consider reducing geometry subdivision

### Audio-Reactive Integration

The shader responds to audio through the `intensity` uniform with GSAP smoothing:

```typescript
// In AuroraEffect component
const baseIntensity = 0.6;
const targetIntensity = baseIntensity + audioAmplitude * 0.6;

gsap.to(material.uniforms.intensity, {
  value: targetIntensity,
  duration: 0.3,
  ease: 'power2.out',
});
```

**Response Curve:**
- Silent (amplitude = 0): Base intensity 0.6 (subtle presence)
- Speaking (amplitude = 0.5): Intensity 0.9 (enhanced visibility)
- Loud (amplitude = 1.0): Intensity 1.2 (dramatic glow)

**Transition Characteristics:**
- Duration: 0.3 seconds (smooth, not jarring)
- Easing: power2.out (natural deceleration)
- Updates: Per audio frame (real-time response)

### Animation Speed

```typescript
// In useFrame hook
material.uniforms.time.value = state.clock.elapsedTime;
```

**Speed Factors:**
- Noise layer 1: 0.1 (very slow, calming)
- Noise layer 2: 0.15 (slightly faster detail)
- Noise layer 3: 0.08 (slowest, subtle variation)
- Wave motion: 0.2 and 0.15 (gentle flow)

**Design Philosophy:** All animations are intentionally slow to maintain meditative atmosphere.

### Visual Quality Settings

Subdivision levels affect pattern smoothness:

| Device | Width Segments | Height Segments | Performance |
|--------|----------------|-----------------|-------------|
| Mobile | 32 | 16 | 30 FPS |
| Tablet | 48 | 24 | 45 FPS |
| Desktop | 64 | 32 | 60 FPS |

### Integration with Scene

The aurora effect complements other scene elements:

1. **Sky Gradient:** Aurora colors harmonize with blue/purple sky tones
2. **Ice Cave:** Aurora provides atmospheric ceiling lighting
3. **Water Surface:** Aurora reflection could be added to water shader
4. **Rose Avatar:** Aurora intensity increases when Rose speaks
5. **Lighting:** Aurora adds ambient blue/purple fill light

### Usage Example

```typescript
import { AuroraEffect } from './components/Scene/AuroraEffect';

// In IceCaveScene
<AuroraEffect audioAmplitude={0.7} />
```

### Debugging

Enable shader debugging in development:

```typescript
// Add to AuroraEffect component
if (import.meta.env.DEV) {
  console.log('Aurora Intensity:', material.uniforms.intensity.value);
  console.log('Aurora Colors:', {
    color1: material.uniforms.color1.value,
    color2: material.uniforms.color2.value,
    color3: material.uniforms.color3.value,
  });
}
```

### Troubleshooting

**Issue:** Aurora not visible
- Check position and rotation (should be above and behind camera view)
- Verify intensity value (should be > 0.3)
- Ensure transparent: true and blending: AdditiveBlending

**Issue:** Aurora too bright/overwhelming
- Reduce base intensity (default 0.6 → 0.4)
- Reduce alpha multiplier in shader (0.7 → 0.5)
- Adjust color brightness

**Issue:** Performance issues on mobile
- Reduce geometry subdivision (64x32 → 32x16)
- Simplify noise (remove one octave)
- Disable on low-end devices

### Future Enhancements

Potential improvements for future iterations:
- [ ] Multiple aurora layers at different depths
- [ ] Particle system integration (aurora "rays")
- [ ] Color palette variations (red/yellow for different moods)
- [ ] Reflection in water surface
- [ ] Dynamic position based on camera angle
- [ ] Seasonal variations (stronger in winter theme)
- [ ] User-controllable intensity slider

### References

- [Aurora Borealis Physics](https://en.wikipedia.org/wiki/Aurora)
- [Simplex Noise Algorithm](https://en.wikipedia.org/wiki/Simplex_noise)
- [Three.js Additive Blending](https://threejs.org/docs/#api/en/constants/Materials)
- [GLSL Noise Functions](https://gist.github.com/patriciogonzalezvivo/670c22f3966e662d2f83)
- [Real-Time Aurora Rendering](https://developer.nvidia.com/gpugems/gpugems2/part-ii-shading-lighting-and-shadows/chapter-16-accurate-atmospheric-scattering)
