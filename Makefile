-include .env

HOST ?= 0.0.0.0
PORT ?= 8000
CHECK_DIRS ?= src tests scripts

# ============================================
# Rose Application Commands
# ============================================

rose-run:
	@echo "Starting Rose the Healer Shaman..."
	uv run uvicorn ai_companion.interfaces.web.app:app --host $(HOST) --port $(PORT) --reload

rose-build:
	docker compose build

rose-start:
	docker compose up --build -d

rose-stop:
	docker compose stop

rose-delete:
	@if [ -d "long_term_memory" ]; then rm -rf long_term_memory; fi
	@if [ -d "short_term_memory" ]; then rm -rf short_term_memory; fi
	@if [ -d "generated_images" ]; then rm -rf generated_images; fi
	docker compose down

# ============================================
# Frontend Commands
# ============================================

frontend-install:
	cd frontend && npm install

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev

frontend-clean:
	rm -rf frontend/dist frontend/node_modules

# ============================================
# Development Commands
# ============================================

install:
	uv sync
	$(MAKE) frontend-install

setup-dev:
	@mkdir -p long_term_memory short_term_memory generated_images
	@mkdir -p src/ai_companion/modules/memory/short_term
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env from .env.example"; fi
	@echo "Rose developer directories are ready"

dev: frontend-build rose-run

clean: rose-delete frontend-clean

# ============================================
# Code Quality Commands
# ============================================

format-fix:
	uv run ruff format $(CHECK_DIRS)
	uv run ruff check --select I --fix $(CHECK_DIRS)

lint-fix:
	uv run ruff check --fix $(CHECK_DIRS)

format-check:
	uv run ruff format --check $(CHECK_DIRS)
	uv run ruff check --select I $(CHECK_DIRS)

lint-check:
	uv run ruff check $(CHECK_DIRS)

TEST_FAST_FILES ?= tests/unit/test_repository_hygiene.py tests/unit/test_settings.py tests/unit/test_memory_manager.py tests/unit/test_vector_store.py tests/unit/test_error_handlers.py tests/unit/test_fixtures_setup.py tests/unit/test_fixtures_validation.py tests/test_core.py tests/test_circuit_breaker.py tests/test_data_persistence.py tests/test_resource_management.py tests/test_rose_character.py tests/test_voice_interaction.py

test:
	uv run pytest --no-cov $(TEST_FAST_FILES)

test-coverage:
	uv run pytest --ignore=tests/test_e2e_playwright.py --ignore=scripts/archive

test-deployment:
	uv run pytest --no-cov tests/test_deployment.py tests/test_post_deployment_smoke.py tests/test_smoke.py tests/test_security.py

test-performance:
	uv run pytest --no-cov tests/test_performance.py tests/test_performance_benchmarks.py tests/test_memory_smoke_10x5min.py

test-e2e:
	uv run pytest --no-cov tests/test_e2e_playwright.py

hygiene-check:
	@if grep -RIn "$$(printf '\342\200\224')" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=frontend/node_modules --exclude-dir=assets .; then echo "Em dash found"; exit 1; else echo "No em dashes found"; fi

.PHONY: rose-run rose-build rose-start rose-stop rose-delete         frontend-install frontend-build frontend-dev frontend-clean         install setup-dev dev clean         format-fix lint-fix format-check lint-check test test-coverage test-deployment test-performance test-e2e hygiene-check
