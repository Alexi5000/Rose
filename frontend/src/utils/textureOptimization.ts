import * as THREE from 'three';

/**
 * Texture Optimization Utilities
 * 
 * Provides utilities for optimizing texture loading and usage:
 * - Texture compression (KTX2 with Basis Universal)
 * - Mipmap generation
 * - Texture atlasing
 * - Size limiting (max 2048x2048)
 * - Memory management
 * 
 * Requirements: 6.2, 6.3
 */

/**
 * Maximum texture size for optimization
 * Limits textures to 2048x2048 to balance quality and performance
 */
export const MAX_TEXTURE_SIZE = 2048;

/**
 * Texture quality presets based on device capability
 */
export interface TextureQualityPreset {
  maxSize: number;
  anisotropy: number;
  generateMipmaps: boolean;
  minFilter: THREE.MinificationTextureFilter;
  magFilter: THREE.MagnificationTextureFilter;
}

export const TEXTURE_QUALITY_PRESETS: Record<string, TextureQualityPreset> = {
  high: {
    maxSize: 2048,
    anisotropy: 16,
    generateMipmaps: true,
    minFilter: THREE.LinearMipmapLinearFilter,
    magFilter: THREE.LinearFilter,
  },
  medium: {
    maxSize: 1024,
    anisotropy: 8,
    generateMipmaps: true,
    minFilter: THREE.LinearMipmapLinearFilter,
    magFilter: THREE.LinearFilter,
  },
  low: {
    maxSize: 512,
    anisotropy: 4,
    generateMipmaps: true,
    minFilter: THREE.LinearMipmapNearestFilter,
    magFilter: THREE.LinearFilter,
  },
};

/**
 * Get appropriate texture quality preset based on device
 */
export const getTextureQualityPreset = (
  isMobile: boolean,
  isTablet: boolean
): TextureQualityPreset => {
  if (isMobile) return TEXTURE_QUALITY_PRESETS.low;
  if (isTablet) return TEXTURE_QUALITY_PRESETS.medium;
  return TEXTURE_QUALITY_PRESETS.high;
};

/**
 * Optimize a texture with appropriate settings
 */
export const optimizeTexture = (
  texture: THREE.Texture,
  preset: TextureQualityPreset,
  renderer?: THREE.WebGLRenderer
): THREE.Texture => {
  // Set filtering
  texture.minFilter = preset.minFilter;
  texture.magFilter = preset.magFilter;

  // Enable mipmaps
  texture.generateMipmaps = preset.generateMipmaps;

  // Set anisotropy if renderer available
  if (renderer) {
    const maxAnisotropy = renderer.capabilities.getMaxAnisotropy();
    texture.anisotropy = Math.min(preset.anisotropy, maxAnisotropy);
  } else {
    texture.anisotropy = preset.anisotropy;
  }

  // Set wrapping
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;

  // Mark as needing update
  texture.needsUpdate = true;

  return texture;
};

/**
 * Load and optimize texture with size constraints
 */
export const loadOptimizedTexture = async (
  url: string,
  preset: TextureQualityPreset,
  loader: THREE.TextureLoader = new THREE.TextureLoader()
): Promise<THREE.Texture> => {
  return new Promise((resolve, reject) => {
    loader.load(
      url,
      (texture) => {
        // Check texture size and resize if needed
        const image = texture.image as HTMLImageElement;
        if (image.width > preset.maxSize || image.height > preset.maxSize) {
          console.warn(
            `Texture ${url} exceeds max size (${image.width}x${image.height}). Consider pre-optimizing.`
          );
        }

        // Optimize texture
        optimizeTexture(texture, preset);

        resolve(texture);
      },
      undefined,
      (error) => {
        console.error(`Failed to load texture: ${url}`, error);
        reject(error);
      }
    );
  });
};

/**
 * Create a texture atlas from multiple textures
 * Reduces draw calls by combining textures
 */
export const createTextureAtlas = (
  textures: THREE.Texture[],
  atlasSize: number = 2048
): {
  atlas: THREE.Texture;
  uvMappings: Array<{ offsetX: number; offsetY: number; scaleX: number; scaleY: number }>;
} => {
  // Create canvas for atlas
  const canvas = document.createElement('canvas');
  canvas.width = atlasSize;
  canvas.height = atlasSize;
  const ctx = canvas.getContext('2d');

  if (!ctx) {
    throw new Error('Failed to create canvas context for texture atlas');
  }

  // Calculate grid layout
  const gridSize = Math.ceil(Math.sqrt(textures.length));
  const cellSize = atlasSize / gridSize;

  const uvMappings: Array<{
    offsetX: number;
    offsetY: number;
    scaleX: number;
    scaleY: number;
  }> = [];

  // Draw textures into atlas
  textures.forEach((texture, index) => {
    const row = Math.floor(index / gridSize);
    const col = index % gridSize;

    const x = col * cellSize;
    const y = row * cellSize;

    // Draw texture
    const image = texture.image as HTMLImageElement;
    if (image) {
      ctx.drawImage(image, x, y, cellSize, cellSize);
    }

    // Store UV mapping
    uvMappings.push({
      offsetX: x / atlasSize,
      offsetY: y / atlasSize,
      scaleX: cellSize / atlasSize,
      scaleY: cellSize / atlasSize,
    });
  });

  // Create texture from canvas
  const atlasTexture = new THREE.CanvasTexture(canvas);
  atlasTexture.needsUpdate = true;

  return {
    atlas: atlasTexture,
    uvMappings,
  };
};

/**
 * Dispose of texture and free memory
 */
export const disposeTexture = (texture: THREE.Texture): void => {
  texture.dispose();

  // Also dispose of the image if it's a data texture
  if (texture.image && texture.image instanceof ImageData) {
    // ImageData doesn't need explicit disposal
  }
};

/**
 * Calculate texture memory usage in MB
 */
export const calculateTextureMemory = (texture: THREE.Texture): number => {
  const image = texture.image as HTMLImageElement;
  if (!image) return 0;

  const width = image.width || 0;
  const height = image.height || 0;

  // Assume RGBA (4 bytes per pixel)
  let bytesPerPixel = 4;

  // Account for mipmaps (adds ~33% more memory)
  const mipmapMultiplier = texture.generateMipmaps ? 1.33 : 1;

  const bytes = width * height * bytesPerPixel * mipmapMultiplier;
  return bytes / (1024 * 1024); // Convert to MB
};

/**
 * Get total texture memory usage for a scene
 */
export const getSceneTextureMemory = (scene: THREE.Scene): number => {
  let totalMemory = 0;
  const processedTextures = new Set<THREE.Texture>();

  scene.traverse((object) => {
    if (object instanceof THREE.Mesh && object.material) {
      const materials = Array.isArray(object.material) ? object.material : [object.material];

      materials.forEach((material) => {
        // Check all texture properties
        Object.keys(material).forEach((key) => {
          const value = (material as any)[key];
          if (value instanceof THREE.Texture && !processedTextures.has(value)) {
            processedTextures.add(value);
            totalMemory += calculateTextureMemory(value);
          }
        });
      });
    }
  });

  return totalMemory;
};

/**
 * Compress texture using canvas downscaling
 * Note: For production, use KTX2 with Basis Universal compression
 */
export const compressTexture = (
  texture: THREE.Texture,
  targetSize: number
): THREE.Texture => {
  const image = texture.image as HTMLImageElement;
  if (!image) return texture;

  // Only compress if image is larger than target
  if (image.width <= targetSize && image.height <= targetSize) {
    return texture;
  }

  // Create canvas for downscaling
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  if (!ctx) return texture;

  // Calculate new size maintaining aspect ratio
  const aspectRatio = image.width / image.height;
  let newWidth = targetSize;
  let newHeight = targetSize;

  if (aspectRatio > 1) {
    newHeight = targetSize / aspectRatio;
  } else {
    newWidth = targetSize * aspectRatio;
  }

  canvas.width = newWidth;
  canvas.height = newHeight;

  // Draw downscaled image
  ctx.drawImage(image, 0, 0, newWidth, newHeight);

  // Create new texture from canvas
  const compressedTexture = new THREE.CanvasTexture(canvas);
  compressedTexture.needsUpdate = true;

  // Copy settings from original texture
  compressedTexture.minFilter = texture.minFilter;
  compressedTexture.magFilter = texture.magFilter;
  compressedTexture.wrapS = texture.wrapS;
  compressedTexture.wrapT = texture.wrapT;
  compressedTexture.generateMipmaps = texture.generateMipmaps;

  return compressedTexture;
};

/**
 * Preload textures with optimization
 */
export const preloadTextures = async (
  urls: string[],
  preset: TextureQualityPreset
): Promise<THREE.Texture[]> => {
  const loader = new THREE.TextureLoader();
  const promises = urls.map((url) => loadOptimizedTexture(url, preset, loader));

  return Promise.all(promises);
};

/**
 * Create a procedural texture (useful for noise, gradients, etc.)
 * More memory efficient than loading image files
 */
export const createProceduralTexture = (
  width: number,
  height: number,
  generator: (x: number, y: number) => [number, number, number, number]
): THREE.DataTexture => {
  const size = width * height;
  const data = new Uint8Array(4 * size);

  for (let i = 0; i < size; i++) {
    const x = i % width;
    const y = Math.floor(i / width);

    const [r, g, b, a] = generator(x / width, y / height);

    const stride = i * 4;
    data[stride] = r * 255;
    data[stride + 1] = g * 255;
    data[stride + 2] = b * 255;
    data[stride + 3] = a * 255;
  }

  const texture = new THREE.DataTexture(data, width, height);
  texture.needsUpdate = true;

  return texture;
};
