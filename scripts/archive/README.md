# Archived Scripts

This directory contains deprecated scripts that are no longer actively used but kept for reference.

## Deployment Scripts (Deprecated)

These scripts were used for initial Railway deployment setups and diagnostics:

- **deploy_rose_clean.py** - Clean deployment script for Railway
- **deploy_rose_ultimate.py** - Enhanced deployment script with additional checks
- **diagnose_deployment.py** - Deployment diagnostics and troubleshooting
- **fix_deployment_issues.py** - Automated deployment issue fixes
- **verify_deployment.py** - Post-deployment verification checks

**Status**: Deprecated - Deployment now handled via `railway.json` and CI/CD

## Development & Testing Scripts (Deprecated)

- **quick_start.py** - Quick start script for development environment
- **restart_dev_clean.py** - Clean restart of development environment
- **test_voice_api.py** - Voice API testing (replaced by `e2e_test_voice.py`)
- **master_smoke.py** - Smoke test suite (replaced by pytest integration tests)
- **run_memory_smoke_test.py** - Memory system smoke tests

**Status**: Deprecated - Testing now handled via pytest test suite

## Analysis & Monitoring Scripts (Deprecated)

- **analyze_dependencies.py** - Dependency analysis and conflict detection
- **profile_performance.py** - Performance profiling utilities
- **verify_observability.py** - Observability stack verification

**Status**: Deprecated - Analysis now handled via dedicated monitoring tools

## Qdrant Management Scripts

- **qdrant_inspect.py** - Basic Qdrant collection inspection
- **qdrant_diagnose.py** - Comprehensive Qdrant diagnostics
- **reindex_qdrant.py** - Qdrant collection reindexing
- **verify_qdrant.py** - Qdrant health checks

**Status**: Partially active - Basic operations now handled via admin API endpoints

## Documentation

- **REFACTORING_NOTES.md** - Historical refactoring notes and decisions

## Active Scripts (in parent directory)

For actively maintained scripts, see the parent `scripts/` directory:

- `build_and_serve.py` - Production build and serve
- `run_dev_server.py` - Development server with hot reload
- `e2e_test_voice.py` - End-to-end voice interface testing
- `utils.py` - Shared utilities for scripts

## Migration Notes

When updating or replacing archived scripts:

1. Check if functionality exists in active scripts
2. Consider migrating useful functions to `utils.py`
3. Update this README with deprecation notes
4. Prefer pytest tests over standalone test scripts
5. Use admin API endpoints for system operations
