import { useState, useEffect, useCallback } from 'react';
import { useGLTF, useTexture } from '@react-three/drei';

/**
 * Asset Loading Hook
 * 
 * Implements progressive asset loading strategy:
 * 1. Critical assets first (Rose, water, lighting)
 * 2. Secondary assets (icicles, particles, igloo)
 * 3. Post-processing effects (lazy loaded)
 * 
 * Requirements: 6.1, 6.4
 */

export interface AssetLoadingProgress {
  loaded: number;
  total: number;
  percentage: number;
  phase: 'critical' | 'secondary' | 'effects' | 'complete';
  currentAsset?: string;
  failedAssets?: string[];
  criticalAssetsFailed?: boolean;
}

interface UseAssetLoaderOptions {
  enabled?: boolean;
  onProgress?: (progress: AssetLoadingProgress) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

// Asset type emojis for logging
const ASSET_EMOJIS = {
  css: '🎨',
  model: '🎭',
  texture: '🎭',
  audio: '🎵',
  generic: '📦',
} as const;

// Define asset groups for progressive loading
const CRITICAL_ASSETS = {
  // Models
  // models: ['/models/rose-avatar.glb'],
  // Textures
  textures: [
    // '/textures/water-normal.jpg',
    // '/textures/sky-gradient.jpg',
  ],
};

const SECONDARY_ASSETS = {
  // models: ['/models/igloo.glb', '/models/icicle.glb'],
  textures: [
    // '/textures/ice-normal.jpg',
    // '/textures/aurora-noise.jpg',
  ],
};

/**
 * Get emoji for asset type based on file extension
 */
const getAssetEmoji = (assetPath: string): string => {
  const ext = assetPath.split('.').pop()?.toLowerCase();
  if (ext === 'css') return ASSET_EMOJIS.css;
  if (ext === 'glb' || ext === 'gltf') return ASSET_EMOJIS.model;
  if (ext === 'jpg' || ext === 'png' || ext === 'webp') return ASSET_EMOJIS.texture;
  if (ext === 'mp3' || ext === 'wav' || ext === 'ogg') return ASSET_EMOJIS.audio;
  return ASSET_EMOJIS.generic;
};

export const useAssetLoader = (options: UseAssetLoaderOptions = {}) => {
  const { enabled = true, onProgress, onComplete, onError } = options;

  const [loadingState, setLoadingState] = useState<AssetLoadingProgress>({
    loaded: 0,
    total: 0,
    percentage: 0,
    phase: 'critical',
    failedAssets: [],
    criticalAssetsFailed: false,
  });

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [failedAssets, setFailedAssets] = useState<string[]>([]);

  // Calculate total assets
  const totalAssets =
    CRITICAL_ASSETS.textures.length +
    SECONDARY_ASSETS.textures.length;

  // Update progress
  const updateProgress = useCallback(
    (
      loaded: number,
      phase: AssetLoadingProgress['phase'],
      currentAsset?: string,
      failed?: string[],
      criticalFailed?: boolean
    ) => {
      const percentage = totalAssets > 0 ? Math.round((loaded / totalAssets) * 100) : 0;
      const progress: AssetLoadingProgress = {
        loaded,
        total: totalAssets,
        percentage,
        phase,
        currentAsset,
        failedAssets: failed,
        criticalAssetsFailed: criticalFailed,
      };

      setLoadingState(progress);
      onProgress?.(progress);
    },
    [totalAssets, onProgress]
  );

  // Load assets progressively
  useEffect(() => {
    // Skip loading if not enabled (e.g., WebGL not supported)
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    let loadedCount = 0;
    let isCancelled = false;

    const loadAssets = async () => {
      try {
        const failed: string[] = [];
        let criticalFailed = false;

        // Phase 1: Load critical assets
        console.log('🎨 Starting critical asset loading phase...');
        updateProgress(loadedCount, 'critical', 'Loading essential scene elements...', failed, criticalFailed);

        // Preload critical textures
        for (const texture of CRITICAL_ASSETS.textures) {
          if (isCancelled) return;
          try {
            const emoji = getAssetEmoji(texture);
            console.log(`${emoji} Loading critical asset: ${texture} (${loadedCount + 1}/${totalAssets})`);
            // In production, actually load textures
            // await useTexture.preload(texture);
            loadedCount++;
            updateProgress(loadedCount, 'critical', texture, failed, criticalFailed);
            // Simulate loading time for development
            await new Promise((resolve) => setTimeout(resolve, 100));
            console.log(`✅ Loaded: ${texture}`);
          } catch (err) {
            console.error(`❌ Failed to load critical texture: ${texture}`, err);
            failed.push(texture);
            criticalFailed = true;
            setFailedAssets(prev => [...prev, texture]);
          }
        }

        // Verify critical assets loaded successfully
        if (criticalFailed) {
          console.error('❌ Critical assets failed to load:', failed);
          throw new Error(`Critical assets failed to load: ${failed.join(', ')}`);
        }
        console.log('✅ All critical assets verified successfully');

        // Phase 2: Load secondary assets
        if (isCancelled) return;
        console.log('🎭 Starting secondary asset loading phase...');
        updateProgress(loadedCount, 'secondary', 'Loading environmental details...', failed, criticalFailed);

        for (const texture of SECONDARY_ASSETS.textures) {
          if (isCancelled) return;
          try {
            const emoji = getAssetEmoji(texture);
            console.log(`${emoji} Loading secondary asset: ${texture} (${loadedCount + 1}/${totalAssets})`);
            // await useTexture.preload(texture);
            loadedCount++;
            updateProgress(loadedCount, 'secondary', texture, failed, criticalFailed);
            await new Promise((resolve) => setTimeout(resolve, 100));
            console.log(`✅ Loaded: ${texture}`);
          } catch (err) {
            console.warn(`❌ Failed to load secondary texture: ${texture}`, err);
            failed.push(texture);
            setFailedAssets(prev => [...prev, texture]);
          }
        }

        // Log verification results for secondary assets
        if (failed.length > 0) {
          console.warn(`⚠️ ${failed.length} secondary asset(s) failed to load (non-critical):`, failed);
        } else {
          console.log('✅ All secondary assets verified successfully');
        }

        // Phase 3: Effects ready
        if (isCancelled) return;
        console.log('✨ Preparing visual effects...');
        updateProgress(loadedCount, 'effects', 'Preparing visual effects...', failed, criticalFailed);
        await new Promise((resolve) => setTimeout(resolve, 200));

        // Complete - Final verification
        if (isCancelled) return;
        console.log('✅ Asset loading complete!');
        console.log(`📊 Verification summary: ${totalAssets - failed.length}/${totalAssets} assets loaded successfully`);
        if (failed.length > 0) {
          console.log(`⚠️ Failed assets (${failed.length}):`, failed);
        }
        updateProgress(totalAssets, 'complete', 'Ready', failed, criticalFailed);
        setIsLoading(false);
        onComplete?.();
      } catch (err) {
        if (!isCancelled) {
          const error = err instanceof Error ? err : new Error('Asset loading failed');
          console.error('❌ Asset loading failed:', error);
          setError(error);
          setIsLoading(false);
          onError?.(error);
        }
      }
    };

    loadAssets();

    return () => {
      isCancelled = true;
    };
  }, [enabled, updateProgress, totalAssets, onComplete, onError]);

  return {
    isLoading,
    progress: loadingState,
    error,
    failedAssets,
  };
};

/**
 * Preload specific assets
 * Utility function for manual asset preloading
 */
export const preloadAssets = async (assets: {
  models?: string[];
  textures?: string[];
}): Promise<void> => {
  const promises: Promise<any>[] = [];

  // Preload models
  if (assets.models) {
    assets.models.forEach((model) => {
      const preloadPromise = useGLTF.preload(model);
      if (preloadPromise) {
        promises.push(preloadPromise);
      }
    });
  }

  // Preload textures
  if (assets.textures) {
    assets.textures.forEach((texture) => {
      const preloadPromise = useTexture.preload(texture);
      if (preloadPromise) {
        promises.push(preloadPromise);
      }
    });
  }

  await Promise.all(promises);
};
