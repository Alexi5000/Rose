# Implementation Plan: Frontend-Backend Integration Fix

## Overview

This plan fixes the broken frontend-backend integration by:

1. Correcting build output paths
2. Creating unified development workflow
3. Eliminating magic numbers with named constants
4. Adding emoji logging for observability
5. Improving error handling and documentation

## Task List

- [ ] 1. Create Configuration Constants Module

- [x] 1.1 Create server configuration file with all constants

  - Create `src/ai_companion/config/server_config.py`
  - Define network configuration constants (ports, hosts)
  - Define path configuration constants (build directories)
  - Define timeout configuration constants
  - Define file size limit constants
  - Define rate limiting constants
  - Define cache configuration constants
  - Define cleanup configuration constants
  - Define CORS configuration constants
  - Add docstrings with emoji indicators for each section
  - _Requirements: 1.5, 5.1, 5.4, 6.1, 6.2, 6.3, 6.4_

- [x] 1.2 Update settings.py to import and use new constants

  - Import constants from `server_config.py`
  - Replace hardcoded values with named constants
  - Ensure backward compatibility with existing settings
  - _Requirements: 5.2, 5.3, 6.1_

- [x] 2. Fix Vite Build Configuration

- [x] 2.1 Update Vite config with correct output path

  - Modify `frontend/vite.config.ts`
  - Set `outDir` to `../src/ai_companion/interfaces/web/static`
  - Ensure `emptyOutDir: true` is set
  - Add path constant at top of file with emoji comment
  - _Requirements: 1.1, 1.2, 1.4, 1.5_

- [x] 2.2 Add build logging plugin to Vite config

  - Create custom Vite plugin for build event logging
  - Log build start with 🎨 emoji
  - Log build completion with ✅ emoji and output path
  - Log any build errors with ❌ emoji
  - _Requirements: 6.3, 10.2_

- [x] 2.3 Configure API proxy for development mode

  - Update `server.proxy` configuration in Vite config
  - Proxy `/api` requests to `http://localhost:8000`
  - Set `changeOrigin: true` and `secure: false`
  - Add comment explaining proxy purpose

  - _Requirements: 2.2, 2.3_

- [x] 2.4 Update frontend environment configuration

  - Update `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8000/api/v1`
  - Update `frontend/.env.example` with same value
  - Add comments explaining each environment variable
  - _Requirements: 5.1, 5.2, 5.5_

- [x] 3. Update FastAPI Backend Server

- [x] 3.1 Update app.py to use configuration constants

  - Import constants from `server_config.py`
  - Replace hardcoded `FRONTEND_BUILD_DIR` path
  - Replace hardcoded port numbers
  - Replace hardcoded timeout values
  - Replace hardcoded cache header values
  - _Requirements: 1.3, 6.1, 6.2_

- [x] 3.2 Add emoji logging to app.py startup

  - Add 🚀 emoji to app startup log
  - Add ✅ emoji to successful initialization logs
  - Add 🎨 emoji to frontend serving logs
  - Add ❌ emoji to error logs
  - Add 🔌 emoji to server binding logs
  - _Requirements: 2.5, 6.3_

- [x] 3.3 Fix static file serving path

  - Verify `FRONTEND_BUILD_DIR` points to correct location
  - Update static file mount to use `FRONTEND_BUILD_DIR / "assets"`
  - Add existence check with clear error message if build not found
  - Log which directory is being served
  - _Requirements: 1.3, 3.1, 3.2, 3.3_

- [x] 3.4 Update CORS configuration for development

  - Import `DEV_ALLOWED_ORIGINS` from config
  - Update CORS middleware to use config constant
  - Ensure `http://localhost:3000` is in allowed origins for dev
  - Log allowed origins on startup
  - _Requirements: 2.3, 4.3, 5.3_

- [x] 3.5 Add cache headers using configuration constants

  - Update cache header middleware to use constants
  - Use `STATIC_ASSET_CACHE_SECONDS` for /assets routes
  - Use `HTML_CACHE_SECONDS` for HTML files
  - Use `API_CACHE_SECONDS` (0) for API routes
  - _Requirements: 3.3, 6.1_

- [x] 4. Update Voice Processing Route

- [x] 4.1 Add emoji logging to voice.py

  - Add 🎤 emoji to voice processing start log
  - Add ✅ emoji to successful transcription log
  - Add 🔊 emoji to audio generation log
  - Add ❌ emoji to error logs
  - Add 📊 emoji to metrics logs
  - _Requirements: 4.5, 6.3, 7.3_

- [x] 4.2 Improve error messages in voice.py

  - Update error messages to be user-friendly
  - Use constants from config for error messages

  - Ensure errors include actionable guidance
  - _Requirements: 4.4, 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4.3 Use configuration constants in voice.py

  - Replace `MAX_AUDIO_SIZE` with constant from config
  - Replace timeout values with constants
  - Replace cleanup intervals with constants
  - _Requirements: 6.1, 6.2_

- [x] 5. Create Development Server Script

- [x] 5.1 Create run_dev_server.py script

  - Create `scripts/run_dev_server.py`
  - Import subprocess and Path modules
  - Define functions to start backend and frontend
  - Add emoji logging for each step (🚀 🔌 🎨)

  - Handle Ctrl+C gracefully to stop both servers
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 5.2 Add backend server startup function

  - Start uvicorn with reload flag
  - Use port 8000
  - Log startup with 🔌 emoji
  - Return process handle
  - _Requirements: 2.1, 2.5_

- [x] 5.3 Add frontend server startup function

  - Start npm run dev in frontend directory
  - Log startup with 🎨 emoji
  - Return process handle

  - _Requirements: 2.1, 2.5_

- [x] 5.4 Add startup summary with URLs

  - Print clear summary of running servers
  - Show frontend URL (http://localhost:3000)
  - Show backend URL (http://localhost:8000)
  - Show API docs URL (http://localhost:8000/api/v1/docs)

  - Add instructions to press Ctrl+C to stop
  - _Requirements: 2.4, 2.5_

- [x] 5.5 Make script executable

  - Add shebang line `#!/usr/bin/env python3`
  - Set executable permissions on Unix systems
  - Test script runs correctly
  - _Requirements: 2.1_

- [x] 6. Create Production Build Script

- [x] 6.1 Create build_and_serve.py script

  - Create `scripts/build_and_serve.py`
  - Add function to build frontend
  - Add function to start production server
  - Add emoji logging for each step
  - _Requirements: 3.1, 3.2_

- [x] 6.2 Add frontend build function

  - Run `npm run build` in frontend directory
  - Check exit code and fail if build fails
  - Log build start with 🎨 emoji
  - Log build success with ✅ emoji
  - _Requirements: 3.1, 3.4_

- [ ] 6.3 Add production server startup function

  - Start uvicorn without reload flag
  - Bind to 0.0.0.0:8000
  - Log startup with 🚀 emoji

  - _Requirements: 3.2, 3.3_

- [x] 6.4 Make script executable

  - Add shebang line
  - Set executable permissions
  - Test script runs correctly
  - _Requirements: 3.1_

- [x] 7. Update Frontend API Client

- [x] 7.1 Add emoji logging to apiClient.ts

  - Add 🔌 emoji to initialization log
  - Add 📤 emoji to request logs
  - Add ✅ emoji to successful response logs
  - Add ❌ emoji to error logs
  - Log API base URL on initialization
  - _Requirements: 4.5, 6.3_

- [x] 7.2 Improve error messages in apiClient.ts

  - Update error interceptor with user-friendly messages
  - Map common errors to helpful messages
  - Include actionable guidance in error messages
  - _Requirements: 4.4, 7.1, 7.2, 7.5_

- [x] 7.3 Add request/response logging interceptors

  - Log all outgoing requests with method and URL
  - Log all responses with status code
  - Log errors with full context
  - _Requirements: 6.3, 9.5_

- [x] 8. Add Health Check System

- [x] 8.1 Create useHealthCheck hook

  - Create `frontend/src/hooks/useHealthCheck.ts`
  - Call `/api/v1/health` endpoint on mount
  - Return health status and error state

  - Add emoji logging (🏥 for check, ✅ for success, ❌ for failure)
  - _Requirements: 9.1, 9.2, 9.3, 9.5_

- [x] 8.2 Integrate health check into App.tsx

  - Import and use useHealthCheck hook
  - Display connection error if health check fails
  - Show loading state during health check
  - _Requirements: 9.2, 9.3, 9.5_

- [x] 8.3 Update health endpoint to return version

  - Modify `/api/v1/health` to include API version
  - Include service status in response
  - Log health check requests
  - _Requirements: 9.4, 9.5_

- [ ] 9. Improve Asset Loading

- [x] 9.1 Add asset loading logs to useAssetLoader

  - Add 🎨 emoji for CSS loading
  - Add 🎭 emoji for 3D model loading
  - Add 🎵 emoji for audio loading

  - Log each asset load with progress
  - _Requirements: 10.2, 10.3_

- [x] 9.2 Add asset load verification

  - Check that critical assets loaded successfully
  - Log verification results with emoji
  - Display error if critical assets fail
  - _Requirements: 10.3, 10.5_

- [x] 9.3 Update loading screen with detailed progress

  - Show which asset is currently loading
  - Display progress percentage
  - Show emoji indicator for asset type
  - _Requirements: 10.1, 10.4_

- [x] 10. Create Development Documentation

- [ ]\* 10.1 Create DEVELOPMENT.md file

  - Create `DEVELOPMENT.md` in project root
  - Add Quick Start section with emoji headers
  - Add Development Mode instructions
  - Add Production Mode instructions
  - _Requirements: 8.1, 8.2, 8.3_

- [ ]\* 10.2 Add troubleshooting section

  - Document "Cannot connect to Rose" issue
  - Document "Styles not loading" issue
  - Document "Voice processing error" issue
  - Provide solutions with emoji indicators
  - _Requirements: 8.4, 8.5_

- [ ]\* 10.3 Add configuration reference

  - Document all environment variables
  - Provide examples for each variable
  - Explain purpose of each configuration
  - _Requirements: 5.5, 8.5_

- [ ]\* 10.4 Add testing checklist

  - Create manual testing checklist
  - Add automated testing commands
  - Include deployment reference
  - _Requirements: 8.2, 8.3, 8.5_

-

- [ ] 11. Update Error Handling


- [x] 11.1 Create error message constants in frontend

  - Create `frontend/src/config/errorMessages.ts`
  - Define all user-facing error messages with emojis
  - Use descriptive constant names
  - _Requirements: 6.1, 6.4, 7.1, 7.2, 7.3, 7.4_

- [x] 11.2 Update useVoiceInteraction error handling

  - Import error message constants
  - Use constants instead of hardcoded strings
  - Ensure all errors have emoji indicators
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 11.3 Add auto-dismiss for transient errors

  - Implement 5-second auto-dismiss for transient errors
  - Keep critical errors visible until dismissed
  - Log error dismissal events
  - _Requirements: 7.4_

- [ ] 12. Testing and Verification

- [ ] 12.1 Test development mode workflow

  - Run `python scripts/run_dev_server.py`
  - Verify both servers start successfully
  - Verify frontend loads at http://localhost:3000
  - Verify API accessible at http://localhost:8000/api/v1
  - Verify hot reload works for both frontend and backend
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 12.2 Test production build workflow

  - Run `python scripts/build_and_serve.py`
  - Verify frontend builds successfully
  - Verify build output in correct directory
  - Verify server serves static files correctly
  - Verify all assets load (CSS, JS, 3D models)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [ ] 12.3 Test voice interaction end-to-end

  - Open frontend in browser
  - Click voice button
  - Grant microphone permission
  - Record voice input
  - Verify backend processes request
  - Verify audio response plays
  - Check all logs have emoji indicators
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 12.4 Test error scenarios

  - Test with backend stopped (connection error)
  - Test with microphone denied (permission error)
  - Test with invalid audio (validation error)
  - Verify error messages are user-friendly
  - Verify errors auto-dismiss after 5 seconds
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 12.5 Test health check system

  - Verify health check runs on app startup
  - Test with backend running (should pass)
  - Test with backend stopped (should fail with clear message)
  - Verify health check logs have emoji indicators
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 12.6 Verify all magic numbers eliminated

  - Search codebase for hardcoded numbers
  - Ensure all ports, timeouts, sizes use named constants
  - Verify constants are properly documented
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 12.7 Verify emoji logging throughout

  - Check all log statements have appropriate emojis
  - Verify logs are easy to scan visually
  - Test log output in development and production
  - _Requirements: 6.3, 6.5_

- [ ] 13. Update Project Documentation

- [ ]\* 13.1 Update main README.md

  - Add link to DEVELOPMENT.md
  - Update quick start instructions
  - Add emoji indicators to sections
  - _Requirements: 8.1, 8.5_

- [ ]\* 13.2 Update existing documentation

  - Update any references to old build paths
  - Update any references to old server commands
  - Ensure consistency across all docs
  - _Requirements: 8.5_

- [ ]\* 13.3 Add deployment notes
  - Document production build process
  - Document environment variable requirements
  - Add troubleshooting for common deployment issues
  - _Requirements: 8.3, 8.4, 8.5_
