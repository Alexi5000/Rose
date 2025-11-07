# Accessibility Features

This document outlines the accessibility features implemented in the Rose frontend application to ensure an inclusive user experience for all users, including those using assistive technologies.

## Overview

The Rose application follows WCAG 2.1 Level AA guidelines and implements comprehensive accessibility features including:

- Semantic HTML and ARIA labels
- Keyboard navigation support
- Screen reader compatibility
- Visual focus indicators
- Live region announcements
- Skip navigation links

## Keyboard Navigation

### Keyboard Shortcuts

- **Space** or **Enter**: Press and hold to start recording, release to send message
- **Tab**: Navigate between interactive elements
- **Shift + Tab**: Navigate backwards through interactive elements

### Focus Management

- All interactive elements are keyboard accessible
- Clear visual focus indicators with outline styling
- Logical tab order through the interface
- Skip link to jump directly to main content

## Screen Reader Support

### ARIA Labels

All interactive elements have descriptive ARIA labels:

- **Voice Button**: Dynamic labels based on state
  - Idle: "Press and hold to speak with Rose"
  - Listening: "Listening... Release to send your message"
  - Processing: "Processing your message, please wait"
  - Speaking: "Rose is speaking, please wait"
  - Error: "Error occurred. Press to try again"

- **Retry Button**: "Retry voice input"
- **Response Region**: "Rose's response"
- **Keyboard Shortcuts**: "Keyboard shortcuts"

### Live Regions

Dynamic content updates are announced to screen readers using ARIA live regions:

- **Voice Button State**: `aria-live="polite"` announces state changes
- **Status Messages**: `aria-live="polite"` for processing updates
- **Network Status**: 
  - Offline: `aria-live="assertive"` for immediate announcement
  - Online: `aria-live="polite"` for reconnection notification
- **Timeout Indicators**: `aria-live="polite"` for long operation warnings

### Semantic HTML

- Proper heading hierarchy (`h1` for title)
- Semantic landmarks (`header`, `main`, `role="banner"`, `role="main"`)
- Descriptive button text and labels
- Proper list structure for keyboard shortcuts

## Visual Accessibility

### Focus Indicators

- High contrast focus outlines (3px solid)
- Visible focus states on all interactive elements
- Focus-visible pseudo-class for keyboard-only focus indicators

### Color and Contrast

- Sufficient color contrast ratios for text
- Visual state indicators don't rely solely on color
- Error states use both color and text

### Skip Links

- Skip to main content link for keyboard users
- Visually hidden until focused
- Positioned at the top of the page

## Component-Specific Features

### VoiceButton

- Dynamic ARIA labels based on state
- Keyboard event handlers for Space and Enter keys
- Screen reader announcements for state changes
- Disabled state properly communicated
- `aria-pressed` attribute for toggle state

### StatusIndicator

- Status messages in live region
- Retry button with descriptive label
- Color-coded states with text descriptions

### NetworkStatus

- Alert role for offline status (assertive)
- Status role for reconnection (polite)
- Icons marked as decorative with `aria-hidden`

### TimeoutIndicator

- Polite live region for timeout warnings
- Clear text descriptions of elapsed time
- Icons marked as decorative

## Testing Recommendations

### Manual Testing

1. **Keyboard Navigation**
   - Tab through all interactive elements
   - Verify focus indicators are visible
   - Test Space/Enter key functionality

2. **Screen Reader Testing**
   - Test with NVDA (Windows), JAWS (Windows), or VoiceOver (macOS)
   - Verify all content is announced correctly
   - Check live region announcements

3. **Visual Testing**
   - Verify focus indicators are visible
   - Check color contrast ratios
   - Test with browser zoom (200%)

### Automated Testing

Consider adding automated accessibility tests using:
- axe-core
- jest-axe
- Lighthouse accessibility audits
- Pa11y

## Browser Support

Accessibility features are supported in:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Future Improvements

Potential enhancements for even better accessibility:

1. Add high contrast mode support
2. Implement reduced motion preferences
3. Add voice command alternatives
4. Support for additional languages
5. Customizable text size settings
6. Dark mode with proper contrast ratios

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Resources](https://webaim.org/)
