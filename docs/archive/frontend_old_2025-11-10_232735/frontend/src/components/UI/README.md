# UI Components

This directory contains all UI components for the immersive 3D frontend experience.

## Components

### HeroTitle
Displays "ROSE THE HEALER SHAMAN" typography at the top center of the viewport with fade-in animation.

**Requirements:** 8.1, 8.7

**Usage:**
```tsx
import { HeroTitle } from './components/UI';

<HeroTitle />
```

### VoiceButton
Circular button with glassmorphism effect for push-to-talk interaction. Supports mouse and touch events with visual states for idle, listening, processing, and speaking.

**Requirements:** 3.1, 3.2, 3.3, 3.4, 3.5, 3.6

**Props:**
- `voiceState`: 'idle' | 'listening' | 'processing' | 'speaking'
- `onStartRecording`: () => void
- `onStopRecording`: () => void
- `disabled?`: boolean
- `audioAmplitude?`: number (0-1, for audio-reactive pulsing)

**Usage:**
```tsx
import { VoiceButton } from './components/UI';

const [voiceState, setVoiceState] = useState<VoiceState>('idle');
const [audioAmplitude, setAudioAmplitude] = useState(0);

<VoiceButton
  voiceState={voiceState}
  onStartRecording={handleStartRecording}
  onStopRecording={handleStopRecording}
  audioAmplitude={audioAmplitude}
/>
```

**Visual Effects:**
- **Idle:** Pulsing glow animation
- **Listening:** Expanded glow with ripple effects
- **Processing:** Spinner animation
- **Speaking:** Audio-reactive pulsing based on amplitude

### LoadingScreen
Beautiful loading screen with gradient background, animated loader icon, progress bar, and "Entering the sanctuary..." message.

**Requirements:** 6.1

**Props:**
- `isLoading`: boolean
- `progress?`: number (0-100)

**Usage:**
```tsx
import { LoadingScreen } from './components/UI';

const [isLoading, setIsLoading] = useState(true);
const [progress, setProgress] = useState(0);

<LoadingScreen isLoading={isLoading} progress={progress} />
```

### SettingsPanel
Minimal, non-intrusive settings panel with ambient audio volume control and accessibility options. The settings icon fades when not in use.

**Requirements:** 8.2, 8.3, 8.4, 8.5, 8.6

**Props:**
- `ambientVolume`: number (0-1)
- `onAmbientVolumeChange`: (volume: number) => void
- `reducedMotion`: boolean
- `onReducedMotionChange`: (enabled: boolean) => void

**Usage:**
```tsx
import { SettingsPanel } from './components/UI';

const [ambientVolume, setAmbientVolume] = useState(0.5);
const [reducedMotion, setReducedMotion] = useState(false);

<SettingsPanel
  ambientVolume={ambientVolume}
  onAmbientVolumeChange={setAmbientVolume}
  reducedMotion={reducedMotion}
  onReducedMotionChange={setReducedMotion}
/>
```

### AudioVisualizer
Audio-reactive effects controller (to be implemented in Task 15).

## Complete Example

```tsx
import { useState } from 'react';
import {
  HeroTitle,
  VoiceButton,
  LoadingScreen,
  SettingsPanel,
  VoiceState,
} from './components/UI';

function App() {
  // Loading state
  const [isLoading, setIsLoading] = useState(true);
  const [loadProgress, setLoadProgress] = useState(0);

  // Voice interaction state
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [audioAmplitude, setAudioAmplitude] = useState(0);

  // Settings state
  const [ambientVolume, setAmbientVolume] = useState(0.5);
  const [reducedMotion, setReducedMotion] = useState(false);

  const handleStartRecording = () => {
    setVoiceState('listening');
    // Start recording logic...
  };

  const handleStopRecording = () => {
    setVoiceState('processing');
    // Process recording logic...
    // Then set to 'speaking' when Rose responds
  };

  return (
    <>
      <LoadingScreen isLoading={isLoading} progress={loadProgress} />
      
      {!isLoading && (
        <>
          <HeroTitle />
          
          <VoiceButton
            voiceState={voiceState}
            onStartRecording={handleStartRecording}
            onStopRecording={handleStopRecording}
            audioAmplitude={audioAmplitude}
          />
          
          <SettingsPanel
            ambientVolume={ambientVolume}
            onAmbientVolumeChange={setAmbientVolume}
            reducedMotion={reducedMotion}
            onReducedMotionChange={setReducedMotion}
          />
        </>
      )}
    </>
  );
}
```

## Styling

All components use Tailwind CSS for styling with the following design principles:

- **Glassmorphism:** `bg-white/10 backdrop-blur-md border border-white/20`
- **Color Palette:** Defined in `src/config/constants.ts`
- **Animations:** Framer Motion for declarative animations
- **Accessibility:** ARIA labels, keyboard navigation, screen reader support

## Accessibility Features

- Keyboard navigation support (Space/Enter for voice button)
- ARIA labels and live regions for screen readers
- Visible focus states
- Reduced motion support
- High contrast text and borders

## Dependencies

- `framer-motion`: Animation library
- `lucide-react`: Icon library
- `tailwindcss`: Utility-first CSS framework
