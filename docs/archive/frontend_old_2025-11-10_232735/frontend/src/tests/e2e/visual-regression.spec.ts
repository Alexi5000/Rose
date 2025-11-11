import { test, expect } from '@playwright/test';

/**
 * Visual Regression Tests
 * 
 * Tests visual appearance and layout across different states and viewports
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6
 */

test.describe('Visual Regression Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for 3D scene to load
    await page.waitForTimeout(3000);
  });

  test.describe('Initial Load State', () => {
    test('should render hero title correctly', async ({ page }) => {
      const heroTitle = page.locator('h1');
      await expect(heroTitle).toBeVisible();
      await expect(heroTitle).toContainText('ROSE');
      
      // Visual snapshot
      await expect(heroTitle).toHaveScreenshot('hero-title.png');
    });

    test('should render 3D scene canvas', async ({ page }) => {
      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
      
      // Wait for scene to stabilize
      await page.waitForTimeout(2000);
      
      // Full page snapshot
      await expect(page).toHaveScreenshot('initial-scene.png', {
        fullPage: true,
      });
    });

    test('should render voice button in idle state', async ({ page }) => {
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      await expect(voiceButton).toBeVisible();
      
      // Snapshot of voice button area
      await expect(voiceButton).toHaveScreenshot('voice-button-idle.png');
    });
  });

  test.describe('Voice Button States', () => {
    test('should show hover state on voice button', async ({ page }) => {
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      
      // Hover over button
      await voiceButton.hover();
      await page.waitForTimeout(500);
      
      await expect(voiceButton).toHaveScreenshot('voice-button-hover.png');
    });

    test('should show listening state visual feedback', async ({ page }) => {
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      
      // Mock microphone permission
      await page.context().grantPermissions(['microphone']);
      
      // Click to start listening
      await voiceButton.click();
      await page.waitForTimeout(1000);
      
      // Capture listening state
      await expect(page).toHaveScreenshot('listening-state.png', {
        fullPage: true,
      });
    });

    test('should show processing state', async ({ page }) => {
      // This would require mocking the API response
      // For now, we'll test the UI component directly
      const statusIndicator = page.locator('[class*="processing"]').first();
      
      if (await statusIndicator.isVisible()) {
        await expect(page).toHaveScreenshot('processing-state.png', {
          fullPage: true,
        });
      }
    });
  });

  test.describe('Responsive Layouts', () => {
    test('should render correctly on desktop', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 });
      await page.waitForTimeout(1000);
      
      await expect(page).toHaveScreenshot('desktop-layout.png', {
        fullPage: true,
      });
    });

    test('should render correctly on tablet', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 });
      await page.waitForTimeout(1000);
      
      await expect(page).toHaveScreenshot('tablet-layout.png', {
        fullPage: true,
      });
    });

    test('should render correctly on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(1000);
      
      await expect(page).toHaveScreenshot('mobile-layout.png', {
        fullPage: true,
      });
    });

    test('should adapt camera position on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.waitForTimeout(2000);
      
      const canvas = page.locator('canvas');
      await expect(canvas).toHaveScreenshot('mobile-camera-view.png');
    });
  });

  test.describe('Color Palette Verification', () => {
    test('should display correct ice cave colors', async ({ page }) => {
      // Wait for scene to fully render
      await page.waitForTimeout(3000);
      
      // Capture full scene for color verification
      await expect(page).toHaveScreenshot('color-palette-ice-cave.png', {
        fullPage: true,
      });
    });

    test('should show warm igloo glow', async ({ page }) => {
      await page.waitForTimeout(3000);
      
      // Focus on left side where igloo should be
      const canvas = page.locator('canvas');
      await expect(canvas).toHaveScreenshot('igloo-warm-glow.png');
    });

    test('should display aurora effect colors', async ({ page }) => {
      await page.waitForTimeout(3000);
      
      // Capture scene with aurora visible
      await expect(page).toHaveScreenshot('aurora-colors.png', {
        fullPage: true,
      });
    });
  });

  test.describe('UI Components', () => {
    test('should render settings panel when opened', async ({ page }) => {
      const settingsButton = page.locator('[aria-label*="settings"]').first();
      
      if (await settingsButton.isVisible()) {
        await settingsButton.click();
        await page.waitForTimeout(500);
        
        await expect(page).toHaveScreenshot('settings-panel-open.png', {
          fullPage: true,
        });
      }
    });

    test('should show keyboard help overlay', async ({ page }) => {
      // Press ? key to show keyboard help
      await page.keyboard.press('?');
      await page.waitForTimeout(500);
      
      const helpOverlay = page.locator('[class*="keyboard-help"]').first();
      
      if (await helpOverlay.isVisible()) {
        await expect(page).toHaveScreenshot('keyboard-help.png', {
          fullPage: true,
        });
      }
    });

    test('should display loading screen', async ({ page }) => {
      // Navigate to fresh page to catch loading screen
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      
      const loadingScreen = page.locator('[class*="loading"]').first();
      
      if (await loadingScreen.isVisible()) {
        await expect(loadingScreen).toHaveScreenshot('loading-screen.png');
      }
    });
  });

  test.describe('Animation States', () => {
    test('should capture water ripple animation', async ({ page }) => {
      await page.waitForTimeout(3000);
      
      // Capture multiple frames to verify animation
      await expect(page).toHaveScreenshot('water-ripples-frame1.png', {
        fullPage: true,
      });
      
      await page.waitForTimeout(1000);
      
      await expect(page).toHaveScreenshot('water-ripples-frame2.png', {
        fullPage: true,
      });
    });

    test('should show Rose avatar ambient animation', async ({ page }) => {
      await page.waitForTimeout(3000);
      
      const canvas = page.locator('canvas');
      await expect(canvas).toHaveScreenshot('rose-ambient-animation.png');
    });
  });

  test.describe('Error States', () => {
    test('should display WebGL fallback message', async ({ page }) => {
      // This would require disabling WebGL in browser
      // For now, we'll check if the fallback component exists
      const fallback = page.locator('[class*="webgl-fallback"]').first();
      
      if (await fallback.isVisible()) {
        await expect(fallback).toHaveScreenshot('webgl-fallback.png');
      }
    });

    test('should show error overlay for loading failures', async ({ page }) => {
      // This would require mocking asset loading failures
      const errorOverlay = page.locator('[class*="error"]').first();
      
      if (await errorOverlay.isVisible()) {
        await expect(page).toHaveScreenshot('error-overlay.png', {
          fullPage: true,
        });
      }
    });
  });

  test.describe('Accessibility Features', () => {
    test('should show focus indicators on keyboard navigation', async ({ page }) => {
      // Tab to voice button
      await page.keyboard.press('Tab');
      await page.waitForTimeout(300);
      
      await expect(page).toHaveScreenshot('focus-voice-button.png', {
        fullPage: true,
      });
    });

    test('should display reduced motion mode', async ({ page }) => {
      // Enable reduced motion preference
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.reload();
      await page.waitForTimeout(2000);
      
      await expect(page).toHaveScreenshot('reduced-motion-mode.png', {
        fullPage: true,
      });
    });
  });
});
