# Requirements Document: Frontend-Backend Integration Fix

## Introduction

This document outlines the requirements for fixing the broken frontend-backend integration for Rose the Healer Shaman. The current implementation has critical issues preventing the 3D immersive frontend from connecting to the backend API, resulting in non-functional voice processing and broken visual styles.

## Glossary

- **Web Interface**: The FastAPI-based HTTP server that serves both the React frontend and REST API endpoints
- **Frontend Build**: The compiled React application (HTML, CSS, JS) output by Vite
- **API Endpoints**: REST endpoints for session management and voice processing
- **Static File Serving**: FastAPI's mechanism for serving compiled frontend assets
- **CORS**: Cross-Origin Resource Sharing configuration for API access
- **Build Output Directory**: The filesystem location where Vite outputs compiled frontend files
- **Development Server**: Local server for testing (Vite dev server + FastAPI backend)
- **Production Build**: Optimized, minified frontend build for deployment
- **Service Orchestration**: Running multiple services (frontend dev, backend API) simultaneously

## Requirements

### Requirement 1: Fix Build Output Path Configuration

**User Story:** As a developer, I want the frontend build to output to the correct directory that the backend expects, so that static files are served properly.

#### Acceptance Criteria

1. THE Frontend Build SHALL output compiled assets to `src/ai_companion/interfaces/web/static/` directory
2. THE Vite Configuration SHALL use `emptyOutDir: true` to clean the output directory before each build
3. THE Backend Web App SHALL correctly locate and serve static files from `src/ai_companion/interfaces/web/static/`
4. WHEN the frontend is built, THE Build Output Directory SHALL contain `index.html` and an `assets/` subdirectory
5. THE Build Configuration SHALL be documented with clear comments explaining the output path

### Requirement 2: Unified Development Server Configuration

**User Story:** As a developer, I want a single command to start both the frontend dev server and backend API, so that I can test the full integration locally.

#### Acceptance Criteria

1. THE Development Environment SHALL provide a command to start the FastAPI web server on port 8000
2. THE Vite Dev Server SHALL proxy API requests to `http://localhost:8000/api/v1/`
3. THE FastAPI Server SHALL enable CORS for `http://localhost:3000` during development
4. THE Development Setup SHALL be documented in a README with clear emoji-labeled steps
5. THE System SHALL log startup events with emoji indicators for easy visual scanning

### Requirement 3: Production Build and Serving

**User Story:** As a developer, I want to build and serve the production frontend through FastAPI, so that users can access the complete application.

#### Acceptance Criteria

1. WHEN the production build command is run, THE System SHALL compile the frontend with optimizations enabled
2. THE FastAPI Server SHALL serve the compiled `index.html` for all non-API routes (SPA routing)
3. THE FastAPI Server SHALL serve static assets from the `assets/` directory with proper cache headers
4. THE Production Build SHALL include all required CSS, JavaScript, and 3D assets
5. THE System SHALL log which files are being served with emoji indicators

### Requirement 4: API Endpoint Consistency

**User Story:** As a frontend developer, I want consistent API endpoint paths, so that the frontend can reliably communicate with the backend.

#### Acceptance Criteria

1. THE API Endpoints SHALL be accessible at `/api/v1/session/start` and `/api/v1/voice/process`
2. THE Frontend API Client SHALL use the correct base URL from environment variables
3. THE Backend SHALL return proper CORS headers for all API responses
4. THE System SHALL log all API requests with emoji indicators showing success/failure
5. THE Error Messages SHALL be user-friendly and actionable

### Requirement 5: Environment Configuration Management

**User Story:** As a developer, I want clear environment configuration, so that I can easily switch between development and production modes.

#### Acceptance Criteria

1. THE System SHALL use a `.env` file for development configuration
2. THE Frontend SHALL read `VITE_API_BASE_URL` from environment variables
3. THE Backend SHALL read allowed CORS origins from environment variables
4. THE Configuration SHALL have sensible defaults for local development
5. THE Environment Variables SHALL be documented with examples and descriptions

### Requirement 6: Eliminate Magic Numbers and Improve Observability

**User Story:** As a developer, I want all configuration values to be named constants with emoji logs, so that the code is self-documenting and easy to debug.

#### Acceptance Criteria

1. THE System SHALL define all port numbers, timeouts, and limits as named constants
2. THE Constants SHALL use SCREAMING_SNAKE_CASE naming convention
3. THE Log Messages SHALL include emoji indicators for visual scanning (🚀 start, ✅ success, ❌ error, 🔌 connection, 🎨 frontend, 🎤 voice)
4. THE Constants SHALL be grouped by concern (network, timeouts, file sizes, paths)
5. THE System SHALL validate configuration on startup and log any issues

### Requirement 7: Comprehensive Error Handling

**User Story:** As a user, I want clear error messages when something goes wrong, so that I understand what happened and how to fix it.

#### Acceptance Criteria

1. WHEN the backend is unreachable, THE Frontend SHALL display "Cannot connect to Rose. Please ensure the server is running."
2. WHEN voice processing fails, THE Frontend SHALL display the specific error from the backend
3. WHEN the microphone is denied, THE Frontend SHALL display "Microphone access denied. Please allow microphone access in your browser settings."
4. THE Error Messages SHALL auto-dismiss after 5 seconds for transient errors
5. THE System SHALL log all errors with stack traces and context

### Requirement 8: Development Workflow Documentation

**User Story:** As a new developer, I want clear documentation on how to run the application, so that I can get started quickly.

#### Acceptance Criteria

1. THE Documentation SHALL provide step-by-step setup instructions with emoji indicators
2. THE Documentation SHALL explain how to run development mode (frontend + backend)
3. THE Documentation SHALL explain how to build and run production mode
4. THE Documentation SHALL include troubleshooting steps for common issues
5. THE Documentation SHALL be located in a `DEVELOPMENT.md` file in the project root

### Requirement 9: Health Check and Monitoring

**User Story:** As a developer, I want to verify that all services are running correctly, so that I can quickly diagnose issues.

#### Acceptance Criteria

1. THE Backend SHALL provide a `/api/v1/health` endpoint that returns service status
2. THE Frontend SHALL check the health endpoint on startup
3. WHEN the health check fails, THE Frontend SHALL display a connection error
4. THE Health Endpoint SHALL return the API version and service status
5. THE System SHALL log health check results with emoji indicators

### Requirement 10: Asset Loading Verification

**User Story:** As a user, I want all 3D assets and styles to load correctly, so that the immersive experience works as designed.

#### Acceptance Criteria

1. THE Frontend SHALL display a loading screen while assets are loading
2. THE System SHALL log each asset load with emoji indicators (🎨 CSS, 🎭 3D models, 🎵 audio)
3. WHEN an asset fails to load, THE System SHALL log the error and display a fallback
4. THE Loading Screen SHALL show progress percentage
5. THE System SHALL verify that all critical assets loaded successfully before showing the main UI
