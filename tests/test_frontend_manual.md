# Frontend Manual Testing Checklist

This document provides a comprehensive manual testing checklist for the Rose voice interface frontend across multiple devices and browsers.

## Test Environment Setup

### Required Test Devices
- [ ] Desktop/Laptop (Windows/Mac/Linux)
- [ ] iOS Device (iPhone/iPad)
- [ ] Android Device (Phone/Tablet)

### Required Browsers
- [ ] Chrome (Desktop)
- [ ] Firefox (Desktop)
- [ ] Safari (Desktop - Mac only)
- [ ] Safari (iOS)
- [ ] Chrome (Android)

## Test Scenarios

### 1. Initial Load and Responsive Design

#### Desktop (Chrome, Firefox, Safari)
- [ ] Page loads without errors
- [ ] Voice button is centered and visible
- [ ] Layout is appropriate for desktop screen size
- [ ] No horizontal scrolling
- [ ] All visual elements render correctly
- [ ] Animations are smooth

#### Mobile (iOS Safari, Android Chrome)
- [ ] Page loads without errors on mobile
- [ ] Voice button is appropriately sized for touch
- [ ] Layout adapts to mobile screen size
- [ ] Portrait orientation works correctly
- [ ] Landscape orientation works correctly
- [ ] No content is cut off or hidden
- [ ] Touch targets are at least 44x44 pixels

### 2. Microphone Permissions Flow

#### Desktop Browsers
- [ ] Browser prompts for microphone permission on first use
- [ ] Permission prompt is clear and understandable
- [ ] Granting permission allows recording to proceed
- [ ] Denying permission shows appropriate error message
- [ ] Permission state persists across page reloads
- [ ] Can revoke and re-grant permissions

#### Mobile Browsers
- [ ] iOS Safari prompts for microphone permission
- [ ] Android Chrome prompts for microphone permission
- [ ] Permission prompt appears at appropriate time
- [ ] Granting permission works correctly
- [ ] Denying permission shows user-friendly error
- [ ] Can access browser settings to change permission

### 3. Voice Button Interaction

#### Desktop (Mouse)
- [ ] Button shows idle state initially
- [ ] Hover effect works (if implemented)
- [ ] Click and hold starts recording
- [ ] Visual feedback shows recording state
- [ ] Releasing button stops recording
- [ ] Processing state displays while waiting for response
- [ ] Speaking state displays during audio playback
- [ ] Button returns to idle after interaction completes

#### Mobile (Touch)
- [ ] Touch and hold starts recording
- [ ] Visual feedback is clear on touch
- [ ] Recording continues while finger is held down
- [ ] Releasing finger stops recording
- [ ] No accidental triggers from scrolling
- [ ] Works with different finger sizes
- [ ] Haptic feedback (if implemented) works

#### Keyboard (Accessibility)
- [ ] Button is focusable with Tab key
- [ ] Visual focus indicator is clear
- [ ] Space or Enter key activates recording
- [ ] Keyboard interaction provides same functionality as mouse/touch

### 4. Audio Recording

#### All Platforms
- [ ] Recording starts immediately when button is pressed
- [ ] Audio waveform/visualizer displays during recording (if implemented)
- [ ] Recording captures clear audio
- [ ] Background noise is handled appropriately
- [ ] Recording stops when button is released
- [ ] Short recordings (< 1 second) are handled
- [ ] Long recordings (> 30 seconds) are handled
- [ ] Recording works in quiet environments
- [ ] Recording works in moderately noisy environments

### 5. Audio Playback

#### Desktop Browsers
- [ ] Audio response plays automatically
- [ ] Audio quality is clear and understandable
- [ ] Volume is appropriate
- [ ] Playback completes fully
- [ ] Visual feedback shows playback state
- [ ] Can hear Rose's voice clearly
- [ ] No audio distortion or clipping

#### Mobile Browsers
- [ ] Audio plays on iOS Safari (no autoplay restrictions)
- [ ] Audio plays on Android Chrome
- [ ] Volume is appropriate for mobile speakers
- [ ] Audio plays through headphones if connected
- [ ] Audio plays through Bluetooth devices if connected
- [ ] Playback doesn't interfere with other apps

### 6. Session Management

#### All Platforms
- [ ] Session starts successfully
- [ ] Session ID is maintained across interactions
- [ ] Multiple interactions in same session work correctly
- [ ] Conversation context is preserved
- [ ] Refreshing page starts new session
- [ ] Multiple tabs can have independent sessions

### 7. Error Handling

#### Network Errors
- [ ] Loss of internet connection shows error message
- [ ] Error message is user-friendly
- [ ] Retry option is available
- [ ] Reconnection works after network restored

#### API Errors
- [ ] STT failure shows appropriate message
- [ ] LLM failure shows appropriate message
- [ ] TTS failure falls back to text (if implemented)
- [ ] Error messages don't expose technical details
- [ ] User can retry after error

#### Audio Errors
- [ ] Microphone not available shows error
- [ ] Audio format not supported shows error
- [ ] Empty audio file shows error
- [ ] Audio too large shows error

### 8. Performance

#### Desktop
- [ ] Page loads in < 3 seconds
- [ ] Button responds immediately to interaction
- [ ] No lag during recording
- [ ] Smooth animations throughout
- [ ] No memory leaks during extended use

#### Mobile
- [ ] Page loads in < 5 seconds on 4G
- [ ] Touch response is immediate
- [ ] Battery drain is reasonable
- [ ] App doesn't cause device to overheat
- [ ] Works on older devices (2-3 years old)

### 9. Visual States and Animations

#### All Platforms
- [ ] Idle state is clear and inviting
- [ ] Listening state is visually distinct
- [ ] Processing state shows activity (spinner/animation)
- [ ] Speaking state is recognizable
- [ ] Error state is clearly different
- [ ] Transitions between states are smooth
- [ ] Animations don't cause motion sickness
- [ ] Reduced motion preferences are respected (if implemented)

### 10. Accessibility

#### Screen Readers
- [ ] Button has appropriate ARIA label
- [ ] State changes are announced
- [ ] Error messages are announced
- [ ] All interactive elements are accessible

#### Keyboard Navigation
- [ ] All functionality available via keyboard
- [ ] Focus order is logical
- [ ] Focus is visible
- [ ] No keyboard traps

#### Visual Accessibility
- [ ] Sufficient color contrast
- [ ] Text is readable
- [ ] Icons have text alternatives
- [ ] Works with browser zoom (up to 200%)

### 11. Edge Cases

#### All Platforms
- [ ] Very short audio (< 0.5 seconds) is handled
- [ ] Very long audio (> 60 seconds) is handled
- [ ] Rapid button presses don't break functionality
- [ ] Interrupting playback works correctly
- [ ] Multiple rapid interactions are queued properly
- [ ] Switching tabs during interaction works
- [ ] Minimizing browser during interaction works

### 12. Cross-Browser Compatibility

#### Feature Parity
- [ ] All features work in Chrome
- [ ] All features work in Firefox
- [ ] All features work in Safari (Desktop)
- [ ] All features work in Safari (iOS)
- [ ] All features work in Chrome (Android)
- [ ] Visual appearance is consistent across browsers
- [ ] Performance is acceptable across browsers

## Test Results Template

### Test Session Information
- **Date**: _______________
- **Tester**: _______________
- **Device**: _______________
- **Browser**: _______________
- **Browser Version**: _______________
- **OS**: _______________

### Issues Found
| Issue # | Severity | Description | Steps to Reproduce | Expected | Actual |
|---------|----------|-------------|-------------------|----------|--------|
| 1 | | | | | |
| 2 | | | | | |

### Overall Assessment
- [ ] Pass - All critical functionality works
- [ ] Pass with Minor Issues - Works but has non-critical issues
- [ ] Fail - Critical functionality broken

### Notes
_Additional observations, comments, or recommendations_

---

## Testing Tips

1. **Clear browser cache** between test sessions to ensure fresh state
2. **Test with different microphone devices** (built-in, external, headset)
3. **Test in different network conditions** (WiFi, 4G, 3G, slow connection)
4. **Test at different times of day** to check server load handling
5. **Document all issues** with screenshots/videos when possible
6. **Test with different user personas** (tech-savvy, non-tech-savvy)
7. **Test in different physical environments** (quiet, noisy, outdoor)

## Automated Testing Considerations

While this is a manual testing checklist, consider automating:
- Page load and rendering tests
- API endpoint tests
- Basic interaction flows
- Accessibility checks (using tools like axe-core)
- Performance benchmarks

## Sign-off

- [ ] Desktop Chrome testing complete
- [ ] Desktop Firefox testing complete
- [ ] Desktop Safari testing complete
- [ ] iOS Safari testing complete
- [ ] Android Chrome testing complete
- [ ] All critical issues resolved
- [ ] Ready for production deployment

**Tester Signature**: _______________
**Date**: _______________
