import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// 🎯 Build output path - matches backend static directory
const OUTPUT_DIR = '../src/ai_companion/interfaces/web/static'

// 🌐 API proxy configuration for development
const API_PROXY_TARGET = 'http://localhost:8000'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // 🎨 Build logging plugin for better observability
    {
      name: 'build-logger',
      buildStart() {
        console.log('🎨 Starting frontend build...')
      },
      buildEnd(error) {
        if (error) {
          console.error('❌ Build failed:', error)
        } else {
          console.log(`✅ Build complete! Output: ${OUTPUT_DIR}`)
        }
      }
    }
  ],
  build: {
    outDir: OUTPUT_DIR,
    emptyOutDir: true,
    target: 'es2020',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // Separate Three.js and R3F into their own chunks
          'three': ['three'],
          'r3f': ['@react-three/fiber', '@react-three/drei', '@react-three/postprocessing'],
          // Animation libraries in separate chunk
          'animations': ['gsap', 'framer-motion', 'lenis'],
          // React core
          'react-vendor': ['react', 'react-dom'],
        },
      },
    },
    // Chunk size warnings
    chunkSizeWarningLimit: 1000,
  },
  optimizeDeps: {
    include: ['three', '@react-three/fiber', '@react-three/drei'],
  },
  server: {
    port: 3000,
    // 🔌 Proxy API requests to backend server during development
    // This allows the frontend dev server to forward API calls to the FastAPI backend
    proxy: {
      '/api': {
        target: API_PROXY_TARGET,
        changeOrigin: true,
        secure: false,
      },
    },
  },
  // Asset optimization
  assetsInclude: ['**/*.glb', '**/*.gltf', '**/*.hdr', '**/*.exr'],
})
