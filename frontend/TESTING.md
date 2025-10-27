# Testing Documentation

## Overview

This document describes the comprehensive testing suite for the Rose Immersive 3D Frontend. The test suite covers unit tests, integration tests, visual regression tests, performance benchmarks, cross-browser compatibility, and accessibility.

## Test Structure

```
frontend/src/tests/
├── setup.ts                          # Test configuration and mocks
├── hooks/                            # Unit tests for React hooks
│   ├── useVoiceInteraction.test.ts
│   └── useAudioAnalyzer.test.ts
├── integration/                      # Integration tests
│   └── audio-visual-sync.test.ts
└── e2e/                             # End-to-end tests
    ├── visual-regression.spec.ts
    ├── performance.spec.ts
    ├── cross-browser.spec.ts
    └── accessibility.spec.ts
```

## Running Tests

### Unit Tests (Vitest)

```bash
# Run all unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage
```

### E2E Tests (Playwright)

```bash
# Run all E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run specific test file
npx playwright test visual-regression

# Run tests in specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Categories

### 1. Unit Tests

**Location:** `src/tests/hooks/`

**Coverage:**
- `useVoiceInteraction` hook
  - State management (idle, listening, processing, speaking)
  - Microphone access and recording
  - Error handling (permissions, API failures)
  - Audio playback
  - Resource cleanup
  
- `useAudioAnalyzer` hook
  - Web Audio API initialization
  - Amplitude and frequency extraction
  - Real-time audio analysis
  - Performance optimization
  - Error handling

**Requirements Tested:** 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2

### 2. Integration Tests

**Location:** `src/tests/integration/`

**Coverage:**
- Audio-visual synchronization
  - Water ripple response to audio amplitude
  - Rose avatar glow with audio
  - Aurora intensity changes
  - Lighting effects synchronization
  - End-to-end audio-visual flow
  - Performance and timing
  - Error handling in sync

**Requirements Tested:** 4.1, 4.2, 4.3, 4.4, 4.5, 4.6

### 3. Visual Regression Tests

**Location:** `src/tests/e2e/visual-regression.spec.ts`

**Coverage:**
- Initial load state (hero title, 3D scene, voice button)
- Voice button states (idle, hover, listening, processing, speaking)
- Responsive layouts (desktop, tablet, mobile)
- Color palette verification (ice cave, igloo glow, aurora)
- UI components (settings panel, keyboard help, loading screen)
- Animation states (water ripples, Rose avatar)
- Error states (WebGL fallback, loading failures)
- Accessibility features (focus indicators, reduced motion)

**Requirements Tested:** 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6

### 4. Performance Benchmarks

**Location:** `src/tests/e2e/performance.spec.ts`

**Coverage:**
- Frame rate performance (30+ FPS on desktop, 25+ on mobile)
- Memory usage monitoring
- Memory leak detection
- Loading performance (< 5 seconds initial load)
- Time to Interactive
- First Contentful Paint
- Asset optimization (texture sizes, code splitting)
- Responsive performance (mobile, tablet, desktop)
- Lighthouse metrics

**Requirements Tested:** 6.1, 6.2, 6.3, 6.4

### 5. Cross-Browser Compatibility

**Location:** `src/tests/e2e/cross-browser.spec.ts`

**Coverage:**
- WebGL support detection (WebGL 1.0 and 2.0)
- WebGL context loss handling
- Audio API compatibility (Web Audio API, MediaRecorder)
- Audio format support (MP3, WAV, WebM, OGG)
- Shader compilation (vertex and fragment shaders)
- GLSL feature support
- Browser-specific features (Chrome, Firefox, Safari)
- Mobile browser compatibility (iOS Safari, Android Chrome)
- Feature detection and fallbacks
- Performance across browsers

**Requirements Tested:** 5.1, 5.2, 5.3, 5.4, 5.5

### 6. Accessibility Tests

**Location:** `src/tests/e2e/accessibility.spec.ts`

**Coverage:**
- Keyboard navigation (Tab, Space, Enter, Escape, ?)
- ARIA labels and announcements
- Live regions for status updates
- Reduced motion support
- Focus management (visible indicators, modal focus trap)
- Screen reader support (semantic HTML, proper roles)
- Color contrast
- Touch target sizes (44x44px minimum)
- Zoom support (up to 200%)

**Requirements Tested:** 5.5

## Test Configuration

### Vitest Configuration

**File:** `vitest.config.ts`

- Environment: jsdom
- Setup file: `src/tests/setup.ts`
- Coverage provider: v8
- Globals enabled for easier test writing

### Playwright Configuration

**File:** `playwright.config.ts`

- Test directory: `src/tests/e2e`
- Base URL: `http://localhost:5173`
- Projects: Chromium, Mobile (iPhone 12), Tablet (iPad Pro)
- Web server: Automatically starts dev server
- Retries: 2 in CI, 0 locally
- Screenshots: On failure only
- Trace: On first retry

## Mocking Strategy

### Web Audio API Mocks

- `AudioContext` - Mocked with all required methods
- `AnalyserNode` - Provides frequency and waveform data
- `MediaElementAudioSourceNode` - Connects audio elements

### MediaRecorder Mocks

- `MediaRecorder` - Mocked constructor and methods
- `isTypeSupported()` - Returns true for webm and mp4
- Event handlers: `ondataavailable`, `onstop`, `onerror`

### Browser APIs

- `navigator.mediaDevices.getUserMedia` - Mocked for microphone access
- `HTMLAudioElement` - Mocked for audio playback
- `requestAnimationFrame` - Mocked for animation testing
- `window.matchMedia` - Mocked for responsive and reduced motion tests

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm test
      - run: npm run test:coverage

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npx playwright install --with-deps
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

### Writing Tests

1. **Focus on behavior, not implementation**
   - Test what the user experiences
   - Avoid testing internal state directly

2. **Use descriptive test names**
   - Clearly state what is being tested
   - Include the expected outcome

3. **Keep tests isolated**
   - Each test should be independent
   - Use `beforeEach` for setup
   - Clean up in `afterEach`

4. **Mock external dependencies**
   - Mock API calls
   - Mock browser APIs
   - Use realistic mock data

5. **Test error cases**
   - Permission denied
   - Network failures
   - Invalid input

### Visual Regression Tests

1. **Wait for animations to complete**
   - Use appropriate timeouts
   - Wait for scene to stabilize

2. **Use consistent viewport sizes**
   - Define standard breakpoints
   - Test all responsive layouts

3. **Update baselines carefully**
   - Review visual changes
   - Commit baseline images to git

### Performance Tests

1. **Set realistic thresholds**
   - 30 FPS on desktop
   - 25 FPS on mobile
   - < 5 seconds load time

2. **Test on representative hardware**
   - Mid-range devices
   - Various screen sizes

3. **Monitor trends over time**
   - Track performance metrics
   - Identify regressions early

## Troubleshooting

### Common Issues

**Tests timing out:**
- Increase timeout in test configuration
- Check for infinite loops in animations
- Verify async operations complete

**Visual regression failures:**
- Check for animation timing issues
- Verify consistent viewport sizes
- Review baseline images

**WebGL tests failing:**
- Ensure headless browser supports WebGL
- Check for GPU availability in CI
- Use software rendering fallback

**Audio tests failing:**
- Verify mock setup is correct
- Check for timing issues in async operations
- Ensure cleanup is happening properly

## Coverage Goals

- **Unit Tests:** > 80% code coverage
- **Integration Tests:** All critical user flows
- **E2E Tests:** All major features and states
- **Accessibility:** WCAG 2.1 AA compliance
- **Performance:** Meet all defined thresholds
- **Cross-Browser:** Chrome, Firefox, Safari support

## Continuous Improvement

1. **Add tests for new features**
   - Write tests before implementation (TDD)
   - Ensure adequate coverage

2. **Update tests when requirements change**
   - Keep tests in sync with code
   - Remove obsolete tests

3. **Monitor test execution time**
   - Optimize slow tests
   - Parallelize where possible

4. **Review test failures**
   - Investigate flaky tests
   - Fix or skip unreliable tests

5. **Collect metrics**
   - Track test coverage trends
   - Monitor performance benchmarks
   - Analyze failure patterns

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)
- [Testing Library](https://testing-library.com/)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [WebGL Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/WebGL_best_practices)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
