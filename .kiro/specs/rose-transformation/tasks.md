# Implementation Plan: Rose the Healer Shaman

## Task List

- [x] 1. Update character profile and prompts

- [x] 1.1 Replace Ava's character card with Rose's healer shaman profile in CHARACTER_CARD_PROMPT

  - Define Rose as a grief counselor and healer trained in ancient healing traditions
  - Update personality traits: empathetic, grounding, spiritually aware, warm
  - Remove all Ava-specific details (Groq ML Engineer, San Francisco, tech interests)
  - Add therapeutic approach and ancient wisdom focus
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.2 Update MEMORY_ANALYSIS_PROMPT to prioritize therapeutic context

  - Add examples for emotional states, grief experiences, and healing goals
  - Update extraction rules to focus on therapeutic information
  - _Requirements: 4.1, 4.3_

- [x] 1.3 Update ROUTER_PROMPT to remove image generation logic

  - Remove all image-related decision rules
  - Simplify to only choose between 'conversation' and 'audio'
  - Default to 'audio' for voice-first experience
  - _Requirements: 6.4_

- [x] 1.4 Update context injection for Rose's healing activities

  - Modify ScheduleContextGenerator or remove schedule dependency
  - Replace with simple "available for healing sessions" context
  - _Requirements: 1.1_

- [x] 2. Simplify LangGraph workflow

- [x] 2.1 Update graph.py to disable image workflow path

  - Remove image_node from conditional edges in select_workflow
  - Keep image_node code but don't add to graph
  - Update workflow to only route to conversation_node or audio_node
  - _Requirements: 6.1, 6.4_

- [x] 2.2 Update router_node to only return 'conversation' or 'audio'

  - Modify router logic to exclude 'image' option
  - Set default to 'audio' for voice interactions
  - _Requirements: 2.3, 6.4_

- [x] 2.3 Update edges.py select_workflow function

  - Remove image workflow routing logic
  - Ensure only conversation and audio paths are active
  - _Requirements: 6.4_

- [x] 2.4 Verify memory nodes work with Rose's therapeutic context

  - Test memory extraction with grief counseling conversations
  - Verify memory injection provides relevant therapeutic context
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Create FastAPI web interface backend

- [x] 3.1 Create new web interface module structure

  - Create src/ai_companion/interfaces/web/ directory
  - Create app.py for FastAPI application
  - Create routes/ directory for endpoint modules
  - _Requirements: 5.1, 7.3_

- [x] 3.2 Implement voice processing endpoint (POST /api/voice/process)

  - Accept multipart/form-data with audio file
  - Validate audio format and size (max 10MB)
  - Use Groq Whisper API for speech-to-text transcription
  - Pass transcribed text to LangGraph workflow with session_id
  - Generate audio response using TTS
  - Save audio file temporarily and return URL
  - Return JSON with text, audio_url, and session_id
  - _Requirements: 2.2, 2.3, 2.4, 3.2_

- [x] 3.3 Implement session management endpoint (POST /api/session/start)

  - Generate unique session_id
  - Initialize LangGraph checkpointer with session_id
  - Return session_id to frontend
  - _Requirements: 4.2_

- [x] 3.4 Implement audio serving endpoint (GET /api/voice/audio/{audio_id})

  - Serve generated audio files as streaming response
  - Set appropriate content-type headers (audio/mpeg)
  - Implement cleanup for old audio files
  - _Requirements: 2.5_

- [x] 3.5 Implement health check endpoint (GET /api/health)

  - Return system status and version
  - Check connectivity to Groq API, Qdrant
  - _Requirements: 7.4_

- [x] 3.6 Configure CORS middleware for frontend access

  - Allow requests from frontend origin
  - Configure appropriate headers
  - _Requirements: 5.3_

- [x] 3.7 Add static file serving for React frontend

  - Configure FastAPI to serve React build files
  - Set up catch-all route for React Router
  - _Requirements: 7.3_

- [x] 4. Implement Groq API integration improvements

- [x] 4.1 Verify Groq STT (Whisper) integration

  - Test speech-to-text with various audio formats
  - Implement error handling and retries
  - Add timeout configuration (60s)
  - _Requirements: 3.2, 3.4_

- [x] 4.2 Update model configurations in settings.py

  - Set TEXT_MODEL_NAME to "llama-3.3-70b-versatile"
  - Set SMALL_TEXT_MODEL_NAME to "llama-3.1-8b-instant"
  - Set STT_MODEL_NAME to "whisper-large-v3"
  - Add ROSE_VOICE_ID configuration for TTS
  - _Requirements: 3.3_

- [x] 4.3 Implement retry logic with exponential backoff for Groq API calls

  - Add retry decorator for API calls
  - Configure max retries (3) and backoff strategy
  - Log all retry attempts
  - _Requirements: 3.4, 9.1_

- [x] 4.4 Add comprehensive error handling for API failures

  - Catch and log Groq API errors
  - Return user-friendly error messages
  - Implement fallback strategies
  - _Requirements: 9.1, 9.2_

- [x] 5. Configure TTS for Rose's voice

- [x] 5.1 Update TextToSpeech module for Rose's voice profile

  - Configure ElevenLabs voice_id for warm, calming female voice
  - Set speech parameters (rate: slightly slower, stability: high)
  - Test voice quality with therapeutic language
  - _Requirements: 8.1, 8.2_

- [x] 5.2 Implement TTS error handling and fallback

  - Handle TTS API failures gracefully
  - Provide text-only fallback when TTS unavailable
  - Log TTS errors for monitoring
  - _Requirements: 8.4, 9.2_

- [x] 5.3 Add TTS response caching for common phrases

  - Cache greeting and common therapeutic responses
  - Implement cache invalidation strategy
  - _Requirements: 10.2_

- [x] 6. Build React frontend for voice interface

- [x] 6.1 Initialize React project with TypeScript

  - Create frontend/ directory in project root
  - Set up React with Vite or Create React App
  - Configure TypeScript ``
  - Install dependencies: react, framer-motion or gsap, axios
  - _Requirements: 5.1, 5.2_

- [x] 6.2 Create VoiceButton component with state management

  - Implement push-to-talk button with hold-to-record functionality
  - Create visual states: idle, listening, processing, speaking, error
  - Add smooth animations for state transitions using Framer Motion or GSAP
  - Implement touch and mouse event handlers
  - _Requirements: 2.1, 5.3, 5.4_

- [x] 6.3 Implement useVoiceRecording hook for audio capture

  - Use Web Audio API to capture microphone input
  - Record audio while button is pressed
  - Convert audio to appropriate format (WAV or WebM)
  - Handle browser permissions for microphone access
  - _Requirements: 2.2_

- [x] 6.4 Implement useAudioPlayback hook for response playback

  - Automatically play audio responses from backend
  - Show visual feedback during playback
  - Handle audio loading and buffering states
  - _Requirements: 2.5_

- [x] 6.5 Create API client service for backend communication

  - Implement POST /api/session/start call
  - Implement POST /api/voice/process with audio upload
  - Handle multipart/form-data for audio files
  - Manage session_id across requests
  - _Requirements: 2.2, 2.3_

- [x] 6.6 Implement error handling and user feedback in UI

  - Display error messages for failed requests
  - Show retry options for recoverable errors
  - Implement loading states and spinners
  - _Requirements: 9.2, 9.3_

- [x] 6.7 Add responsive design and mobile support

  - Ensure button works on touch devices
  - Optimize layout for mobile and desktop
  - Test on various screen sizes
  - _Requirements: 5.5_

- [x] 6.8 Implement audio visualizer component

  - Show waveform or visual feedback during recording
  - Animate during Rose's response playback
  - Use canvas or SVG for visualizations
  - _Requirements: 5.3_

- [x] 6.9 Configure build process and output

  - Set up production build configuration
  - Configure output directory for FastAPI static serving
  - Optimize bundle size
  - _Requirements: 7.3_

- [x] 7. Disable WhatsApp integration

- [x] 7.1 Comment out WhatsApp route registration in FastAPI

  - Keep WhatsApp code files intact
  - Don't register WhatsApp endpoints in main app
  - Add comments indicating feature is frozen for future
  - _Requirements: 6.2, 6.3_

- [x] 7.2 Remove WhatsApp environment variables from required settings

  - Make WHATSAPP\_\* variables optional in settings.py
  - Update .env.example to mark as optional
  - _Requirements: 6.3, 6.5_

- [ ] 8. Configure deployment for Railway
- [ ] 8.1 Create railway.json configuration file

  - Define build command (install Python deps + build React frontend)
  - Define start command (uvicorn server)
  - Configure health check path
  - Set restart policy

  - _Requirements: 7.1, 7.4_

- [ ] 8.2 Update Dockerfile for production deployment

  - Multi-stage build: Python deps + React build
  - Copy frontend build to static directory
  - Configure port from environment variable
  - Optimize image size
  - _Requirements: 7.1, 7.3_

- [ ] 8.3 Create deployment documentation

  - Document Railway deployment steps
  - List required environment variables
  - Include troubleshooting guide
  - Add alternative deployment options (Render, Fly.io)
  - _Requirements: 7.5_

- [ ] 8.4 Configure environment variables for production

  - Update settings.py to use PORT environment variable
  - Ensure all secrets are loaded from environment
  - Add validation for required variables
  - _Requirements: 7.2_

- [ ] 9. Update project configuration and dependencies
- [ ] 9.1 Update pyproject.toml dependencies

  - Mark image generation dependencies as optional
  - Ensure all required dependencies are listed
  - Add fastapi[standard] if not present
  - Add python-multipart for file uploads
  - _Requirements: 6.5_

- [ ] 9.2 Update .env.example with Rose-specific variables

  - Add ROSE_VOICE_ID for TTS configuration
  - Mark WhatsApp variables as optional
  - Remove or mark image generation variables as optional
  - Add deployment-specific variables (PORT)
  - _Requirements: 7.2, 8.1_

- [ ] 9.3 Update README.md with Rose project information

  - Replace Ava references with Rose
  - Update project description for grief counseling focus
  - Document voice-first interaction
  - Update setup instructions
  - Add deployment guide
  - _Requirements: 7.5_

- [ ] 9.4 Update Makefile commands for new workflow

  - Update rose-run command (replace ava-run)
  - Remove or update Docker Compose if needed
  - Add frontend build commands
  - _Requirements: 7.3_

- [ ] 10. Testing and validation
- [ ] 10.1 Test complete voice interaction flow

  - Record audio → transcribe → process → respond → play audio
  - Verify session continuity across multiple interactions
  - Test error recovery and retry mechanisms
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 10.2 Test Rose's character and therapeutic responses

  - Verify Rose responds with healer shaman personality
  - Test grief counseling scenarios
  - Validate ancient wisdom and holistic approach in responses
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 10.3 Test memory system with therapeutic context

  - Share emotional information and verify storage
  - Start new session and verify memory recall
  - Test memory relevance for grief counseling
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 10.4 Test frontend on multiple devices and browsers

  - Test on desktop (Chrome, Firefox, Safari)
  - Test on mobile (iOS Safari, Android Chrome)
  - Verify responsive design
  - Test microphone permissions flow
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 10.5 Perform load testing and performance validation

  - Test concurrent voice sessions
  - Monitor API usage and costs
  - Verify resource consumption within Railway limits
  - Test audio processing latency
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 10.6 Validate deployment on Railway
  - Deploy to Railway staging environment
  - Test all endpoints in production
  - Verify environment variables are loaded correctly
  - Test health check endpoint
  - Monitor logs for errors
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
