# Scripts Directory

This directory contains utility scripts for development, testing, and maintenance.

## Test Runners

### run_tests.sh (Unix/Linux/Mac)
Comprehensive test runner script for running different test suites.

**Usage:**
```bash
./scripts/run_tests.sh [test_type] [options]
```

**Test Types:**
- `all` - Run all tests
- `core` - Core functionality tests
- `voice` - Voice interaction tests
- `character` - Rose character tests
- `memory` - Memory system tests
- `performance` - Performance tests
- `deployment` - Deployment validation tests
- `coverage` - Run with coverage report

**Examples:**
```bash
# Run all tests
./scripts/run_tests.sh all

# Run voice tests with verbose output
./scripts/run_tests.sh voice -v

# Run with coverage report
./scripts/run_tests.sh coverage
```

### run_tests.bat (Windows)
Windows equivalent of the Unix test runner.

**Usage:**
```cmd
scripts\run_tests.bat [test_type] [options]
```

**Examples:**
```cmd
REM Run all tests
scripts\run_tests.bat all

REM Run voice tests
scripts\run_tests.bat voice
```

## Utility Scripts

### fix-secret.sh
Git history cleanup script for removing secrets from commit history.

**Note:** This script is for emergency use only. Prefer preventing secrets from being committed in the first place using `.gitignore` and pre-commit hooks.

## Adding New Scripts

When adding new scripts to this directory:

1. **Use descriptive names** - Script purpose should be clear from filename
2. **Add execute permissions** (Unix/Linux/Mac):
   ```bash
   chmod +x scripts/your-script.sh
   ```
3. **Document in this README** - Add usage instructions
4. **Include help text** - Scripts should support `--help` flag
5. **Handle errors gracefully** - Exit with appropriate error codes

## Best Practices

- Keep scripts focused on a single task
- Use environment variables for configuration
- Provide clear error messages
- Test scripts on all target platforms
- Document dependencies and requirements
