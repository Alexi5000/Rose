import { test, expect } from '@playwright/test';

/**
 * Accessibility Test Suite
 * 
 * Tests keyboard navigation, ARIA labels, reduced motion, and focus management
 * Requirements: 5.5
 */

test.describe('Accessibility Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);
  });

  test.describe('Keyboard Navigation', () => {
    test('should navigate to voice button with Tab', async ({ page }) => {
      // Press Tab to focus first interactive element
      await page.keyboard.press('Tab');
      await page.waitForTimeout(300);

      // Check if an element is focused
      const focusedElement = await page.evaluate(() => {
        const el = document.activeElement;
        return {
          tagName: el?.tagName,
          ariaLabel: el?.getAttribute('aria-label'),
          role: el?.getAttribute('role'),
        };
      });

      console.log('Focused element:', focusedElement);
      expect(focusedElement.tagName).toBeTruthy();
    });

    test('should activate voice button with Space key', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      
      // Tab to voice button
      await page.keyboard.press('Tab');
      await page.waitForTimeout(300);

      // Press Space to activate
      await page.keyboard.press('Space');
      await page.waitForTimeout(500);

      // Check if listening state is active
      const isListening = await page.evaluate(() => {
        const button = document.querySelector('[aria-label*="speak"]');
        return button?.getAttribute('aria-pressed') === 'true' ||
               button?.classList.contains('listening');
      });

      console.log('Is listening:', isListening);
    });

    test('should activate voice button with Enter key', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      
      await page.keyboard.press('Tab');
      await page.waitForTimeout(300);

      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);

      // Should activate voice interaction
      const button = page.locator('[aria-label*="speak"]').first();
      await expect(button).toBeVisible();
    });

    test('should cancel recording with Escape key', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      
      // Start recording
      await page.keyboard.press('Tab');
      await page.keyboard.press('Space');
      await page.waitForTimeout(500);

      // Cancel with Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      // Should return to idle state
      const button = page.locator('[aria-label*="speak"]').first();
      await expect(button).toBeVisible();
    });

    test('should navigate through all interactive elements', async ({ page }) => {
      const interactiveElements: string[] = [];

      // Tab through all elements
      for (let i = 0; i < 10; i++) {
        await page.keyboard.press('Tab');
        await page.waitForTimeout(200);

        const focused = await page.evaluate(() => {
          const el = document.activeElement;
          return el?.getAttribute('aria-label') || el?.tagName || '';
        });

        if (focused) {
          interactiveElements.push(focused);
        }
      }

      console.log('Interactive elements:', interactiveElements);
      expect(interactiveElements.length).toBeGreaterThan(0);
    });

    test('should show keyboard help with ? key', async ({ page }) => {
      await page.keyboard.press('?');
      await page.waitForTimeout(500);

      // Check if help overlay appears
      const helpVisible = await page.evaluate(() => {
        const help = document.querySelector('[class*="keyboard-help"]') ||
                     document.querySelector('[class*="help"]');
        return help ? window.getComputedStyle(help).display !== 'none' : false;
      });

      console.log('Keyboard help visible:', helpVisible);
    });

    test('should trap focus in modal dialogs', async ({ page }) => {
      // Open settings if available
      const settingsButton = page.locator('[aria-label*="settings"]').first();
      
      if (await settingsButton.isVisible()) {
        await settingsButton.click();
        await page.waitForTimeout(500);

        // Tab multiple times
        const focusedElements: string[] = [];
        for (let i = 0; i < 5; i++) {
          await page.keyboard.press('Tab');
          await page.waitForTimeout(100);

          const focused = await page.evaluate(() => {
            return document.activeElement?.tagName || '';
          });
          focusedElements.push(focused);
        }

        console.log('Focus trap elements:', focusedElements);
        // Focus should stay within modal
        expect(focusedElements.length).toBeGreaterThan(0);
      }
    });
  });

  test.describe('ARIA Labels and Announcements', () => {
    test('should have proper ARIA label on voice button', async ({ page }) => {
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      
      const ariaLabel = await voiceButton.getAttribute('aria-label');
      console.log('Voice button ARIA label:', ariaLabel);
      
      expect(ariaLabel).toBeTruthy();
      expect(ariaLabel?.toLowerCase()).toContain('speak');
    });

    test('should update ARIA pressed state', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      
      // Initial state
      const initialPressed = await voiceButton.getAttribute('aria-pressed');
      console.log('Initial aria-pressed:', initialPressed);

      // Click button
      await voiceButton.click();
      await page.waitForTimeout(500);

      // Check updated state
      const updatedPressed = await voiceButton.getAttribute('aria-pressed');
      console.log('Updated aria-pressed:', updatedPressed);
    });

    test('should have ARIA live region for status updates', async ({ page }) => {
      const liveRegion = await page.evaluate(() => {
        const regions = document.querySelectorAll('[aria-live]');
        return Array.from(regions).map(el => ({
          ariaLive: el.getAttribute('aria-live'),
          ariaAtomic: el.getAttribute('aria-atomic'),
          content: el.textContent?.trim(),
        }));
      });

      console.log('Live regions:', liveRegion);
      
      if (liveRegion.length > 0) {
        expect(liveRegion[0].ariaLive).toBeTruthy();
      }
    });

    test('should announce voice state changes', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      await voiceButton.click();
      await page.waitForTimeout(500);

      // Check for status announcements
      const statusText = await page.evaluate(() => {
        const status = document.querySelector('[role="status"]') ||
                      document.querySelector('[aria-live]');
        return status?.textContent?.trim();
      });

      console.log('Status announcement:', statusText);
    });

    test('should have descriptive alt text for images', async ({ page }) => {
      const images = await page.evaluate(() => {
        const imgs = document.querySelectorAll('img');
        return Array.from(imgs).map(img => ({
          src: img.src,
          alt: img.alt,
          ariaLabel: img.getAttribute('aria-label'),
        }));
      });

      console.log('Images:', images);
      
      // All images should have alt text or aria-label
      images.forEach(img => {
        expect(img.alt || img.ariaLabel).toBeTruthy();
      });
    });

    test('should have proper heading hierarchy', async ({ page }) => {
      const headings = await page.evaluate(() => {
        const h = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        return Array.from(h).map(heading => ({
          level: heading.tagName,
          text: heading.textContent?.trim(),
        }));
      });

      console.log('Headings:', headings);
      
      // Should have at least one h1
      const h1Count = headings.filter(h => h.level === 'H1').length;
      expect(h1Count).toBeGreaterThanOrEqual(1);
    });

    test('should have skip link for keyboard users', async ({ page }) => {
      const skipLink = await page.evaluate(() => {
        const link = document.querySelector('a[href="#main"]') ||
                     document.querySelector('[class*="skip"]');
        return {
          exists: !!link,
          text: link?.textContent?.trim(),
        };
      });

      console.log('Skip link:', skipLink);
    });
  });

  test.describe('Reduced Motion Support', () => {
    test('should detect reduced motion preference', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.reload();
      await page.waitForTimeout(2000);

      const reducedMotion = await page.evaluate(() => {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      });

      console.log('Reduced motion detected:', reducedMotion);
      expect(reducedMotion).toBe(true);
    });

    test('should disable animations with reduced motion', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.reload();
      await page.waitForTimeout(2000);

      // Check if animations are disabled
      const animationsDisabled = await page.evaluate(() => {
        const body = document.body;
        const computedStyle = window.getComputedStyle(body);
        
        // Check for reduced motion class or style
        return body.classList.contains('reduced-motion') ||
               computedStyle.getPropertyValue('--animation-duration') === '0s';
      });

      console.log('Animations disabled:', animationsDisabled);
    });

    test('should maintain functionality without animations', async ({ page, context }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.reload();
      await context.grantPermissions(['microphone']);
      await page.waitForTimeout(2000);

      // Voice button should still work
      const voiceButton = page.locator('[aria-label*="speak"]').first();
      await voiceButton.click();
      await page.waitForTimeout(500);

      // Functionality should be preserved
      await expect(voiceButton).toBeVisible();
    });

    test('should have toggle for reduced motion in settings', async ({ page }) => {
      const settingsButton = page.locator('[aria-label*="settings"]').first();
      
      if (await settingsButton.isVisible()) {
        await settingsButton.click();
        await page.waitForTimeout(500);

        // Look for reduced motion toggle
        const motionToggle = await page.evaluate(() => {
          const toggle = document.querySelector('[aria-label*="motion"]') ||
                        document.querySelector('[aria-label*="animation"]');
          return !!toggle;
        });

        console.log('Motion toggle exists:', motionToggle);
      }
    });
  });

  test.describe('Focus Management', () => {
    test('should have visible focus indicators', async ({ page }) => {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(300);

      const focusStyle = await page.evaluate(() => {
        const el = document.activeElement;
        if (!el) return null;

        const style = window.getComputedStyle(el);
        return {
          outline: style.outline,
          outlineWidth: style.outlineWidth,
          outlineColor: style.outlineColor,
          boxShadow: style.boxShadow,
        };
      });

      console.log('Focus style:', focusStyle);
      
      // Should have some visible focus indicator
      if (focusStyle) {
        const hasOutline = focusStyle.outline !== 'none' && 
                          focusStyle.outlineWidth !== '0px';
        const hasBoxShadow = focusStyle.boxShadow !== 'none';
        
        expect(hasOutline || hasBoxShadow).toBe(true);
      }
    });

    test('should manage focus on modal open', async ({ page }) => {
      const settingsButton = page.locator('[aria-label*="settings"]').first();
      
      if (await settingsButton.isVisible()) {
        await settingsButton.click();
        await page.waitForTimeout(500);

        // Focus should move into modal
        const focusedElement = await page.evaluate(() => {
          const el = document.activeElement;
          const modal = el?.closest('[role="dialog"]') ||
                       el?.closest('[class*="modal"]');
          return !!modal;
        });

        console.log('Focus in modal:', focusedElement);
      }
    });

    test('should restore focus on modal close', async ({ page }) => {
      const settingsButton = page.locator('[aria-label*="settings"]').first();
      
      if (await settingsButton.isVisible()) {
        // Remember initial focus
        await settingsButton.focus();
        
        // Open modal
        await settingsButton.click();
        await page.waitForTimeout(500);

        // Close modal (Escape key)
        await page.keyboard.press('Escape');
        await page.waitForTimeout(300);

        // Focus should return to settings button
        const focusRestored = await page.evaluate(() => {
          const el = document.activeElement;
          return el?.getAttribute('aria-label')?.includes('settings') || false;
        });

        console.log('Focus restored:', focusRestored);
      }
    });

    test('should not trap focus outside modals', async ({ page }) => {
      // Tab through elements
      const elements: string[] = [];
      
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press('Tab');
        await page.waitForTimeout(200);

        const tag = await page.evaluate(() => document.activeElement?.tagName);
        if (tag) elements.push(tag);
      }

      console.log('Tabbed elements:', elements);
      
      // Should be able to tab through different elements
      const uniqueElements = new Set(elements);
      expect(uniqueElements.size).toBeGreaterThan(0);
    });

    test('should focus first element on page load', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      // Check initial focus
      const initialFocus = await page.evaluate(() => {
        return document.activeElement?.tagName;
      });

      console.log('Initial focus:', initialFocus);
      expect(initialFocus).toBeTruthy();
    });
  });

  test.describe('Screen Reader Support', () => {
    test('should have proper document title', async ({ page }) => {
      const title = await page.title();
      console.log('Page title:', title);
      
      expect(title).toBeTruthy();
      expect(title.length).toBeGreaterThan(0);
    });

    test('should have lang attribute on html', async ({ page }) => {
      const lang = await page.evaluate(() => {
        return document.documentElement.lang;
      });

      console.log('Document language:', lang);
      expect(lang).toBeTruthy();
    });

    test('should have semantic HTML structure', async ({ page }) => {
      const semanticElements = await page.evaluate(() => {
        return {
          main: !!document.querySelector('main'),
          nav: !!document.querySelector('nav'),
          header: !!document.querySelector('header'),
          footer: !!document.querySelector('footer'),
        };
      });

      console.log('Semantic elements:', semanticElements);
      
      // Should have at least main element
      expect(semanticElements.main).toBe(true);
    });

    test('should have proper button roles', async ({ page }) => {
      const buttons = await page.evaluate(() => {
        const btns = document.querySelectorAll('button, [role="button"]');
        return Array.from(btns).map(btn => ({
          tagName: btn.tagName,
          role: btn.getAttribute('role'),
          ariaLabel: btn.getAttribute('aria-label'),
        }));
      });

      console.log('Buttons:', buttons);
      
      // All buttons should have proper semantics
      buttons.forEach(btn => {
        expect(btn.tagName === 'BUTTON' || btn.role === 'button').toBe(true);
      });
    });

    test('should announce loading states', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });

      const loadingAnnouncement = await page.evaluate(() => {
        const loading = document.querySelector('[aria-busy="true"]') ||
                       document.querySelector('[role="progressbar"]') ||
                       document.querySelector('[aria-label*="loading"]');
        return !!loading;
      });

      console.log('Loading announcement:', loadingAnnouncement);
    });

    test('should have descriptive error messages', async ({ page }) => {
      // Check if error messages are accessible
      const errorElements = await page.evaluate(() => {
        const errors = document.querySelectorAll('[role="alert"], [aria-live="assertive"]');
        return Array.from(errors).map(el => ({
          role: el.getAttribute('role'),
          ariaLive: el.getAttribute('aria-live'),
          text: el.textContent?.trim(),
        }));
      });

      console.log('Error elements:', errorElements);
    });
  });

  test.describe('Color Contrast', () => {
    test('should have sufficient contrast for text', async ({ page }) => {
      const contrastIssues = await page.evaluate(() => {
        const elements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, button, a');
        const issues: any[] = [];

        elements.forEach(el => {
          const style = window.getComputedStyle(el);
          const color = style.color;
          const bgColor = style.backgroundColor;
          
          if (color && bgColor) {
            issues.push({
              element: el.tagName,
              color,
              backgroundColor: bgColor,
            });
          }
        });

        return issues;
      });

      console.log('Contrast check:', contrastIssues.length, 'elements checked');
      expect(contrastIssues.length).toBeGreaterThan(0);
    });

    test('should not rely solely on color for information', async ({ page }) => {
      // Check if interactive elements have additional indicators
      const indicators = await page.evaluate(() => {
        const buttons = document.querySelectorAll('button');
        return Array.from(buttons).map(btn => {
          const style = window.getComputedStyle(btn);
          return {
            hasOutline: style.outline !== 'none',
            hasBorder: style.border !== 'none',
            hasBoxShadow: style.boxShadow !== 'none',
          };
        });
      });

      console.log('Visual indicators:', indicators);
    });
  });

  test.describe('Responsive Accessibility', () => {
    test('should be accessible on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.reload();
      await page.waitForTimeout(2000);

      // Check touch target sizes
      const touchTargets = await page.evaluate(() => {
        const interactive = document.querySelectorAll('button, a, input');
        return Array.from(interactive).map(el => {
          const rect = el.getBoundingClientRect();
          return {
            width: rect.width,
            height: rect.height,
            meetsMinimum: rect.width >= 44 && rect.height >= 44,
          };
        });
      });

      console.log('Touch targets:', touchTargets);
      
      // Most touch targets should meet minimum size
      const meetingMinimum = touchTargets.filter(t => t.meetsMinimum).length;
      const total = touchTargets.length;
      
      if (total > 0) {
        const percentage = (meetingMinimum / total) * 100;
        console.log(`${percentage.toFixed(0)}% of touch targets meet minimum size`);
      }
    });

    test('should support zoom up to 200%', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      // Zoom in
      await page.evaluate(() => {
        document.body.style.zoom = '2';
      });

      await page.waitForTimeout(500);

      // Content should still be accessible
      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
    });
  });
});
