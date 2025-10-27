# Design Document: Immersive 3D Frontend for Rose the Healer Shaman

## Overview

This design document outlines the technical architecture for creating a cinematic, immersive 3D web experience that transports users into Rose's sacred ice cave sanctuary. The implementation leverages modern web technologies including React Three Fiber, GSAP, Framer Motion, and Lenis Scroll to create a world-class visual experience while maintaining the existing backend voice functionality.

### Design Principles

1. **Cinematic First**: Every frame should look like a beautiful film still
2. **Performance Optimized**: Smooth 60fps on mid-range devices
3. **Seamless Integration**: Connect to existing backend without modifications
4. **Progressive Enhancement**: Graceful degradation for lower-powered devices
5. **Immersive Audio-Visual**: Voice interactions drive environmental responses

## Technology Stack

### Core Framework
- **React 18+**: Component architecture and state management
- **TypeScript**: Type safety and developer experience
- **Vite**: Fast build tooling and HMR

### 3D Rendering
- **Three.js**: WebGL 3D engine
- **React Three Fiber (R3F)**: Declarative Three.js in React
- **@react-three/drei**: Useful R3F helpers and abstractions
- **@react-three/postprocessing**: Post-processing effects (bloom, color grading)

### Animation Libraries
- **GSAP (GreenSock)**: High-performance timeline animations and scroll triggers
- **Framer Motion**: React component animations and gesture handling
- **Lenis**: Smooth momentum-based scrolling

### UI Components
- **ShadCN UI**: Accessible, customizable components built on Radix UI
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Icon library

### Audio Processing
- **Web Audio API**: Audio analysis for visualizations
- **Tone.js** (optional): Advanced audio processing if needed

## Architecture

### High-Level Component Structure

```
src/
├── components/
│   ├── Scene/
│   │   ├── IceCaveScene.tsx          # Main R3F Canvas and scene
│   │   ├── IceCaveEnvironment.tsx    # Icicles, cave walls, lighting
│   │   ├── RoseAvatar.tsx            # Rose meditation figure
│   │   ├── WaterSurface.tsx          # Animated water with ripples
│   │   ├── Igloo.tsx                 # Glowing igloo model
│   │   ├── OceanHorizon.tsx          # Background ocean and sky
│   │   └── AuroraEffect.tsx          # Aurora borealis shader
│   ├── UI/
│   │   ├── HeroTitle.tsx             # "ROSE THE HEALER SHAMAN" typography
│   │   ├── VoiceButton.tsx           # Push-to-talk interaction
│   │   ├── AudioVisualizer.tsx       # Audio-reactive effects controller
│   │   └── LoadingScreen.tsx         # Initial loading experience
│   └── Effects/
│       ├── PostProcessing.tsx        # Bloom, color grading, vignette
│       ├── ParticleSystem.tsx        # Mist, snow particles
│       └── LightingRig.tsx           # Dynamic lighting setup
├── hooks/
│   ├── useVoiceInteraction.ts        # Voice recording and playback
│   ├── useAudioAnalyzer.ts           # Audio frequency analysis
│   ├── useSceneAnimations.ts         # GSAP timeline management
│   └── useResponsiveScene.ts         # Viewport-based scene adjustments
├── shaders/
│   ├── waterShader.ts                # Custom water surface shader
│   ├── auroraShader.ts               # Aurora borealis effect
│   ├── glowShader.ts                 # Soft glow for igloo/candles
│   └── icicleShader.ts               # Ice material with refraction
├── services/
│   ├── apiClient.ts                  # Backend API integration (existing)
│   └── audioService.ts               # Audio processing utilities
└── App.tsx
```


## Detailed Component Design

### 1. IceCaveScene (Main Scene Container)

**Purpose**: Root R3F Canvas component that orchestrates the entire 3D scene.

**Implementation**:
```typescript
<Canvas
  camera={{ position: [0, 2, 8], fov: 50 }}
  gl={{ antialias: true, alpha: false }}
  dpr={[1, 2]} // Adaptive pixel ratio
>
  <Suspense fallback={<LoadingScreen />}>
    <IceCaveEnvironment />
    <RoseAvatar />
    <WaterSurface />
    <Igloo />
    <OceanHorizon />
    <AuroraEffect />
    <LightingRig />
    <ParticleSystem />
    <PostProcessing />
  </Suspense>
</Canvas>
```

**Key Features**:
- Adaptive DPR for performance
- Suspense boundaries for progressive loading
- Camera positioned for cinematic framing
- Color management for accurate color reproduction

### 2. IceCaveEnvironment (Icicles & Cave Walls)

**Purpose**: Create the dramatic ice cave framing with icicles at the top.

**Technical Approach**:
- Use instanced meshes for icicles (performance optimization)
- Custom ice shader with:
  - Subsurface scattering for translucency
  - Fresnel effect for edge glow
  - Normal map for surface detail
  - Refraction for realistic ice look

**Shader Concept**:
```glsl
// Icicle shader with subsurface scattering
uniform vec3 lightPosition;
uniform vec3 baseColor; // Deep blue
uniform float translucency;

// Fresnel for edge glow
float fresnel = pow(1.0 - dot(normal, viewDir), 3.0);
vec3 glowColor = mix(baseColor, vec3(0.3, 0.6, 1.0), fresnel);
```

**Geometry**:
- Procedurally generate icicle positions along top edge
- Vary sizes and rotations for natural look
- Use LOD (Level of Detail) for distant icicles


### 3. RoseAvatar (Meditation Figure)

**Purpose**: Render Rose as an elegant silhouette in meditation pose.

**Technical Approach**:
- Use a simple 3D model or 2D plane with custom shader
- Silhouette effect: render as dark shape with soft edges
- Subtle animations using GSAP:
  - Breathing motion (scale Y axis slightly)
  - Gentle floating (translate Y with sine wave)
  - Rotation sway (rotate Z axis subtly)

**Animation Code**:
```typescript
useFrame((state) => {
  if (roseRef.current) {
    // Breathing
    roseRef.current.scale.y = 1 + Math.sin(state.clock.elapsedTime * 0.5) * 0.02;
    
    // Floating
    roseRef.current.position.y = baseY + Math.sin(state.clock.elapsedTime * 0.3) * 0.05;
    
    // Gentle sway
    roseRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.4) * 0.02;
  }
});
```

**Audio-Reactive Enhancement**:
- When Rose speaks, increase glow intensity
- Pulse scale slightly with audio amplitude
- Enhance water ripples emanating from position

### 4. WaterSurface (Animated Water with Ripples)

**Purpose**: Create realistic water surface with concentric ripples.

**Technical Approach**:
- Use PlaneGeometry with high subdivision for smooth waves
- Custom water shader with:
  - Ripple animation from center (Rose's position)
  - Reflection of sky gradient
  - Refraction distortion
  - Foam/edge effects near shore

**Water Shader**:
```glsl
uniform float time;
uniform vec2 rippleCenter; // Rose's position
uniform float rippleStrength;
uniform sampler2D skyTexture;

// Calculate distance from ripple center
float dist = distance(vUv, rippleCenter);

// Create concentric ripples
float ripple = sin(dist * 20.0 - time * 2.0) * rippleStrength;
ripple *= exp(-dist * 2.0); // Fade with distance

// Displace vertices
vec3 newPosition = position;
newPosition.z += ripple * 0.1;
```

**Audio-Reactive Ripples**:
- Increase `rippleStrength` based on audio amplitude
- Create multiple ripple sources during conversation
- Smooth interpolation using GSAP for natural feel


### 5. Igloo (Warm Glowing Structure)

**Purpose**: Create cozy igloo with warm orange interior glow.

**Technical Approach**:
- 3D model of igloo (can use simple geometry or GLTF model)
- Emissive material for warm glow effect
- Point light inside for volumetric lighting
- Subtle flickering animation for candle-like effect

**Material Setup**:
```typescript
<mesh geometry={iglooGeometry}>
  <meshStandardMaterial
    color="#ff8c42"
    emissive="#ff6b42"
    emissiveIntensity={0.8}
    roughness={0.7}
  />
</mesh>

<pointLight
  position={iglooInteriorPosition}
  color="#ff8c42"
  intensity={2}
  distance={3}
  decay={2}
/>
```

**Flickering Animation**:
```typescript
useFrame((state) => {
  if (lightRef.current) {
    // Subtle candle flicker
    const flicker = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1 
                      + Math.random() * 0.05;
    lightRef.current.intensity = baseIntensity * flicker;
  }
});
```

### 6. OceanHorizon (Background Sky & Water)

**Purpose**: Create serene ocean horizon with gradient sky.

**Technical Approach**:
- Large sphere or dome for sky with gradient shader
- Distant water plane for ocean
- Gradient from deep blue (#0a1e3d) to warm orange/pink (#ff8c42, #ff6b9d)

**Sky Gradient Shader**:
```glsl
uniform vec3 topColor;    // Deep blue
uniform vec3 horizonColor; // Warm orange/pink
uniform vec3 bottomColor;  // Light blue

// Vertical gradient based on Y position
float gradientFactor = normalize(vPosition).y;
vec3 skyColor = mix(horizonColor, topColor, smoothstep(0.0, 0.5, gradientFactor));
skyColor = mix(bottomColor, skyColor, smoothstep(-0.2, 0.0, gradientFactor));
```

**Atmospheric Perspective**:
- Add subtle fog/haze for depth
- Distant objects fade into horizon color
- Use Three.js Fog for automatic distance fading


### 7. AuroraEffect (Aurora Borealis Shader)

**Purpose**: Create ethereal aurora borealis effect in the ice cave ceiling.

**Technical Approach**:
- Animated shader on a curved plane above the scene
- Flowing, wave-like patterns
- Colors: blues, purples, hints of green
- Subtle audio-reactive intensity changes

**Aurora Shader**:
```glsl
uniform float time;
uniform float intensity;
uniform vec3 color1; // #4d9fff
uniform vec3 color2; // #9d4dff
uniform vec3 color3; // #4dffaa

// Flowing noise pattern
float noise1 = snoise(vec3(vUv * 2.0, time * 0.1));
float noise2 = snoise(vec3(vUv * 3.0, time * 0.15));

// Combine noise for aurora waves
float aurora = noise1 * 0.5 + noise2 * 0.5;
aurora = smoothstep(0.3, 0.7, aurora);

// Color mixing
vec3 auroraColor = mix(color1, color2, aurora);
auroraColor = mix(auroraColor, color3, noise2);

// Apply intensity and transparency
gl_FragColor = vec4(auroraColor, aurora * intensity * 0.6);
```

**Audio-Reactive Behavior**:
- Increase intensity during conversation
- Pulse with audio peaks
- Smooth transitions using GSAP

### 8. LightingRig (Scene Lighting)

**Purpose**: Create atmospheric lighting that matches the reference design.

**Light Setup**:
```typescript
// Main ambient light (soft blue)
<ambientLight color="#4d9fff" intensity={0.3} />

// Key light (from horizon, warm)
<directionalLight
  position={[0, 2, -10]}
  color="#ff8c42"
  intensity={1.5}
  castShadow
/>

// Rim light (from above, cool blue)
<directionalLight
  position={[0, 10, 5]}
  color="#4d9fff"
  intensity={0.8}
/>

// Fill light (soft, from left)
<pointLight
  position={[-5, 3, 2]}
  color="#6db3ff"
  intensity={0.5}
/>

// Igloo interior light (warm glow)
<pointLight
  position={iglooPosition}
  color="#ff8c42"
  intensity={2}
  distance={3}
/>
```

**Shadow Configuration**:
- Enable shadows for Rose figure on water
- Soft shadows with high resolution shadow map
- Optimize shadow camera frustum for performance


### 9. PostProcessing (Visual Effects)

**Purpose**: Add cinematic post-processing effects for final polish.

**Effects Stack**:
```typescript
import { EffectComposer, Bloom, ColorGrading, Vignette } from '@react-three/postprocessing';

<EffectComposer>
  {/* Bloom for glowing elements */}
  <Bloom
    intensity={0.8}
    luminanceThreshold={0.3}
    luminanceSmoothing={0.9}
  />
  
  {/* Color grading for cinematic look */}
  <ColorGrading
    brightness={0.05}
    contrast={1.1}
    saturation={1.2}
    temperature={0.1} // Slightly warm
  />
  
  {/* Vignette for focus */}
  <Vignette
    offset={0.3}
    darkness={0.5}
  />
</EffectComposer>
```

**Performance Considerations**:
- Use selective bloom (only glow sources)
- Optimize effect resolution based on device
- Disable on low-end devices

### 10. ParticleSystem (Atmospheric Particles)

**Purpose**: Add subtle mist, snow, or light particles for atmosphere.

**Technical Approach**:
- Use InstancedMesh for thousands of particles
- Simple particle shader with alpha fade
- Gentle floating animation
- Depth-based opacity (fade with distance)

**Particle Implementation**:
```typescript
const particleCount = 1000;
const particles = useMemo(() => {
  const temp = [];
  for (let i = 0; i < particleCount; i++) {
    temp.push({
      position: [
        (Math.random() - 0.5) * 20,
        Math.random() * 10,
        (Math.random() - 0.5) * 20
      ],
      speed: 0.01 + Math.random() * 0.02,
      size: 0.02 + Math.random() * 0.05
    });
  }
  return temp;
}, []);

useFrame((state) => {
  particles.forEach((particle, i) => {
    // Gentle floating motion
    particle.position[1] -= particle.speed;
    if (particle.position[1] < 0) particle.position[1] = 10;
    
    // Update instance matrix
    dummy.position.set(...particle.position);
    dummy.updateMatrix();
    meshRef.current.setMatrixAt(i, dummy.matrix);
  });
  meshRef.current.instanceMatrix.needsUpdate = true;
});
```


## UI Components

### 1. HeroTitle Component

**Purpose**: Display "ROSE THE HEALER SHAMAN" typography.

**Implementation**:
```typescript
<motion.div
  initial={{ opacity: 0, y: -20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 1.5, ease: "easeOut" }}
  className="absolute top-12 left-1/2 -translate-x-1/2 z-10"
>
  <h1 className="text-white text-center">
    <div className="text-6xl font-light tracking-widest">ROSE</div>
    <div className="text-2xl font-light tracking-wider mt-2">
      THE HEALER SHAMAN
    </div>
  </h1>
</motion.div>
```

**Typography**:
- Font: Clean sans-serif (Inter, Montserrat, or similar)
- Weight: Light (300)
- Letter spacing: Wide for elegance
- Color: White with subtle text-shadow for depth
- Animation: Fade in from top on load

### 2. VoiceButton Component

**Purpose**: Elegant push-to-talk interface integrated into the scene.

**Design Approach**:
- Positioned in the water ripple area (bottom center)
- Circular button with subtle glow
- States: idle, listening, processing, speaking
- Framer Motion for smooth state transitions

**Implementation**:
```typescript
<motion.button
  className="absolute bottom-20 left-1/2 -translate-x-1/2 z-10"
  whileHover={{ scale: 1.1 }}
  whileTap={{ scale: 0.95 }}
  animate={{
    boxShadow: isListening 
      ? "0 0 40px rgba(77, 159, 255, 0.8)"
      : "0 0 20px rgba(77, 159, 255, 0.4)"
  }}
  onMouseDown={startRecording}
  onMouseUp={stopRecording}
  onTouchStart={startRecording}
  onTouchEnd={stopRecording}
>
  <div className="w-20 h-20 rounded-full bg-white/10 backdrop-blur-md
                  border-2 border-white/30 flex items-center justify-center">
    {isListening ? <MicIcon /> : <MicOffIcon />}
  </div>
</motion.button>
```

**Visual States**:
- **Idle**: Subtle pulsing glow (GSAP animation)
- **Listening**: Expanded glow, brighter, ripple effect
- **Processing**: Spinner animation
- **Speaking**: Pulsing synchronized with audio


### 3. AudioVisualizer Component

**Purpose**: Analyze audio and drive visual effects in the scene.

**Implementation**:
```typescript
const useAudioAnalyzer = (audioElement: HTMLAudioElement) => {
  const [audioData, setAudioData] = useState({ amplitude: 0, frequency: 0 });
  
  useEffect(() => {
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaElementSource(audioElement);
    
    source.connect(analyser);
    analyser.connect(audioContext.destination);
    
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    const analyze = () => {
      analyser.getByteFrequencyData(dataArray);
      
      // Calculate amplitude (volume)
      const amplitude = dataArray.reduce((a, b) => a + b) / bufferLength / 255;
      
      // Calculate dominant frequency
      const maxIndex = dataArray.indexOf(Math.max(...dataArray));
      const frequency = maxIndex * audioContext.sampleRate / analyser.fftSize;
      
      setAudioData({ amplitude, frequency });
      requestAnimationFrame(analyze);
    };
    
    analyze();
    
    return () => audioContext.close();
  }, [audioElement]);
  
  return audioData;
};
```

**Visual Effect Mapping**:
- **Amplitude** → Water ripple strength, aurora intensity
- **Frequency** → Ripple speed, color shifts
- **Speech detection** → Trigger Rose avatar glow, enhance effects

### 4. LoadingScreen Component

**Purpose**: Beautiful loading experience while assets load.

**Implementation**:
```typescript
<motion.div
  initial={{ opacity: 1 }}
  exit={{ opacity: 0 }}
  transition={{ duration: 1 }}
  className="fixed inset-0 bg-gradient-to-b from-[#0a1e3d] to-[#1e4d8b] 
             flex items-center justify-center z-50"
>
  <div className="text-center">
    <motion.div
      animate={{ scale: [1, 1.2, 1] }}
      transition={{ repeat: Infinity, duration: 2 }}
    >
      <Loader2 className="w-12 h-12 text-white/60 animate-spin" />
    </motion.div>
    <p className="text-white/60 mt-4 text-sm tracking-wide">
      Entering the sanctuary...
    </p>
    <div className="w-64 h-1 bg-white/10 rounded-full mt-4 overflow-hidden">
      <motion.div
        className="h-full bg-white/40"
        initial={{ width: "0%" }}
        animate={{ width: `${loadProgress}%` }}
        transition={{ duration: 0.3 }}
      />
    </div>
  </div>
</motion.div>
```


## Animation Strategy

### GSAP Timeline Orchestration

**Purpose**: Coordinate complex animations across multiple elements.

**Entry Animation Sequence**:
```typescript
useEffect(() => {
  const tl = gsap.timeline();
  
  tl.from(cameraRef.current.position, {
    z: 15,
    duration: 3,
    ease: "power2.out"
  })
  .from(roseRef.current.scale, {
    x: 0, y: 0, z: 0,
    duration: 2,
    ease: "back.out(1.7)"
  }, "-=2")
  .from(waterRippleStrength, {
    value: 0,
    duration: 2,
    ease: "power2.out"
  }, "-=1.5")
  .from(auroraIntensity, {
    value: 0,
    duration: 3,
    ease: "power1.inOut"
  }, "-=2");
  
  return () => tl.kill();
}, []);
```

### Framer Motion for UI

**Purpose**: Handle React component animations declaratively.

**Variants Pattern**:
```typescript
const buttonVariants = {
  idle: {
    scale: 1,
    boxShadow: "0 0 20px rgba(77, 159, 255, 0.4)"
  },
  listening: {
    scale: 1.1,
    boxShadow: "0 0 40px rgba(77, 159, 255, 0.8)",
    transition: { duration: 0.3 }
  },
  speaking: {
    scale: [1, 1.05, 1],
    boxShadow: "0 0 30px rgba(255, 140, 66, 0.6)",
    transition: { repeat: Infinity, duration: 1 }
  }
};

<motion.button
  variants={buttonVariants}
  animate={voiceState}
/>
```

### Lenis Smooth Scrolling

**Purpose**: Enable smooth scrolling for potential multi-section experience.

**Setup**:
```typescript
import Lenis from '@studio-freight/lenis';

useEffect(() => {
  const lenis = new Lenis({
    duration: 1.2,
    easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
    smooth: true,
    smoothTouch: false
  });
  
  function raf(time: number) {
    lenis.raf(time);
    requestAnimationFrame(raf);
  }
  
  requestAnimationFrame(raf);
  
  return () => lenis.destroy();
}, []);
```

**Note**: For single-page experience, Lenis may be optional, but useful for future expansion.


## Responsive Design Strategy

### Viewport Breakpoints

```typescript
const breakpoints = {
  mobile: 768,
  tablet: 1024,
  desktop: 1440,
  ultrawide: 1920
};

const useResponsiveScene = () => {
  const [viewport, setViewport] = useState('desktop');
  
  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      if (width < breakpoints.mobile) setViewport('mobile');
      else if (width < breakpoints.tablet) setViewport('tablet');
      else if (width < breakpoints.desktop) setViewport('desktop');
      else setViewport('ultrawide');
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return viewport;
};
```

### Camera Adjustments

```typescript
const cameraSettings = {
  mobile: { position: [0, 2, 12], fov: 60 },
  tablet: { position: [0, 2, 10], fov: 55 },
  desktop: { position: [0, 2, 8], fov: 50 },
  ultrawide: { position: [0, 2, 8], fov: 45 }
};

<PerspectiveCamera
  makeDefault
  position={cameraSettings[viewport].position}
  fov={cameraSettings[viewport].fov}
/>
```

### Performance Scaling

```typescript
const qualitySettings = {
  mobile: {
    shadows: false,
    postProcessing: false,
    particleCount: 200,
    waterSubdivision: 32
  },
  tablet: {
    shadows: true,
    postProcessing: true,
    particleCount: 500,
    waterSubdivision: 64
  },
  desktop: {
    shadows: true,
    postProcessing: true,
    particleCount: 1000,
    waterSubdivision: 128
  }
};
```

### Touch Interactions

```typescript
// Mobile-friendly voice button
const handleTouchStart = (e: TouchEvent) => {
  e.preventDefault();
  startRecording();
};

const handleTouchEnd = (e: TouchEvent) => {
  e.preventDefault();
  stopRecording();
};

<button
  onTouchStart={handleTouchStart}
  onTouchEnd={handleTouchEnd}
  onMouseDown={startRecording}
  onMouseUp={stopRecording}
>
  Voice Button
</button>
```


## Performance Optimization

### Asset Loading Strategy

**Progressive Loading**:
1. Load critical assets first (Rose, water, basic lighting)
2. Stream in secondary assets (icicles, particles, igloo)
3. Lazy load post-processing effects
4. Use texture compression (KTX2, Basis)

**Implementation**:
```typescript
import { useGLTF, useTexture } from '@react-three/drei';

// Preload critical assets
useGLTF.preload('/models/rose-avatar.glb');
useTexture.preload('/textures/water-normal.jpg');

// Lazy load secondary assets
const Igloo = lazy(() => import('./Igloo'));
const ParticleSystem = lazy(() => import('./ParticleSystem'));
```

### Render Optimization

**Techniques**:
- Use `useMemo` for expensive calculations
- Implement frustum culling for off-screen objects
- Use instanced meshes for repeated geometry (icicles, particles)
- Reduce draw calls by merging static geometry
- Use texture atlases to minimize texture switches

**Example**:
```typescript
const icicles = useMemo(() => {
  const geometry = new ConeGeometry(0.1, 1, 8);
  const material = new MeshStandardMaterial({ color: '#4d9fff' });
  
  return Array.from({ length: 50 }, (_, i) => ({
    position: [
      (i / 50) * 20 - 10,
      5 + Math.random() * 2,
      -5
    ],
    rotation: [0, 0, Math.random() * 0.2],
    scale: 0.5 + Math.random() * 0.5
  }));
}, []);

<instancedMesh args={[geometry, material, icicles.length]}>
  {icicles.map((props, i) => (
    <Instance key={i} {...props} />
  ))}
</instancedMesh>
```

### Frame Rate Management

```typescript
import { useFrame } from '@react-three/fiber';

const targetFPS = 60;
const frameTime = 1000 / targetFPS;
let lastFrameTime = 0;

useFrame((state, delta) => {
  const currentTime = state.clock.elapsedTime * 1000;
  
  if (currentTime - lastFrameTime < frameTime) return;
  
  // Update animations only when needed
  updateWaterRipples(delta);
  updateParticles(delta);
  
  lastFrameTime = currentTime;
});
```

### Memory Management

```typescript
useEffect(() => {
  return () => {
    // Cleanup geometries and materials
    geometry.dispose();
    material.dispose();
    texture.dispose();
  };
}, []);
```


## Backend Integration

### Voice Interaction Flow

**Existing Backend**: The voice processing backend is already implemented and working.

**Frontend Integration**:
```typescript
// services/apiClient.ts (existing, no changes needed)
export const processVoiceInput = async (audioBlob: Blob, sessionId: string) => {
  const formData = new FormData();
  formData.append('audio', audioBlob);
  formData.append('session_id', sessionId);
  
  const response = await fetch('/api/voice/process', {
    method: 'POST',
    body: formData
  });
  
  return response.json(); // { text, audio_url, session_id }
};

// hooks/useVoiceInteraction.ts
const useVoiceInteraction = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  
  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    
    mediaRecorder.ondataavailable = (e) => {
      audioChunksRef.current.push(e.data);
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      audioChunksRef.current = [];
      
      setIsProcessing(true);
      const response = await processVoiceInput(audioBlob, sessionId);
      setIsProcessing(false);
      
      // Play Rose's response
      playAudioResponse(response.audio_url);
    };
    
    mediaRecorder.start();
    mediaRecorderRef.current = mediaRecorder;
    setIsRecording(true);
  };
  
  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };
  
  const playAudioResponse = (audioUrl: string) => {
    const audio = new Audio(audioUrl);
    setIsSpeaking(true);
    
    audio.onended = () => setIsSpeaking(false);
    audio.play();
    
    return audio;
  };
  
  return {
    isRecording,
    isProcessing,
    isSpeaking,
    startRecording,
    stopRecording
  };
};
```

### State Management

**Voice State Machine**:
```typescript
type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

const [voiceState, setVoiceState] = useState<VoiceState>('idle');

// Update visual effects based on state
useEffect(() => {
  switch (voiceState) {
    case 'listening':
      // Enhance water ripples from user position
      setRippleStrength(1.5);
      break;
    case 'speaking':
      // Enhance water ripples from Rose position
      setRippleStrength(2.0);
      setRoseGlow(1.5);
      break;
    default:
      setRippleStrength(0.5);
      setRoseGlow(1.0);
  }
}, [voiceState]);
```


## Color Palette Specification

### Primary Colors

```typescript
const colorPalette = {
  // Ice Cave & Sky
  deepBlue: '#0a1e3d',
  skyBlue: '#1e4d8b',
  iceBlue: '#4d9fff',
  
  // Warm Accents
  warmOrange: '#ff8c42',
  warmPink: '#ff6b9d',
  candleGlow: '#ff6b42',
  
  // Aurora
  auroraBlue: '#4d9fff',
  auroraPurple: '#9d4dff',
  auroraGreen: '#4dffaa',
  
  // UI
  white: '#ffffff',
  whiteTransparent: 'rgba(255, 255, 255, 0.1)',
  whiteBorder: 'rgba(255, 255, 255, 0.3)'
};
```

### Gradient Definitions

```typescript
// Sky gradient (vertical)
const skyGradient = `
  linear-gradient(
    to bottom,
    ${colorPalette.deepBlue} 0%,
    ${colorPalette.skyBlue} 40%,
    ${colorPalette.warmPink} 70%,
    ${colorPalette.warmOrange} 100%
  )
`;

// Water reflection gradient
const waterGradient = `
  linear-gradient(
    to top,
    ${colorPalette.deepBlue} 0%,
    ${colorPalette.iceBlue} 50%,
    ${colorPalette.warmOrange} 100%
  )
`;
```

### Material Color Application

```typescript
// Ice materials
const iceMaterial = {
  color: colorPalette.iceBlue,
  emissive: colorPalette.deepBlue,
  emissiveIntensity: 0.2,
  metalness: 0.1,
  roughness: 0.3,
  transmission: 0.9,
  thickness: 0.5
};

// Igloo glow
const iglooMaterial = {
  color: colorPalette.warmOrange,
  emissive: colorPalette.candleGlow,
  emissiveIntensity: 0.8,
  roughness: 0.7
};

// Rose silhouette
const roseMaterial = {
  color: '#1a1a2e',
  emissive: colorPalette.iceBlue,
  emissiveIntensity: 0.1
};
```


## Accessibility Considerations

### Keyboard Navigation

```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    switch (e.key) {
      case ' ':
      case 'Enter':
        // Space or Enter to activate voice
        if (!isRecording) startRecording();
        break;
      case 'Escape':
        // Escape to cancel
        if (isRecording) stopRecording();
        break;
    }
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [isRecording]);
```

### Screen Reader Support

```typescript
<button
  aria-label={
    isRecording 
      ? "Recording your voice. Release to send." 
      : "Press and hold to speak with Rose"
  }
  aria-pressed={isRecording}
  role="button"
>
  <span className="sr-only">
    {voiceState === 'processing' && "Processing your message..."}
    {voiceState === 'speaking' && "Rose is responding..."}
  </span>
</button>
```

### Reduced Motion Support

```typescript
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const animationConfig = {
  duration: prefersReducedMotion ? 0 : 1,
  ease: prefersReducedMotion ? 'linear' : 'power2.out'
};

// Disable particle effects if reduced motion preferred
{!prefersReducedMotion && <ParticleSystem />}
```

### Focus Management

```typescript
// Ensure voice button is focusable and has visible focus state
<button
  className="focus:outline-none focus:ring-4 focus:ring-blue-400/50"
  tabIndex={0}
>
  Voice Button
</button>
```


## Testing Strategy

### Visual Regression Testing

**Tools**: Percy, Chromatic, or Playwright screenshots

**Test Cases**:
- Initial load state
- Voice button states (idle, listening, processing, speaking)
- Responsive layouts (mobile, tablet, desktop)
- Color accuracy across browsers
- Animation smoothness

### Performance Testing

**Metrics to Monitor**:
- FPS (target: 60fps on desktop, 30fps on mobile)
- Load time (target: < 3s for initial render)
- Memory usage (target: < 200MB)
- Bundle size (target: < 2MB gzipped)

**Tools**:
- Chrome DevTools Performance panel
- Lighthouse
- WebPageTest

### Cross-Browser Testing

**Browsers**:
- Chrome/Edge (Chromium)
- Firefox
- Safari (macOS and iOS)

**WebGL Compatibility**:
- Test fallback for browsers without WebGL 2.0
- Verify shader compilation across browsers
- Test mobile GPU performance

### User Testing Checklist

- [ ] Voice button is intuitive and responsive
- [ ] Audio quality is clear and calming
- [ ] Visual effects enhance rather than distract
- [ ] Loading experience is smooth
- [ ] Mobile touch interactions work reliably
- [ ] Scene composition feels balanced
- [ ] Colors evoke the intended peaceful atmosphere


## Deployment Considerations

### Build Configuration

**Vite Config Optimizations**:
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'three': ['three'],
          'r3f': ['@react-three/fiber', '@react-three/drei'],
          'animations': ['gsap', 'framer-motion']
        }
      }
    }
  },
  optimizeDeps: {
    include: ['three', '@react-three/fiber', '@react-three/drei']
  }
});
```

### Asset Optimization

**3D Models**:
- Use glTF 2.0 format with Draco compression
- Optimize polygon count (target: < 50k triangles total)
- Bake lighting where possible

**Textures**:
- Use KTX2 format with Basis Universal compression
- Maximum texture size: 2048x2048
- Use mipmaps for distant objects

**Audio**:
- Compress ambient audio to MP3 or AAC
- Use streaming for longer audio files

### CDN Strategy

```typescript
// Serve static assets from CDN
const assetBaseUrl = import.meta.env.PROD 
  ? 'https://cdn.example.com/assets'
  : '/assets';

const modelUrl = `${assetBaseUrl}/models/rose-avatar.glb`;
```

### Environment Variables

```env
VITE_API_BASE_URL=https://api.rose-healer.com
VITE_ASSET_CDN_URL=https://cdn.rose-healer.com
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_DEBUG=false
```


## Implementation Phases

### Phase 1: Core 3D Scene (Week 1)
- Set up React Three Fiber project structure
- Implement basic scene with camera and lighting
- Create water surface with simple shader
- Add Rose silhouette (simple geometry)
- Implement basic color palette and sky gradient

**Deliverable**: Static 3D scene matching reference composition

### Phase 2: Environmental Details (Week 2)
- Add icicle framing with ice shader
- Implement igloo with warm glow
- Add ocean horizon and atmospheric perspective
- Create aurora borealis effect
- Implement particle system for atmosphere

**Deliverable**: Complete environmental scene with all visual elements

### Phase 3: Animations & Interactions (Week 3)
- Implement GSAP entry animations
- Add subtle ambient animations (breathing, floating)
- Create audio-reactive water ripples
- Implement voice button with Framer Motion states
- Add post-processing effects (bloom, vignette)

**Deliverable**: Fully animated scene with voice interaction UI

### Phase 4: Backend Integration (Week 4)
- Connect voice button to existing backend API
- Implement audio recording and playback
- Add audio analysis for visualizations
- Sync visual effects with voice states
- Test end-to-end voice flow

**Deliverable**: Fully functional voice interaction experience

### Phase 5: Polish & Optimization (Week 5)
- Optimize performance for target devices
- Implement responsive design adjustments
- Add loading screen and error states
- Conduct cross-browser testing
- Fine-tune colors, lighting, and animations

**Deliverable**: Production-ready immersive experience


## Technical Risks & Mitigations

### Risk 1: Performance on Mobile Devices

**Risk**: Complex 3D scene may not run smoothly on mobile devices.

**Mitigation**:
- Implement aggressive LOD (Level of Detail) system
- Reduce particle count on mobile
- Disable post-processing on low-end devices
- Use simpler shaders with fewer calculations
- Provide 2D fallback experience if needed

### Risk 2: WebGL Compatibility

**Risk**: Some browsers or devices may not support WebGL 2.0.

**Mitigation**:
- Detect WebGL support on load
- Provide graceful fallback to WebGL 1.0
- Create 2D alternative experience for unsupported browsers
- Display clear error message with browser recommendations

### Risk 3: Asset Loading Time

**Risk**: Large 3D models and textures may cause slow initial load.

**Mitigation**:
- Implement progressive loading strategy
- Show beautiful loading screen with progress
- Use texture compression (KTX2, Basis)
- Lazy load non-critical assets
- Implement asset caching strategy

### Risk 4: Audio Synchronization

**Risk**: Visual effects may not sync perfectly with audio.

**Mitigation**:
- Use Web Audio API for precise timing
- Implement audio analysis with low latency
- Buffer visual effects slightly ahead of audio
- Test across different devices and browsers
- Provide manual sync adjustment if needed

### Risk 5: Browser Audio Permissions

**Risk**: Users may deny microphone access or have permission issues.

**Mitigation**:
- Provide clear permission request messaging
- Show helpful error messages for denied permissions
- Offer text-based fallback interaction
- Guide users through browser settings if needed


## Dependencies

### Core Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "three": "^0.160.0",
    "@react-three/fiber": "^8.15.0",
    "@react-three/drei": "^9.95.0",
    "@react-three/postprocessing": "^2.16.0",
    "gsap": "^3.12.0",
    "framer-motion": "^11.0.0",
    "@studio-freight/lenis": "^1.0.0",
    "zustand": "^4.5.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@types/three": "^0.160.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### Optional Dependencies

```json
{
  "optionalDependencies": {
    "tone": "^14.7.0",
    "leva": "^0.9.0",
    "@react-three/rapier": "^1.3.0"
  }
}
```

**Note**: Leva is useful for development to tweak scene parameters in real-time.


## Success Metrics

### Technical Metrics

- **Performance**: 60fps on desktop, 30fps on mobile
- **Load Time**: < 3 seconds to interactive
- **Bundle Size**: < 2MB gzipped
- **Lighthouse Score**: > 90 for Performance
- **Memory Usage**: < 200MB peak

### User Experience Metrics

- **Visual Quality**: Matches reference design aesthetic
- **Interaction Smoothness**: No janky animations or lag
- **Audio Clarity**: Clear voice recording and playback
- **Emotional Impact**: Users report feeling calm and immersed
- **Accessibility**: WCAG 2.1 AA compliance

### Business Metrics

- **Session Duration**: Average time spent in experience
- **Voice Interaction Rate**: % of users who use voice feature
- **Return Rate**: % of users who return for multiple sessions
- **Device Distribution**: Usage across desktop/mobile/tablet
- **Browser Compatibility**: % of users with successful experience

## Conclusion

This design document provides a comprehensive technical blueprint for creating a world-class immersive 3D frontend experience for Rose the Healer Shaman. By leveraging modern web technologies (React Three Fiber, GSAP, Framer Motion) and following best practices for performance and accessibility, we will deliver a stunning, meditative interface that transports users into a sacred healing sanctuary.

The implementation maintains the existing backend voice functionality while elevating the visual experience to match the beautiful reference design provided. The phased approach ensures steady progress with clear deliverables at each stage.

