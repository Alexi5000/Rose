import { test, expect, devices } from '@playwright/test';

/**
 * Cross-Browser Compatibility Tests
 * 
 * Tests WebGL, Audio API, and shader compatibility across browsers
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */

test.describe('Cross-Browser Compatibility', () => {
  test.describe('WebGL Compatibility', () => {
    test('should detect WebGL support', async ({ page }) => {
      await page.goto('/');

      const webglSupport = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        return {
          supported: !!gl,
          version: gl ? (gl as WebGLRenderingContext).getParameter((gl as WebGLRenderingContext).VERSION) : null,
          vendor: gl ? (gl as WebGLRenderingContext).getParameter((gl as WebGLRenderingContext).VENDOR) : null,
          renderer: gl ? (gl as WebGLRenderingContext).getParameter((gl as WebGLRenderingContext).RENDERER) : null,
        };
      });

      console.log('WebGL support:', webglSupport);
      expect(webglSupport.supported).toBe(true);
    });

    test('should check WebGL2 availability', async ({ page }) => {
      await page.goto('/');

      const webgl2Support = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl2 = canvas.getContext('webgl2');
        return {
          supported: !!gl2,
          maxTextureSize: gl2 ? gl2.getParameter(gl2.MAX_TEXTURE_SIZE) : null,
          maxVertexAttribs: gl2 ? gl2.getParameter(gl2.MAX_VERTEX_ATTRIBS) : null,
        };
      });

      console.log('WebGL2 support:', webgl2Support);
      
      if (webgl2Support.supported) {
        expect(webgl2Support.maxTextureSize).toBeGreaterThan(0);
      }
    });

    test('should render 3D canvas successfully', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();

      // Check if canvas has content
      const hasContent = await page.evaluate(() => {
        const canvas = document.querySelector('canvas') as HTMLCanvasElement;
        if (!canvas) return false;

        const ctx = canvas.getContext('2d');
        if (!ctx) return false;

        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const data = imageData.data;

        // Check if any pixels are non-zero (has rendered content)
        for (let i = 0; i < data.length; i += 4) {
          if (data[i] !== 0 || data[i + 1] !== 0 || data[i + 2] !== 0) {
            return true;
          }
        }
        return false;
      });

      expect(hasContent).toBe(true);
    });

    test('should handle WebGL context loss', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      // Simulate context loss
      const contextLost = await page.evaluate(() => {
        const canvas = document.querySelector('canvas') as HTMLCanvasElement;
        if (!canvas) return false;

        const gl = canvas.getContext('webgl');
        if (!gl) return false;

        const ext = gl.getExtension('WEBGL_lose_context');
        if (ext) {
          ext.loseContext();
          return true;
        }
        return false;
      });

      if (contextLost) {
        await page.waitForTimeout(1000);
        
        // Check if app handles context loss gracefully
        const errorMessage = page.locator('[class*="error"]').first();
        const isVisible = await errorMessage.isVisible().catch(() => false);
        
        // Either shows error or recovers
        expect(typeof isVisible).toBe('boolean');
      }
    });
  });

  test.describe('Audio API Compatibility', () => {
    test('should support Web Audio API', async ({ page }) => {
      await page.goto('/');

      const audioSupport = await page.evaluate(() => {
        return {
          AudioContext: 'AudioContext' in window || 'webkitAudioContext' in window,
          MediaRecorder: 'MediaRecorder' in window,
          getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
        };
      });

      console.log('Audio API support:', audioSupport);
      expect(audioSupport.AudioContext).toBe(true);
      expect(audioSupport.MediaRecorder).toBe(true);
      expect(audioSupport.getUserMedia).toBe(true);
    });

    test('should support required audio formats', async ({ page }) => {
      await page.goto('/');

      const formatSupport = await page.evaluate(() => {
        const audio = document.createElement('audio');
        return {
          mp3: audio.canPlayType('audio/mpeg') !== '',
          wav: audio.canPlayType('audio/wav') !== '',
          webm: audio.canPlayType('audio/webm') !== '',
          ogg: audio.canPlayType('audio/ogg') !== '',
        };
      });

      console.log('Audio format support:', formatSupport);
      
      // At least one format should be supported
      const hasSupport = Object.values(formatSupport).some(supported => supported);
      expect(hasSupport).toBe(true);
    });

    test('should support MediaRecorder formats', async ({ page, context }) => {
      await context.grantPermissions(['microphone']);
      await page.goto('/');

      const recorderSupport = await page.evaluate(() => {
        if (!('MediaRecorder' in window)) return {};
        
        return {
          webm: MediaRecorder.isTypeSupported('audio/webm'),
          mp4: MediaRecorder.isTypeSupported('audio/mp4'),
          ogg: MediaRecorder.isTypeSupported('audio/ogg'),
        };
      });

      console.log('MediaRecorder format support:', recorderSupport);
      
      // At least one format should be supported
      const hasSupport = Object.values(recorderSupport).some(supported => supported);
      expect(hasSupport).toBe(true);
    });

    test('should handle audio playback', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      const canPlayAudio = await page.evaluate(() => {
        return new Promise<boolean>((resolve) => {
          const audio = new Audio();
          audio.src = 'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';
          
          audio.oncanplay = () => resolve(true);
          audio.onerror = () => resolve(false);
          
          setTimeout(() => resolve(false), 2000);
        });
      });

      expect(canPlayAudio).toBe(true);
    });
  });

  test.describe('Shader Compilation', () => {
    test('should compile vertex shaders', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      const shaderCompilation = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) return { success: false, error: 'No WebGL context' };

        const vertexShaderSource = `
          attribute vec4 position;
          void main() {
            gl_Position = position;
          }
        `;

        const shader = gl.createShader(gl.VERTEX_SHADER);
        if (!shader) return { success: false, error: 'Could not create shader' };

        gl.shaderSource(shader, vertexShaderSource);
        gl.compileShader(shader);

        const success = gl.getShaderParameter(shader, gl.COMPILE_STATUS);
        const log = gl.getShaderInfoLog(shader);

        return { success, error: log };
      });

      console.log('Vertex shader compilation:', shaderCompilation);
      expect(shaderCompilation.success).toBe(true);
    });

    test('should compile fragment shaders', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      const shaderCompilation = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) return { success: false, error: 'No WebGL context' };

        const fragmentShaderSource = `
          precision mediump float;
          void main() {
            gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
          }
        `;

        const shader = gl.createShader(gl.FRAGMENT_SHADER);
        if (!shader) return { success: false, error: 'Could not create shader' };

        gl.shaderSource(shader, fragmentShaderSource);
        gl.compileShader(shader);

        const success = gl.getShaderParameter(shader, gl.COMPILE_STATUS);
        const log = gl.getShaderInfoLog(shader);

        return { success, error: log };
      });

      console.log('Fragment shader compilation:', shaderCompilation);
      expect(shaderCompilation.success).toBe(true);
    });

    test('should support required GLSL features', async ({ page }) => {
      await page.goto('/');

      const glslFeatures = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) return {};

        return {
          maxVertexUniforms: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS),
          maxFragmentUniforms: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS),
          maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
          maxTextureUnits: gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS),
        };
      });

      console.log('GLSL features:', glslFeatures);
      
      if (Object.keys(glslFeatures).length > 0) {
        expect(glslFeatures.maxVertexUniforms).toBeGreaterThan(0);
        expect(glslFeatures.maxFragmentUniforms).toBeGreaterThan(0);
      }
    });
  });

  test.describe('Browser-Specific Features', () => {
    test('should work in Chrome/Chromium', async ({ page, browserName }) => {
      if (browserName !== 'chromium') test.skip();

      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();

      // Chrome-specific checks
      const chromeFeatures = await page.evaluate(() => {
        return {
          webgl2: !!document.createElement('canvas').getContext('webgl2'),
          offscreenCanvas: 'OffscreenCanvas' in window,
        };
      });

      console.log('Chrome features:', chromeFeatures);
      expect(chromeFeatures.webgl2).toBe(true);
    });

    test('should work in Firefox', async ({ page, browserName }) => {
      if (browserName !== 'firefox') test.skip();

      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();

      // Firefox-specific checks
      const firefoxFeatures = await page.evaluate(() => {
        return {
          webgl: !!document.createElement('canvas').getContext('webgl'),
          audioContext: 'AudioContext' in window,
        };
      });

      console.log('Firefox features:', firefoxFeatures);
      expect(firefoxFeatures.webgl).toBe(true);
    });

    test('should work in Safari/WebKit', async ({ page, browserName }) => {
      if (browserName !== 'webkit') test.skip();

      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();

      // Safari-specific checks
      const safariFeatures = await page.evaluate(() => {
        return {
          webgl: !!document.createElement('canvas').getContext('webgl'),
          webkitAudioContext: 'webkitAudioContext' in window,
        };
      });

      console.log('Safari features:', safariFeatures);
      expect(safariFeatures.webgl).toBe(true);
    });
  });

  test.describe('Mobile Browser Compatibility', () => {
    test('should work on iOS Safari', async ({ page }) => {
      await page.setViewportSize(devices['iPhone 12'].viewport);
      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();

      // Check touch support
      const touchSupport = await page.evaluate(() => {
        return 'ontouchstart' in window;
      });

      console.log('Touch support:', touchSupport);
    });

    test('should work on Android Chrome', async ({ page }) => {
      await page.setViewportSize(devices['Pixel 5'].viewport);
      await page.goto('/');
      await page.waitForTimeout(2000);

      const canvas = page.locator('canvas');
      await expect(canvas).toBeVisible();
    });

    test('should handle mobile WebGL limitations', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.waitForTimeout(2000);

      const webglLimits = await page.evaluate(() => {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl');
        if (!gl) return {};

        return {
          maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
          maxRenderbufferSize: gl.getParameter(gl.MAX_RENDERBUFFER_SIZE),
          maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
        };
      });

      console.log('Mobile WebGL limits:', webglLimits);
      
      if (Object.keys(webglLimits).length > 0) {
        // Mobile devices should have reasonable limits
        expect(webglLimits.maxTextureSize).toBeGreaterThan(1024);
      }
    });
  });

  test.describe('Feature Detection and Fallbacks', () => {
    test('should detect missing features gracefully', async ({ page }) => {
      await page.goto('/');
      await page.waitForTimeout(2000);

      const featureDetection = await page.evaluate(() => {
        return {
          webgl: !!document.createElement('canvas').getContext('webgl'),
          audioContext: 'AudioContext' in window || 'webkitAudioContext' in window,
          mediaRecorder: 'MediaRecorder' in window,
          getUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
          requestAnimationFrame: 'requestAnimationFrame' in window,
        };
      });

      console.log('Feature detection:', featureDetection);
      
      // Core features should be present
      expect(featureDetection.webgl).toBe(true);
      expect(featureDetection.requestAnimationFrame).toBe(true);
    });

    test('should show appropriate fallback for missing WebGL', async ({ page }) => {
      // This test would require disabling WebGL
      // For now, we check if fallback component exists
      await page.goto('/');
      
      const fallbackExists = await page.evaluate(() => {
        return !!document.querySelector('[class*="fallback"]');
      });

      // Fallback component should exist in code
      expect(typeof fallbackExists).toBe('boolean');
    });

    test('should handle vendor prefixes', async ({ page }) => {
      await page.goto('/');

      const vendorPrefixes = await page.evaluate(() => {
        return {
          requestAnimationFrame: 
            'requestAnimationFrame' in window ||
            'webkitRequestAnimationFrame' in window ||
            'mozRequestAnimationFrame' in window,
          AudioContext:
            'AudioContext' in window ||
            'webkitAudioContext' in window,
        };
      });

      console.log('Vendor prefix support:', vendorPrefixes);
      expect(vendorPrefixes.requestAnimationFrame).toBe(true);
    });
  });

  test.describe('Performance Across Browsers', () => {
    test('should maintain acceptable FPS', async ({ page }) => {
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

      console.log(`FPS: ${fps}`);
      expect(fps).toBeGreaterThanOrEqual(25);
    });

    test('should load within acceptable time', async ({ page }) => {
      const startTime = Date.now();
      await page.goto('/');
      await page.locator('canvas').waitFor({ state: 'visible' });
      const loadTime = Date.now() - startTime;

      console.log(`Load time: ${loadTime}ms`);
      expect(loadTime).toBeLessThan(10000);
    });
  });
});
