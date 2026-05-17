# 🚀 Rose the Healer Shaman - Deployment & Development Plan

This document outlines the standardized procedures for local development, testing, and production deployment of the Rose application.

## 🛠️ Local Development (Docker)

We use a dual-container setup for local development to enable hot-reloading for both the backend (FastAPI) and frontend (Vite/React).

### Prerequisites
- Docker & Docker Compose installed.
- `.env` file created from `.env.example` with valid API keys.

### Quick Start
1.  **Start the Dev Environment:**
    ```bash
    docker-compose -f docker-compose.dev.yml up --build
    ```
2.  **Access the App:**
    - Frontend: [http://localhost:3000](http://localhost:3000)
    - Backend API: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
    - Qdrant Dashboard: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### Features
- **Hot Reloading:** Changes to `src/` (Python) or `frontend/src/` (React) will automatically trigger reloads.
- **Data Persistence:**
    - `long_term_memory/`: Persists Qdrant vector data.
    - `short_term_memory/`: Persists SQLite sessions and logs.
- **Networking:**
    - Frontend proxies `/api` requests to the backend container.
    - Backend communicates with Qdrant via the `qdrant` hostname.

---

## 📦 Production Build (Local Test)

We use a single-container architecture for production to minimize costs and complexity. The React frontend is built and served as static files by the FastAPI backend.

### Quick Start
1.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```
2.  **Access the App:**
    - Application: [http://localhost:8000](http://localhost:8000) (Note: Port 8000 is mapped to container port 8080)

### Architecture
- **Multi-stage Dockerfile:**
    1.  `frontend-builder`: Builds React app to static files.
    2.  `python-builder`: Installs Python dependencies with `uv`.
    3.  `runtime`: Minimal Python image serving FastAPI + Static Frontend.
- **Single Service:** No separate frontend container; FastAPI serves `index.html` and assets.

---

## 🚂 Railway Deployment

Target: **Railway** (railway.com)

### Service Structure
1.  **Rose (Main Service)**
    - **Source:** GitHub Repo (this repository).
    - **Dockerfile:** Uses the root `Dockerfile`.
    - **Variables:** Copy contents of `.env` (excluding local-only vars).
    - **Port:** Railway automatically detects `PORT` (default 8080).
    - **Public Domain:** Enabled (e.g., `rose-production.up.railway.app`).

2.  **Qdrant (Vector DB)**
    - **Source:** Docker Image `qdrant/qdrant:latest`.
    - **Variables:** `QDRANT_ALLOW_RECOVERY_MODE=true`.
    - **Volume:** Mount `/qdrant/storage` for persistence.
    - **Private Networking:** Accessible by Rose service via internal DNS.

### Deployment Checklist
- [ ] **Environment Variables:** Ensure all keys from `.env` are set in Railway.
- [ ] **Qdrant Connection:** Set `QDRANT_URL` in Rose service to the internal Railway URL of the Qdrant service (e.g., `http://qdrant.railway.internal:6333`).
- [ ] **Health Check:** Verify deployment success by visiting `/api/v1/health`.

---

## ✅ Verification Checklist

### 1. Local Dev
- [ ] `docker-compose -f docker-compose.dev.yml up` starts without errors.
- [ ] Frontend loads at `localhost:3000`.
- [ ] Voice recording works (browser permission prompt appears).
- [ ] Backend logs show "Application startup complete".
- [ ] Hot reload works (try editing a file).

### 2. Production Docker
- [ ] `docker-compose up` starts without errors.
- [ ] App loads at `localhost:8000`.
- [ ] Static assets (JS/CSS) load correctly (check Network tab).
- [ ] API requests succeed (no 404s on `/api/...`).

### 3. Code Quality
- [ ] No magic numbers in core logic (use `server_config.py` / `voice.ts`).
- [ ] Logs contain emojis for visual scanning (🚀, ❌, ✅).
- [ ] Environment variables are explicitly defined.
