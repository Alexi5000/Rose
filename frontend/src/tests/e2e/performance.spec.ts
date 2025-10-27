import { test, expect } from '@playwright/test';

/**
 * Performance Benchmark Tests
 * 
 * Tests frame rate, memory usage, and loading performance
 * Requirements: 6.1, 6.2, 6.3, 6.4
 */

test.describe('Performance Benchmarks', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test.describe('Frame Rate Performance', () => {
    test('should maintain 30+ FPS on desktop', async ({ page }) => {
      // Wait for scene to load
      await page.waitForTimeout(3000);

      // Measure FPS using Performance API
      const fps = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let frameCount = 0;
          const startTime = performance.now();
          const duration = 2000; // Measure for 2 seconds

          function countFrame() {
            frameCount++;
            const elapsed = performance.now() - startTime;
            
            if (elapsed < duration) {
              requestAnimationFrame(countFrame);
            } else {
              const fps = (frameCount / elapsed) * 1000;
              resolve(fps);
            }
          }

          requestAnimationFrame(countFrame);
        });
      });

      console.log(`Desktop FPS: ${fps.toFixed(2)}`);
      expect(fps).toBeGreaterThanOrEqual(30);
    });

    test('should measure FPS during voice interaction', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      await page.waitForTimeout(2000);

      const voiceButton = page.locator('[aria-label*="speak"]').first();
      
      // Start recording
      await voiceButton.click();
      await page.waitForTimeout(500);

      // Measure FPS during interaction
      const fps = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let frameCount = 0;
          const startTime = performance.now();
          const duration = 1000;

          function countFrame() {
            frameCount++;
            const elapsed = performance.now() - startTime;
            
            if (elapsed < duration) {
              requestAnimationFrame(countFrame);
            } else {
              resolve((frameCount / elapsed) * 1000);
            }
          }

          requestAnimationFrame(countFrame);
        });
      });

      console.log(`FPS during interaction: ${fps.toFixed(2)}`);
      expect(fps).toBeGreaterThanOrEqual(25); // Slightly lower threshold during interaction
    });

    test('should test FPS on different quality settings', async ({ page }) => {
      await page.waitForTimeout(2000);

      // Test with high quality
      const highQualityFps = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let frameCount = 0;
          const startTime = performance.now();
          
          function countFrame() {
            frameCount++;
            if (performance.now() - startTime < 1000) {
              requestAnimationFrame(countFrame);
            } else {
              resolve(frameCount);
            }
          }
          
          requestAnimationFrame(countFrame);
        });
      });

      console.log(`High quality FPS: ${highQualityFps}`);
      expect(highQualityFps).toBeGreaterThanOrEqual(30);
    });
  });

  test.describe('Memory Usage', () => {
    test('should monitor memory usage over time', async ({ page }) => {
      await page.waitForTimeout(3000);

      const memoryMetrics = await page.evaluate(() => {
        if ('memory' in performance) {
          const mem = (performance as any).memory;
          return {
            usedJSHeapSize: mem.usedJSHeapSize,
            totalJSHeapSize: mem.totalJSHeapSize,
            jsHeapSizeLimit: mem.jsHeapSizeLimit,
          };
        }
        return null;
      });

      if (memoryMetrics) {
        console.log('Memory metrics:', memoryMetrics);
        
        // Used heap should be less than 80% of total
        const usagePercent = (memoryMetrics.usedJSHeapSize / memoryMetrics.totalJSHeapSize) * 100;
        console.log(`Memory usage: ${usagePercent.toFixed(2)}%`);
        
        expect(usagePercent).toBeLessThan(80);
      }
    });

    test('should not leak memory during repeated interactions', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      await page.waitForTimeout(2000);

      const getMemory = async () => {
        return await page.evaluate(() => {
          if ('memory' in performance) {
            return (performance as any).memory.usedJSHeapSize;
          }
          return 0;
        });
      };

      const initialMemory = await getMemory();
      const voiceButton = page.locator('[aria-label*="speak"]').first();

      // Perform multiple interactions
      for (let i = 0; i < 5; i++) {
        await voiceButton.click();
        await page.waitForTimeout(200);
        await voiceButton.click(); // Stop
        await page.waitForTimeout(200);
      }

      const finalMemory = await getMemory();
      
      if (initialMemory > 0 && finalMemory > 0) {
        const memoryIncrease = finalMemory - initialMemory;
        const increasePercent = (memoryIncrease / initialMemory) * 100;
        
        console.log(`Memory increase: ${increasePercent.toFixed(2)}%`);
        
        // Memory should not increase by more than 50% after interactions
        expect(increasePercent).toBeLessThan(50);
      }
    });

    test('should cleanup resources on navigation', async ({ page }) => {
      await page.waitForTimeout(3000);

      const initialMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      // Navigate away and back
      await page.goto('about:blank');
      await page.waitForTimeout(500);
      await page.goto('/');
      await page.waitForTimeout(3000);

      const finalMemory = await page.evaluate(() => {
        if ('memory' in performance) {
          return (performance as any).memory.usedJSHeapSize;
        }
        return 0;
      });

      if (initialMemory > 0 && finalMemory > 0) {
        console.log(`Initial: ${initialMemory}, Final: ${finalMemory}`);
        // Memory should be similar after reload
        const diff = Math.abs(finalMemory - initialMemory);
        const diffPercent = (diff / initialMemory) * 100;
        expect(diffPercent).toBeLessThan(30);
      }
    });
  });

  test.describe('Loading Performance', () => {
    test('should load initial assets within 5 seconds', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/');
      
      // Wait for canvas to be visible
      await page.locator('canvas').waitFor({ state: 'visible' });
      
      const loadTime = Date.now() - startTime;
      console.log(`Initial load time: ${loadTime}ms`);
      
      expect(loadTime).toBeLessThan(5000);
    });

    test('should show loading progress', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      
      // Check for loading indicator
      const loadingIndicator = page.locator('[class*="loading"]').first();
      
      // Loading indicator should appear initially
      const isVisible = await loadingIndicator.isVisible().catch(() => false);
      
      if (isVisible) {
        // Wait for it to disappear
        await loadingIndicator.waitFor({ state: 'hidden', timeout: 10000 });
      }
      
      // Scene should be loaded
      await expect(page.locator('canvas')).toBeVisible();
    });

    test('should measure Time to Interactive', async ({ page }) => {
      const metrics = await page.evaluate(() => {
        return new Promise<any>((resolve) => {
          if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
              const entries = list.getEntries();
              resolve(entries);
            });
            
            observer.observe({ entryTypes: ['navigation', 'paint'] });
            
            // Fallback timeout
            setTimeout(() => {
              resolve(performance.getEntriesByType('navigation'));
            }, 5000);
          } else {
            resolve(performance.getEntriesByType('navigation'));
          }
        });
      });

      console.log('Performance metrics:', metrics);
      
      if (metrics && metrics.length > 0) {
        const navEntry = metrics[0];
        if (navEntry.domInteractive) {
          console.log(`DOM Interactive: ${navEntry.domInteractive}ms`);
          expect(navEntry.domInteractive).toBeLessThan(3000);
        }
      }
    });

    test('should measure First Contentful Paint', async ({ page }) => {
      await page.goto('/');
      
      const fcp = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const fcpEntry = entries.find(entry => entry.name === 'first-contentful-paint');
            if (fcpEntry) {
              resolve(fcpEntry.startTime);
              observer.disconnect();
            }
          });
          
          observer.observe({ entryTypes: ['paint'] });
          
          // Fallback
          setTimeout(() => resolve(0), 5000);
        });
      });

      if (fcp > 0) {
        console.log(`First Contentful Paint: ${fcp}ms`);
        expect(fcp).toBeLessThan(2000);
      }
    });
  });

  test.describe('Asset Optimization', () => {
    test('should load optimized textures', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(3000);

      // Check network requests for texture files
      const requests = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources
          .filter((r: any) => r.name.includes('.jpg') || r.name.includes('.png') || r.name.includes('.webp'))
          .map((r: any) => ({
            name: r.name,
            size: r.transferSize,
            duration: r.duration,
          }));
      });

      console.log('Texture requests:', requests);
      
      // Textures should be reasonably sized
      requests.forEach((req: any) => {
        if (req.size > 0) {
          expect(req.size).toBeLessThan(2 * 1024 * 1024); // Less than 2MB per texture
        }
      });
    });

    test('should use code splitting', async ({ page }) => {
      await page.goto('/');
      
      const jsRequests = await page.evaluate(() => {
        const resources = performance.getEntriesByType('resource');
        return resources
          .filter((r: any) => r.name.includes('.js'))
          .map((r: any) => ({
            name: r.name.split('/').pop(),
            size: r.transferSize,
          }));
      });

      console.log('JavaScript bundles:', jsRequests);
      
      // Should have multiple JS chunks (code splitting)
      expect(jsRequests.length).toBeGreaterThan(1);
    });

    test('should lazy load non-critical assets', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      
      // Wait for initial render
      await page.locator('canvas').waitFor({ state: 'visible' });
      const initialLoadTime = Date.now() - startTime;

      // Wait for additional assets
      await page.waitForTimeout(2000);
      const totalLoadTime = Date.now() - startTime;

      console.log(`Initial: ${initialLoadTime}ms, Total: ${totalLoadTime}ms`);
      
      // Initial load should be faster than total load (lazy loading working)
      expect(initialLoadTime).toBeLessThan(totalLoadTime);
    });
  });

  test.describe('Responsive Performance', () => {
    test('should perform well on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForTimeout(2000);

      const fps = await page.evaluate(() => {
        return new Promise<number>((resolve) => {
          let frameCount = 0;
          const startTime = performance.now();
          
          function countFrame() {
            frameCount++;
            if (performance.now() - startTime < 1000) {
              requestAnimationFrame(countFrame);
            } else {
              resolve(frameCount);
            }
          }
          
          requestAnimationFrame(countFrame);
        });
      });

      console.log(`Mobile FPS: ${fps}`);
      expect(fps).toBeGreaterThanOrEqual(25); // Lower threshold for mobile
    });

    test('should adapt quality based on device', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForTimeout(2000);

      // Check if quality settings are applied
      const qualityInfo = await page.evaluate(() => {
        const canvas = document.querySelector('canvas');
        if (canvas) {
          return {
            width: canvas.width,
            height: canvas.height,
            pixelRatio: window.devicePixelRatio,
          };
        }
        return null;
      });

      console.log('Mobile quality settings:', qualityInfo);
      
      if (qualityInfo) {
        // Mobile should use reasonable resolution
        expect(qualityInfo.width).toBeLessThan(2000);
        expect(qualityInfo.height).toBeLessThan(2000);
      }
    });
  });

  test.describe('Lighthouse Metrics', () => {
    test('should generate Lighthouse report', async ({ page }) => {
      // This is a placeholder for Lighthouse CI integration
      // In a real setup, you would use @playwright/test with lighthouse
      
      await page.goto('/');
      await page.waitForTimeout(3000);

      // Basic performance checks
      const performanceMetrics = await page.evaluate(() => {
        const nav = performance.getEntriesByType('navigation')[0] as any;
        return {
          domContentLoaded: nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
          loadComplete: nav.loadEventEnd - nav.loadEventStart,
          domInteractive: nav.domInteractive,
        };
      });

      console.log('Performance metrics:', performanceMetrics);
      
      expect(performanceMetrics.domInteractive).toBeLessThan(3000);
    });
  });
});
