/**
 * 🎨 Render Smoke Test
 *
 * Verifies the app renders without crashing and basic elements are present.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '@/App';

console.log('🎨 Loading render tests');

// Mock WebGL context
const mockGetContext = vi.fn(() => ({
  canvas: {},
  drawingBufferWidth: 800,
  drawingBufferHeight: 600,
  getExtension: vi.fn(),
  getParameter: vi.fn(),
  createShader: vi.fn(() => ({})),
  shaderSource: vi.fn(),
  compileShader: vi.fn(),
  getShaderParameter: vi.fn(() => true),
  createProgram: vi.fn(() => ({})),
  attachShader: vi.fn(),
  linkProgram: vi.fn(),
  getProgramParameter: vi.fn(() => true),
  useProgram: vi.fn(),
  createBuffer: vi.fn(() => ({})),
  bindBuffer: vi.fn(),
  bufferData: vi.fn(),
  getAttribLocation: vi.fn(() => 0),
  getUniformLocation: vi.fn(() => ({})),
  enableVertexAttribArray: vi.fn(),
  vertexAttribPointer: vi.fn(),
  uniform1f: vi.fn(),
  uniform2f: vi.fn(),
  clearColor: vi.fn(),
  clear: vi.fn(),
  viewport: vi.fn(),
  drawArrays: vi.fn(),
  COLOR_BUFFER_BIT: 16384,
  ARRAY_BUFFER: 34962,
  STATIC_DRAW: 35044,
  FLOAT: 5126,
  VERTEX_SHADER: 35633,
  FRAGMENT_SHADER: 35632,
  COMPILE_STATUS: 35713,
  LINK_STATUS: 35714,
  TRIANGLE_STRIP: 5,
}));

describe('🎨 App Rendering', () => {
  beforeEach(() => {
    console.log('  🔧 Setting up WebGL mock');
    // Mock canvas getContext for WebGL
    HTMLCanvasElement.prototype.getContext = mockGetContext as any;

    // Mock canvas width/height
    Object.defineProperty(HTMLCanvasElement.prototype, 'width', {
      get: () => 800,
      set: vi.fn(),
    });
    Object.defineProperty(HTMLCanvasElement.prototype, 'height', {
      get: () => 600,
      set: vi.fn(),
    });
  });

  it('✅ renders without crashing', () => {
    console.log('  🔍 Testing basic render');

    expect(() => {
      render(<App />);
    }).not.toThrow();

    console.log('  ✅ App rendered successfully');
  });

  it('✅ creates shader canvas element', () => {
    console.log('  🔍 Testing canvas element presence');

    render(<App />);

    const canvas = document.querySelector('canvas');
    expect(canvas).toBeInTheDocument();
    expect(canvas).toHaveClass('fixed', 'top-0', 'left-0');

    console.log('  ✅ Canvas element found');
  });

  it('✅ initializes WebGL context', () => {
    console.log('  🔍 Testing WebGL initialization');

    render(<App />);

    // Verify getContext was called for WebGL
    expect(mockGetContext).toHaveBeenCalledWith('webgl');

    console.log('  ✅ WebGL context initialized');
  });

  it('✅ has interactive overlay', () => {
    console.log('  🔍 Testing interactive overlay');

    render(<App />);

    // Find the wrapper div (clickable area)
    const wrapper = document.querySelector('[role="button"]');
    expect(wrapper).toBeInTheDocument();
    expect(wrapper).toHaveClass('fixed', 'inset-0');

    console.log('  ✅ Interactive overlay present');
  });

  it('✅ renders memory privacy controls', () => {
    console.log('  🔍 Testing memory controls');

    render(<App />);

    expect(screen.getByLabelText('Session-only memory')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Export' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Forget' })).toBeInTheDocument();

    console.log('  ✅ Memory controls present');
  });

  it('✅ renders safety boundary copy', () => {
    console.log('  🔍 Testing safety boundary copy');

    render(<App />);

    expect(screen.getByText(/Rose is AI emotional support/i)).toBeInTheDocument();
    expect(screen.getByText(/call or text 988/i)).toBeInTheDocument();

    console.log('  ✅ Safety boundary copy present');
  });

  it('✅ renders without console errors', () => {
    console.log('  🔍 Testing for console errors');

    const consoleError = vi.spyOn(console, 'error');

    render(<App />);

    expect(consoleError).not.toHaveBeenCalled();

    consoleError.mockRestore();

    console.log('  ✅ No console errors detected');
  });
});

console.log('✅ Render tests loaded');
