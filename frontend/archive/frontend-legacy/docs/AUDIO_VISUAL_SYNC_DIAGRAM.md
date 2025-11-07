# Audio-Visual Synchronization Architecture

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Audio Input Sources                          │
│  • User's microphone (listening state)                          │
│  • Rose's voice response (speaking state)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              useAudioAnalyzer Hook                               │
│  • Web Audio API analyzer                                       │
│  • Extract amplitude (0-1)                                      │
│  • Extract frequency data                                       │
│  • Real-time analysis                                           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  IceCaveScene Component                          │
│  Props: { audioAmplitude, voiceState }                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐
│WaterSurface │  │ RoseAvatar  │  │  Aurora  │  │ LightingRig  │
│             │  │             │  │  Effect  │  │              │
│ Ripples:    │  │ Glow:       │  │ Intensity│  │ Key Light:   │
│ 1.5x boost  │  │ 0.5x boost  │  │ 0.6x     │  │ 0.15x pulse  │
│             │  │             │  │ boost    │  │              │
│ Scale:      │  │ Scale:      │  │          │  │ Fill Light:  │
│ 0.05x pulse │  │ 0.05x pulse │  │ GSAP     │  │ 0.15x pulse  │
│             │  │             │  │ smooth   │  │              │
│ GSAP smooth │  │ Emissive:   │  │          │  │ Rim Light:   │
│ 0.3s ease   │  │ intensity   │  │          │  │ 1.2x boost   │
└─────────────┘  └─────────────┘  └──────────┘  └──────────────┘
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │    Igloo     │
                                                  │              │
                                                  │ Candle:      │
                                                  │ 0.15x pulse  │
                                                  │              │
                                                  │ Flicker +    │
                                                  │ audio pulse  │
                                                  └──────────────┘
```

## Component Synchronization Matrix

| Component      | Audio Effect                    | Multiplier | Transition | State Dependency |
|----------------|---------------------------------|------------|------------|------------------|
| WaterSurface   | Ripple strength increase        | 1.5x       | GSAP 0.3s  | Always active    |
| RoseAvatar     | Glow intensity boost            | 0.5x       | Per-frame  | Always active    |
| RoseAvatar     | Scale pulse                     | 0.05x      | Per-frame  | Always active    |
| RoseAvatar     | Glow sphere opacity             | 0.1x       | Per-frame  | Always active    |
| AuroraEffect   | Intensity increase              | 0.6x       | GSAP 0.3s  | Always active    |
| LightingRig    | Key light pulse                 | 0.15x      | Per-frame  | Speaking only    |
| LightingRig    | Fill light pulse                | 0.15x      | Per-frame  | Speaking only    |
| LightingRig    | Rim light boost                 | 1.2x       | Per-frame  | Listening only   |
| Igloo          | Candle flicker pulse            | 0.15x      | Per-frame  | Always active    |

## Voice State Effects

### Idle State
- Base animations only (breathing, floating, ambient flicker)
- No audio amplitude (audioAmplitude = 0)
- All effects at baseline intensity

### Listening State
- User microphone active
- Audio amplitude from user's voice
- Rim light intensity increased (1.2x)
- Water ripples respond to user's voice
- Cool blue lighting emphasis

### Processing State
- No audio input
- Maintain calm lighting (1.05x multiplier)
- Smooth transition state

### Speaking State
- Rose's voice audio active
- Audio amplitude from Rose's response
- All effects respond to Rose's voice:
  - Water ripples enhanced
  - Rose avatar glows brighter
  - Aurora pulses with voice
  - Warm lighting increased
  - Igloo candle pulses
- Key and fill lights pulse with audio (0.15x)

## GSAP Smooth Interpolation

Components using GSAP for smooth transitions:
- **WaterSurface**: Ripple strength interpolation
- **AuroraEffect**: Intensity interpolation

```typescript
gsap.to(target, {
  value: targetValue,
  duration: 0.3,
  ease: 'power2.out',
});
```

**Benefits:**
- Prevents jarring visual changes
- Maintains calm, meditative atmosphere
- Smooth 300ms transitions
- Power2.out easing for natural feel

## Performance Optimization

### Frame Budget
- Audio analysis: ~0.5ms per frame
- Visual updates: ~0.5ms per frame
- Total impact: ~1ms per frame (< 2% of 60fps budget)

### Optimization Techniques
1. **Single audio analysis per frame** - Shared across all components
2. **Efficient useFrame hooks** - Direct uniform updates
3. **GSAP GPU acceleration** - Hardware-accelerated animations
4. **Calibrated multipliers** - Prevent over-animation

### Memory Management
- No additional textures or geometries
- Uniform updates only (minimal memory impact)
- Proper cleanup in useEffect hooks

## Audio Amplitude Calibration

### Design Philosophy
All multipliers carefully calibrated to maintain peaceful atmosphere:

- **High visibility effects** (water, aurora): Higher multipliers (0.6-1.5x)
- **Subtle enhancements** (lighting, igloo): Lower multipliers (0.15x)
- **Character effects** (Rose glow): Medium multipliers (0.5x)

### Testing Methodology
1. Test with various audio amplitudes (0.0 to 1.0)
2. Verify effects remain subtle and calming
3. Ensure no jarring transitions
4. Validate across different voice types and volumes

## Integration Points

### useVoiceInteraction Hook
```typescript
const { voiceState, audioElement } = useVoiceInteraction();
```

### useAudioAnalyzer Hook
```typescript
const { amplitude, frequency } = useAudioAnalyzer(audioElement);
```

### IceCaveScene Props
```typescript
<IceCaveScene 
  audioAmplitude={amplitude}
  voiceState={voiceState}
/>
```

## Future Enhancements

Potential improvements for future iterations:

1. **Frequency-based effects**
   - Low frequencies → water ripple speed
   - High frequencies → aurora color shifts

2. **Directional audio**
   - Stereo analysis for left/right effects
   - Spatial audio visualization

3. **Beat detection**
   - Pulse effects on strong audio peaks
   - Rhythm-based particle emissions

4. **Adaptive sensitivity**
   - Auto-adjust multipliers based on ambient noise
   - User preference controls

## Conclusion

The audio-visual synchronization system creates a cohesive, immersive experience where every visual element responds naturally to voice interactions. The careful calibration of multipliers and smooth GSAP transitions ensure the effects enhance rather than distract from the healing conversation with Rose.
