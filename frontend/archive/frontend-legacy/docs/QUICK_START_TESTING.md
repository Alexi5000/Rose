# Quick Start: Testing the Production Build

## 🚀 Start the Application (2 Steps)

### Step 1: Start the Backend Server

Open a PowerShell terminal and run:

```powershell
cd C:\TechTide\Apps\Rose
uv run uvicorn ai_companion.interfaces.web.app:app --host 0.0.0.0 --port 8080
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Step 2: Open the Application

Open your browser and go to:
```
http://localhost:8080
```

## ✅ What You Should See

### Loading Screen
1. Beautiful gradient background (deep blue to warm blue)
2. Loading spinner with "Entering the sanctuary..." message
3. Progress bar showing asset loading

### Main Scene (After Loading)
1. **Ice Cave Environment**
   - Dramatic icicles framing the top of the screen
   - Deep blue cave atmosphere
   - Ethereal blue glow

2. **Rose Avatar**
   - Silhouetted figure in meditation pose
   - Centered in the composition
   - Sitting in shallow water
   - Gentle breathing and floating animation

3. **Water Surface**
   - Animated water with concentric ripples
   - Ripples emanating from Rose's position
   - Reflective surface

4. **Warm Igloo**
   - Glowing orange igloo on the left side
   - Warm interior lighting
   - Subtle flickering effect

5. **Ocean Horizon**
   - Gradient sky (deep blue → warm orange/pink)
   - Distant ocean plane
   - Atmospheric fog for depth

6. **Aurora Borealis**
   - Flowing aurora effect in the sky
   - Blue, purple, and green colors
   - Gentle wave-like motion

7. **Atmospheric Particles**
   - Gentle floating particles (mist/snow)
   - Depth-based opacity
   - Adds atmosphere

### UI Elements
1. **Title** (top center): "ROSE THE HEALER SHAMAN"
2. **Voice Button** (bottom center): Circular button with glow
3. **Settings** (top right): Gear icon (fades when not in use)
4. **Keyboard Help** (bottom right): Question mark icon

## 🎤 Testing Voice Interaction

### Using Mouse/Touch
1. **Click and hold** the circular voice button at the bottom
2. **Speak** into your microphone
3. **Release** to send your message
4. Wait for Rose to respond with audio

### Using Keyboard
1. Press and hold **Space** or **Enter**
2. **Speak** into your microphone
3. **Release** to send your message
4. Press **Escape** to cancel recording

### What to Expect
- **Listening**: Button glows brighter, water ripples intensify
- **Processing**: Spinner animation appears
- **Speaking**: Rose glows, water ripples pulse with audio, aurora intensifies

## 🔍 Troubleshooting

### Issue: "Failed to connect" Error

**Cause**: Backend not running

**Solution**:
1. Make sure you started the backend server (Step 1 above)
2. Check that you see "Uvicorn running on http://0.0.0.0:8080"
3. Verify health: http://localhost:8080/api/v1/health

### Issue: Blank Screen or No 3D Scene

**Cause**: WebGL not supported or JavaScript error

**Solution**:
1. Open browser console (F12) and check for errors
2. Verify WebGL support: https://get.webgl.org/
3. Try a different browser (Chrome recommended)
4. Update your graphics drivers

### Issue: Microphone Not Working

**Cause**: Microphone permissions denied

**Solution**:
1. Click the microphone icon in your browser's address bar
2. Allow microphone access
3. Refresh the page
4. Try clicking the voice button again

### Issue: No Audio from Rose

**Cause**: Audio playback blocked or backend issue

**Solution**:
1. Check browser console for errors
2. Verify your speakers/headphones are working
3. Check browser audio settings
4. Ensure backend services are connected (check health endpoint)

### Issue: Slow Performance

**Cause**: Low-end device or too many browser tabs

**Solution**:
1. Close other browser tabs
2. Close other applications
3. The app will automatically reduce quality on lower-end devices
4. Try enabling "Reduced Motion" in settings

## 📊 Performance Expectations

### Desktop
- **FPS**: 60 FPS (smooth animations)
- **Load Time**: < 3 seconds
- **Memory**: < 200MB

### Mobile
- **FPS**: 30 FPS (smooth enough)
- **Load Time**: < 5 seconds
- **Memory**: < 150MB

## 🎨 Visual Quality Check

Compare what you see with the reference design:

### Colors
- ✅ Deep blue ice cave (#0a1e3d to #1e4d8b)
- ✅ Warm orange igloo glow (#ff8c42)
- ✅ Ethereal blue ice glow (#4d9fff)
- ✅ Gradient sky (blue to orange/pink)

### Composition
- ✅ Icicles frame the top (natural vignette)
- ✅ Rose centered as focal point
- ✅ Igloo in left third (rule of thirds)
- ✅ Ocean horizon fades into distance

### Atmosphere
- ✅ Peaceful and calming
- ✅ Sacred sanctuary feeling
- ✅ Cinematic depth
- ✅ Immersive 3D environment

## 🧪 Test Scenarios

### Scenario 1: First Visit
1. Open http://localhost:8080
2. Watch loading screen
3. Observe entry animation (camera zoom, fade-ins)
4. Verify all visual elements are present
5. Check that animations are smooth

### Scenario 2: Voice Interaction
1. Click and hold voice button
2. Say: "Hello Rose, how are you today?"
3. Release button
4. Observe processing state
5. Listen to Rose's response
6. Watch audio-reactive effects (ripples, glow, aurora)

### Scenario 3: Settings
1. Click settings icon (top right)
2. Adjust ambient audio volume
3. Toggle reduced motion
4. Verify changes take effect

### Scenario 4: Keyboard Navigation
1. Press Tab to focus voice button
2. Press Space to start recording
3. Speak your message
4. Release Space to send
5. Press Escape to cancel (if needed)

### Scenario 5: Responsive Design
1. Resize browser window
2. Verify UI elements remain accessible
3. Check that 3D scene adjusts
4. Test on mobile device (if available)

## 📝 What to Report

If you encounter issues, please note:

1. **Browser**: Chrome/Firefox/Safari/Edge (version)
2. **Operating System**: Windows/Mac/Linux (version)
3. **Device**: Desktop/Laptop/Mobile/Tablet
4. **Screen Size**: Width x Height
5. **Error Messages**: Any errors in browser console (F12)
6. **Expected Behavior**: What should happen
7. **Actual Behavior**: What actually happened
8. **Steps to Reproduce**: How to recreate the issue

## 🎯 Success Criteria

The production build is working correctly if:

- ✅ 3D scene loads and renders
- ✅ All visual elements are present
- ✅ Animations are smooth (no stuttering)
- ✅ Voice button responds to clicks
- ✅ Microphone recording works
- ✅ Rose responds with audio
- ✅ Audio-reactive effects work
- ✅ No console errors
- ✅ Performance is acceptable
- ✅ UI is responsive

## 🚦 Current Status

**Backend**: ✅ Running on port 8080  
**Frontend**: ✅ Built and ready  
**Integration**: ✅ Connected  
**Health Check**: ⚠️ Degraded (Qdrant disconnected, but functional)

**Ready to Test**: YES ✅

---

**Need Help?**
- Check PRODUCTION_BUILD_TESTING.md for detailed testing guide
- Check PRODUCTION_TEST_RESULTS.md for test results
- Open browser console (F12) for error messages
- Review backend logs in the terminal
