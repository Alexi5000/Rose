ifeq (,$(wildcard .env))
$(error .env file is missing. Please create one based on .env.example)
endif

include .env

CHECK_DIRS := .

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
	uv run ruff check -e $(CHECK_DIRS)
	uv run ruff check --select I -e $(CHECK_DIRS)

lint-check:
	uv run ruff check $(CHECK_DIRS)

# ============================================
# Legacy Commands (for backward compatibility)
# ============================================

ava-build: rose-build
ava-run: rose-start
ava-stop: rose-stop
ava-delete: rose-delete

.PHONY: rose-run rose-build rose-start rose-stop rose-delete \
        frontend-install frontend-build frontend-dev frontend-clean \
        install dev clean \
        format-fix lint-fix format-check lint-check \
        ava-build ava-run ava-stop ava-delete