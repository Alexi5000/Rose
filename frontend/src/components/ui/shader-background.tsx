/**
 * 🌊 WebGL Shader Background Component
 *
 * Animated shader with audio reactivity for both user input and Rose's voice.
 * State-based color transitions:
 * - Blue (idle)
 * - Purple (listening/user speaking)
 * - Pink (Rose speaking)
 */

import React, { useEffect, useRef } from 'react';

interface ShaderBackgroundProps {
  /** User microphone amplitude (0-1) */
  userAmplitude?: number;
  /** Rose voice amplitude (0-1) */
  roseAmplitude?: number;
  /** Current voice state for color shifts */
  state?: 'idle' | 'listening' | 'processing' | 'speaking';
}

const ShaderBackground: React.FC<ShaderBackgroundProps> = ({
  userAmplitude = 0,
  roseAmplitude = 0,
  state = 'idle',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Vertex shader source code
  const vsSource = `
    attribute vec4 aVertexPosition;
    void main() {
      gl_Position = aVertexPosition;
    }
  `;

  // Fragment shader source code with audio reactivity
  const fsSource = `
    precision highp float;
    uniform vec2 iResolution;
    uniform float iTime;
    uniform float uUserAmplitude;
    uniform float uRoseAmplitude;
    uniform float uStateBlend;

    const float overallSpeed = 0.2;
    const float gridSmoothWidth = 0.015;
    const float axisWidth = 0.05;
    const float majorLineWidth = 0.025;
    const float minorLineWidth = 0.0125;
    const float majorLineFrequency = 5.0;
    const float minorLineFrequency = 1.0;
    const vec4 gridColor = vec4(0.5);
    const float scale = 5.0;
    const vec4 lineColor = vec4(0.4, 0.2, 0.8, 1.0);
    const float minLineWidth = 0.01;
    const float maxLineWidth = 0.2;
    const float lineSpeed = 1.0 * overallSpeed;
    const float lineAmplitude = 1.0;
    const float lineFrequency = 0.2;
    const float warpSpeed = 0.2 * overallSpeed;
    const float warpFrequency = 0.5;
    const float warpAmplitude = 1.0;
    const float offsetFrequency = 0.5;
    const float offsetSpeed = 1.33 * overallSpeed;
    const float minOffsetSpread = 0.6;
    const float maxOffsetSpread = 2.0;
    const int linesPerGroup = 16;

    #define drawCircle(pos, radius, coord) smoothstep(radius + gridSmoothWidth, radius, length(coord - (pos)))
    #define drawSmoothLine(pos, halfWidth, t) smoothstep(halfWidth, 0.0, abs(pos - (t)))
    #define drawCrispLine(pos, halfWidth, t) smoothstep(halfWidth + gridSmoothWidth, halfWidth, abs(pos - (t)))
    #define drawPeriodicLine(freq, width, t) drawCrispLine(freq / 2.0, width, abs(mod(t, freq) - (freq) / 2.0))

    float drawGridLines(float axis) {
      return drawCrispLine(0.0, axisWidth, axis)
            + drawPeriodicLine(majorLineFrequency, majorLineWidth, axis)
            + drawPeriodicLine(minorLineFrequency, minorLineWidth, axis);
    }

    float drawGrid(vec2 space) {
      return min(1.0, drawGridLines(space.x) + drawGridLines(space.y));
    }

    float random(float t) {
      return (cos(t) + cos(t * 1.3 + 1.3) + cos(t * 1.4 + 1.4)) / 3.0;
    }

    float getPlasmaY(float x, float horizontalFade, float offset, float audioBoost) {
      float baseFreq = lineFrequency * (1.0 + audioBoost * 0.5);
      return random(x * baseFreq + iTime * lineSpeed) * horizontalFade * lineAmplitude * (1.0 + audioBoost * 0.3) + offset;
    }

    void main() {
      vec2 fragCoord = gl_FragCoord.xy;
      vec4 fragColor;
      vec2 uv = fragCoord.xy / iResolution.xy;
      vec2 space = (fragCoord - iResolution.xy / 2.0) / iResolution.x * 2.0 * scale;

      float horizontalFade = 1.0 - (cos(uv.x * 6.28) * 0.5 + 0.5);
      float verticalFade = 1.0 - (cos(uv.y * 6.28) * 0.5 + 0.5);

      // Audio-reactive warping
      float totalAudio = uUserAmplitude + uRoseAmplitude;
      space.y += random(space.x * warpFrequency + iTime * warpSpeed) * warpAmplitude * (0.5 + horizontalFade) * (1.0 + totalAudio * 0.5);
      space.x += random(space.y * warpFrequency + iTime * warpSpeed + 2.0) * warpAmplitude * horizontalFade * (1.0 + totalAudio * 0.3);

      vec4 lines = vec4(0.0);

      // State-based background colors
      vec4 idleColor1 = vec4(0.1, 0.1, 0.3, 1.0);
      vec4 idleColor2 = vec4(0.3, 0.1, 0.5, 1.0);
      vec4 listeningColor1 = vec4(0.2, 0.1, 0.4, 1.0);
      vec4 listeningColor2 = vec4(0.4, 0.2, 0.6, 1.0);
      vec4 speakingColor1 = vec4(0.3, 0.1, 0.3, 1.0);
      vec4 speakingColor2 = vec4(0.5, 0.2, 0.4, 1.0);

      vec4 bgColor1 = mix(idleColor1, listeningColor1, uStateBlend * 0.5);
      bgColor1 = mix(bgColor1, speakingColor1, uStateBlend);
      vec4 bgColor2 = mix(idleColor2, listeningColor2, uStateBlend * 0.5);
      bgColor2 = mix(bgColor2, speakingColor2, uStateBlend);

      for(int l = 0; l < linesPerGroup; l++) {
        float normalizedLineIndex = float(l) / float(linesPerGroup);
        float offsetTime = iTime * offsetSpeed;
        float offsetPosition = float(l) + space.x * offsetFrequency;
        float rand = random(offsetPosition + offsetTime) * 0.5 + 0.5;

        // Audio-reactive line width
        float audioBoost = uUserAmplitude * 2.0 + uRoseAmplitude * 1.5;
        float halfWidth = mix(minLineWidth, maxLineWidth, rand * horizontalFade * (1.0 + audioBoost * 0.4)) / 2.0;
        float offset = random(offsetPosition + offsetTime * (1.0 + normalizedLineIndex)) * mix(minOffsetSpread, maxOffsetSpread, horizontalFade);

        float linePosition = getPlasmaY(space.x, horizontalFade, offset, audioBoost);
        float line = drawSmoothLine(linePosition, halfWidth, space.y) / 2.0 + drawCrispLine(linePosition, halfWidth * 0.15, space.y);

        float circleX = mod(float(l) + iTime * lineSpeed, 25.0) - 12.0;
        vec2 circlePosition = vec2(circleX, getPlasmaY(circleX, horizontalFade, offset, audioBoost));
        float circle = drawCircle(circlePosition, 0.01 * (1.0 + totalAudio * 0.5), space) * 4.0;

        line = line + circle;

        // Color shift based on audio source
        vec4 userColor = vec4(0.6, 0.3, 0.9, 1.0); // Purple for user
        vec4 roseColor = vec4(0.9, 0.4, 0.7, 1.0);  // Pink for Rose
        vec4 finalLineColor = mix(lineColor, userColor, uUserAmplitude);
        finalLineColor = mix(finalLineColor, roseColor, uRoseAmplitude * 0.8);

        lines += line * finalLineColor * rand;
      }

      fragColor = mix(bgColor1, bgColor2, uv.x);
      fragColor *= verticalFade;
      fragColor.a = 1.0;
      fragColor += lines;

      gl_FragColor = fragColor;
    }
  `;

  // Helper function to compile shader
  const loadShader = (
    gl: WebGLRenderingContext,
    type: number,
    source: string
  ): WebGLShader | null => {
    const shader = gl.createShader(type);
    if (!shader) return null;

    gl.shaderSource(shader, source);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error('🔴 Shader compile error:', gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }

    return shader;
  };

  // Initialize shader program
  const initShaderProgram = (
    gl: WebGLRenderingContext,
    vsSource: string,
    fsSource: string
  ): WebGLProgram | null => {
    const vertexShader = loadShader(gl, gl.VERTEX_SHADER, vsSource);
    const fragmentShader = loadShader(gl, gl.FRAGMENT_SHADER, fsSource);

    if (!vertexShader || !fragmentShader) return null;

    const shaderProgram = gl.createProgram();
    if (!shaderProgram) return null;

    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
      console.error('🔴 Shader program link error:', gl.getProgramInfoLog(shaderProgram));
      return null;
    }

    return shaderProgram;
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl');
    if (!gl) {
      console.warn('⚠️ WebGL not supported');
      return;
    }

    const shaderProgram = initShaderProgram(gl, vsSource, fsSource);
    if (!shaderProgram) return;

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = [-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0];
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(positions), gl.STATIC_DRAW);

    const programInfo = {
      program: shaderProgram,
      attribLocations: {
        vertexPosition: gl.getAttribLocation(shaderProgram, 'aVertexPosition'),
      },
      uniformLocations: {
        resolution: gl.getUniformLocation(shaderProgram, 'iResolution'),
        time: gl.getUniformLocation(shaderProgram, 'iTime'),
        userAmplitude: gl.getUniformLocation(shaderProgram, 'uUserAmplitude'),
        roseAmplitude: gl.getUniformLocation(shaderProgram, 'uRoseAmplitude'),
        stateBlend: gl.getUniformLocation(shaderProgram, 'uStateBlend'),
      },
    };

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    const startTime = Date.now();
    let animationId: number;

    const render = () => {
      const currentTime = (Date.now() - startTime) / 1000;

      // Calculate state blend for smooth color transitions
      let stateBlend = 0;
      if (state === 'listening' || state === 'processing') {
        stateBlend = 0.5; // Purple-ish
      } else if (state === 'speaking') {
        stateBlend = 1.0; // Pink-ish
      }

      gl.clearColor(0.0, 0.0, 0.0, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      gl.useProgram(programInfo.program);

      gl.uniform2f(programInfo.uniformLocations.resolution, canvas.width, canvas.height);
      gl.uniform1f(programInfo.uniformLocations.time, currentTime);
      gl.uniform1f(programInfo.uniformLocations.userAmplitude, userAmplitude);
      gl.uniform1f(programInfo.uniformLocations.roseAmplitude, roseAmplitude);
      gl.uniform1f(programInfo.uniformLocations.stateBlend, stateBlend);

      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
      gl.vertexAttribPointer(
        programInfo.attribLocations.vertexPosition,
        2,
        gl.FLOAT,
        false,
        0,
        0
      );
      gl.enableVertexAttribArray(programInfo.attribLocations.vertexPosition);

      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      animationId = requestAnimationFrame(render);
    };

    animationId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationId);
    };
  }, [userAmplitude, roseAmplitude, state]);

  return <canvas ref={canvasRef} className="fixed top-0 left-0 w-full h-full -z-10" />;
};

export default ShaderBackground;
