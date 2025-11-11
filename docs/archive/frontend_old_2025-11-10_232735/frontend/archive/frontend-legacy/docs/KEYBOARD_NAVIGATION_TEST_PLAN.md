# Keyboard Navigation Test Plan

## Test Environment Setup

1. Open the application in a web browser
2. Ensure no mouse is used during testing
3. Use only keyboard for all interactions
4. Test with screen reader (optional but recommended)

## Test Cases

### TC1: Initial Page Load and Focus

**Steps:**
1. Load the application
2. Press `Tab` key

**Expected Results:**
- ✅ Skip link appears and receives focus
- ✅ Blue focus indicator is visible
- ✅ Screen reader announces "Skip to main content"

**Status:** [ ] Pass [ ] Fail

---

### TC2: Tab Navigation Order

**Steps:**
1. Load the application
2. Press `Tab` repeatedly to cycle through all interactive elements

**Expected Results:**
- ✅ Focus moves in logical order:
  1. Skip link
  2. Settings button (top-right)
  3. Voice button (center-bottom)
  4. Keyboard help button (bottom-right)
- ✅ Each element shows blue focus indicator
- ✅ No keyboard traps encountered

**Status:** [ ] Pass [ ] Fail

---

### TC3: Voice Button Activation with Space

**Steps:**
1. Tab to voice button
2. Press and hold `Space` key
3. Speak a message
4. Release `Space` key

**Expected Results:**
- ✅ Recording starts when `Space` is pressed
- ✅ Voice button shows "listening" state (blue glow)
- ✅ Recording stops when `Space` is released
- ✅ Processing state is shown
- ✅ Rose's response plays

**Status:** [ ] Pass [ ] Fail

---

### TC4: Voice Button Activation with Enter

**Steps:**
1. Tab to voice button
2. Press and hold `Enter` key
3. Speak a message
4. Release `Enter` key

**Expected Results:**
- ✅ Recording starts when `Enter` is pressed
- ✅ Voice button shows "listening" state
- ✅ Recording stops when `Enter` is released
- ✅ Processing state is shown
- ✅ Rose's response plays

**Status:** [ ] Pass [ ] Fail

---

### TC5: Cancel Recording with Escape

**Steps:**
1. Tab to voice button
2. Press and hold `Space` key to start recording
3. Press `Escape` key while still holding `Space`

**Expected Results:**
- ✅ Recording is cancelled
- ✅ Voice button returns to idle state
- ✅ No processing occurs
- ✅ No error is shown

**Status:** [ ] Pass [ ] Fail

---

### TC6: Settings Panel Keyboard Access

**Steps:**
1. Tab to settings button (top-right)
2. Press `Enter` to open settings
3. Press `Tab` to navigate through settings controls
4. Press `Escape` to close settings

**Expected Results:**
- ✅ Settings panel opens when `Enter` is pressed
- ✅ Focus moves through all controls:
  - Volume slider
  - Mute button
  - Reduced motion toggle
- ✅ All controls are keyboard operable
- ✅ Settings panel closes when `Escape` is pressed

**Status:** [ ] Pass [ ] Fail

---

### TC7: Volume Slider Keyboard Control

**Steps:**
1. Open settings panel
2. Tab to volume slider
3. Use arrow keys to adjust volume:
   - `Right Arrow` / `Up Arrow` to increase
   - `Left Arrow` / `Down Arrow` to decrease

**Expected Results:**
- ✅ Volume increases with right/up arrows
- ✅ Volume decreases with left/down arrows
- ✅ Visual feedback shows volume change
- ✅ Percentage updates in real-time

**Status:** [ ] Pass [ ] Fail

---

### TC8: Mute Button Keyboard Access

**Steps:**
1. Open settings panel
2. Tab to mute button
3. Press `Enter` or `Space` to toggle mute

**Expected Results:**
- ✅ Mute button toggles on/off
- ✅ Icon changes between Volume2 and VolumeX
- ✅ Volume slider reflects muted state
- ✅ Focus indicator visible on button

**Status:** [ ] Pass [ ] Fail

---

### TC9: Reduced Motion Toggle

**Steps:**
1. Open settings panel
2. Tab to reduced motion toggle
3. Press `Space` to toggle

**Expected Results:**
- ✅ Toggle switches on/off
- ✅ Visual feedback shows state change
- ✅ Animations are reduced when enabled
- ✅ Focus indicator visible on toggle

**Status:** [ ] Pass [ ] Fail

---

### TC10: Keyboard Help Dialog

**Steps:**
1. Press `?` key (Shift + /)
2. Review keyboard shortcuts
3. Press `Escape` to close

**Expected Results:**
- ✅ Help dialog opens when `?` is pressed
- ✅ All keyboard shortcuts are listed
- ✅ Dialog is readable and well-organized
- ✅ Dialog closes when `Escape` is pressed
- ✅ Focus returns to previous element

**Status:** [ ] Pass [ ] Fail

---

### TC11: Keyboard Help Button

**Steps:**
1. Tab to keyboard help button (bottom-right)
2. Press `Enter` to open help
3. Tab through help dialog
4. Press close button with `Enter`

**Expected Results:**
- ✅ Help dialog opens
- ✅ Focus moves through dialog elements
- ✅ Close button is keyboard accessible
- ✅ Dialog closes when close button is activated

**Status:** [ ] Pass [ ] Fail

---

### TC12: Global Keyboard Shortcuts (Not in Input)

**Steps:**
1. Ensure no input field is focused
2. Press `Space` key

**Expected Results:**
- ✅ Voice button activates (starts recording)
- ✅ No page scroll occurs
- ✅ Default browser behavior is prevented

**Status:** [ ] Pass [ ] Fail

---

### TC13: Keyboard Shortcuts in Input Fields

**Steps:**
1. Open settings panel
2. Focus on volume slider (input element)
3. Press `Space` key

**Expected Results:**
- ✅ Voice button does NOT activate
- ✅ Slider control works normally
- ✅ No conflict with global shortcuts

**Status:** [ ] Pass [ ] Fail

---

### TC14: Focus Indicators Visibility

**Steps:**
1. Tab through all interactive elements
2. Observe focus indicators

**Expected Results:**
- ✅ All elements show blue focus ring when focused
- ✅ Focus ring is clearly visible against all backgrounds
- ✅ Focus ring has 2px width and offset
- ✅ No focus ring appears when clicking with mouse

**Status:** [ ] Pass [ ] Fail

---

### TC15: Screen Reader Announcements

**Steps:**
1. Enable screen reader (NVDA, JAWS, or VoiceOver)
2. Tab to voice button
3. Activate voice button
4. Listen to announcements

**Expected Results:**
- ✅ Voice button label is announced
- ✅ State changes are announced ("Recording your voice", "Processing", "Rose is responding")
- ✅ All interactive elements have descriptive labels
- ✅ Settings controls are properly labeled

**Status:** [ ] Pass [ ] Fail

---

### TC16: No Keyboard Traps

**Steps:**
1. Tab through entire page
2. Open and close all dialogs
3. Ensure you can always navigate away

**Expected Results:**
- ✅ No element traps keyboard focus
- ✅ Can always tab to next/previous element
- ✅ Can always close dialogs with Escape
- ✅ Can navigate entire interface with keyboard only

**Status:** [ ] Pass [ ] Fail

---

### TC17: Skip Link Functionality

**Steps:**
1. Load page
2. Press `Tab` to focus skip link
3. Press `Enter` to activate

**Expected Results:**
- ✅ Skip link appears when focused
- ✅ Activating skip link moves focus to main content
- ✅ Voice button receives focus after skip

**Status:** [ ] Pass [ ] Fail

---

### TC18: Multiple Recording Sessions

**Steps:**
1. Use keyboard to record multiple messages in sequence
2. Test with both `Space` and `Enter` keys

**Expected Results:**
- ✅ Each recording session works correctly
- ✅ No state issues between sessions
- ✅ Keyboard shortcuts remain functional
- ✅ Focus management works correctly

**Status:** [ ] Pass [ ] Fail

---

### TC19: Error State Keyboard Handling

**Steps:**
1. Trigger an error (e.g., deny microphone permission)
2. Try to use keyboard shortcuts

**Expected Results:**
- ✅ Voice button is disabled
- ✅ Keyboard shortcuts don't activate disabled button
- ✅ Error message is accessible
- ✅ Other controls remain functional

**Status:** [ ] Pass [ ] Fail

---

### TC20: Mobile External Keyboard

**Steps:**
1. Connect external keyboard to mobile device
2. Test all keyboard shortcuts

**Expected Results:**
- ✅ All keyboard shortcuts work on mobile
- ✅ Touch interactions still work
- ✅ No conflicts between touch and keyboard
- ✅ Focus indicators visible on mobile

**Status:** [ ] Pass [ ] Fail

---

## Browser Compatibility Testing

Test all above cases in:

- [ ] Chrome (Windows/Mac/Linux)
- [ ] Firefox (Windows/Mac/Linux)
- [ ] Safari (Mac/iOS)
- [ ] Edge (Windows)
- [ ] Mobile Safari (iOS with external keyboard)
- [ ] Chrome Mobile (Android with external keyboard)

## Screen Reader Testing

Test with:

- [ ] NVDA (Windows)
- [ ] JAWS (Windows)
- [ ] VoiceOver (Mac/iOS)
- [ ] TalkBack (Android)

## Accessibility Compliance

- [ ] WCAG 2.1 Level A compliance
- [ ] WCAG 2.1 Level AA compliance
- [ ] Section 508 compliance
- [ ] ARIA best practices followed

## Performance Testing

- [ ] No noticeable lag when using keyboard shortcuts
- [ ] Focus indicators render smoothly
- [ ] No performance impact from keyboard event listeners

## Test Summary

**Total Test Cases:** 20  
**Passed:** ___  
**Failed:** ___  
**Blocked:** ___  

**Overall Status:** [ ] Pass [ ] Fail

**Tester Name:** _______________  
**Test Date:** _______________  
**Browser/OS:** _______________  

## Notes

_Add any additional observations or issues here:_

---

## Automated Testing Recommendations

For future automated testing, consider:

1. **Playwright/Cypress Tests:**
   - Simulate keyboard events
   - Verify focus order
   - Check ARIA attributes

2. **Axe DevTools:**
   - Run automated accessibility scans
   - Verify WCAG compliance
   - Check keyboard accessibility

3. **Pa11y:**
   - Automated accessibility testing
   - CI/CD integration
   - Regular compliance checks

## References

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Keyboard Accessibility](https://webaim.org/techniques/keyboard/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
