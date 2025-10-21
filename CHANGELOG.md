# Changelog

All notable changes to the Rose the Healer Shaman project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive deployment checklist with pre/post-deployment tasks
- Project structure documentation with complete directory guide
- Root folder cleanup summary documentation
- Code quality improvements documentation
- Scripts directory with organized utility scripts
- Docker directory with organized Docker configurations
- Standardized error handling decorators (`@handle_api_errors`, `@log_errors`, `@with_fallback`)
- Enhanced exception hierarchy with base `AICompanionError` class
- Type hints for all graph node functions
- Google-style docstrings across core modules
- Configuration parameters for STT, TTS, audio cleanup, and circuit breakers
- Lazy initialization for circuit breakers to avoid import-time dependencies

### Changed
- **BREAKING**: Reorganized root folder structure - files moved to subdirectories
  - Scripts moved to `scripts/` directory
  - Docker configs moved to `docker/` directory
  - Configuration files moved to `config/` directory
  - Test config moved to `tests/` directory
  - Documentation moved to `docs/` directory
  - CI config moved to `.github/` directory
- Pinned all dependency versions from `>=` to `==` for reproducible builds
- Fixed pytest version to 7.4.4 for compatibility with pytest-playwright
- Moved hardcoded configuration values to centralized settings module
- Updated all file references in code and documentation
- Enhanced Settings class with comprehensive docstrings
- Improved error messages with structured logging context

### Fixed
- Removed actual API key from `.env.example` file (security issue)
- Circuit breaker initialization no longer requires settings at import time
- Test compatibility issues with environment variables

### Documentation
- Added `docs/PROJECT_STRUCTURE.md` - Complete project organization guide
- Added `docs/ROOT_FOLDER_CLEANUP_SUMMARY.md` - Cleanup summary and migration guide
- Added `docs/CODE_QUALITY_IMPROVEMENTS.md` - Code quality improvements summary
- Added `docs/DEPLOYMENT_CHECKLIST.md` - Comprehensive deployment guide
- Added `scripts/README.md` - Scripts documentation
- Added `docker/README.md` - Docker configuration guide
- Updated `README.md` with project structure section
- Updated all documentation with new file paths

## [0.1.0] - 2024-01-XX

### Added
- Initial release of Rose the Healer Shaman
- Voice-first AI grief counselor with therapeutic personality
- LangGraph workflow orchestration
- Groq API integration (LLM and STT)
- ElevenLabs TTS integration
- Qdrant vector database for long-term memory
- SQLite checkpointer for conversation state
- FastAPI backend with voice processing endpoints
- React frontend with push-to-talk interface
- Circuit breakers for external service resilience
- Comprehensive test suite (80+ tests)
- Docker and Railway deployment support
- Security middleware (CORS, rate limiting, security headers)
- Structured logging with JSON output
- Health check endpoint with dependency verification
- Session management and cleanup
- Audio file cleanup automation
- Memory extraction and retrieval system
- Therapeutic character card with ancient healing wisdom

### Documentation
- Complete API documentation
- Architecture overview
- Deployment guides (Railway, Docker)
- Operations runbook
- Incident response plan
- Security implementation guide
- Testing documentation
- Getting started guide

---

## Version History

- **Unreleased** - Root folder cleanup, code quality improvements, deployment checklist
- **0.1.0** - Initial release with core functionality

## Migration Guides

### Upgrading from Pre-Cleanup Version

If you have an existing clone of the repository before the root folder cleanup:

1. **Update file references in your scripts:**
   ```bash
   # Old
   ./run_tests.sh all
   
   # New
   ./scripts/run_tests.sh all
   ```

2. **Update configuration paths:**
   ```bash
   # Old
   cat railway.json
   
   # New
   cat config/railway.json
   ```

3. **Docker Compose still works** - No changes needed, paths updated automatically

4. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

See [docs/ROOT_FOLDER_CLEANUP_SUMMARY.md](docs/ROOT_FOLDER_CLEANUP_SUMMARY.md) for detailed migration guide.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Support

For issues, questions, or contributions:
- **Issues**: GitHub Issues
- **Documentation**: [docs/](docs/)
- **Discussions**: GitHub Discussions
