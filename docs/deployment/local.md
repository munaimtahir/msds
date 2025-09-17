# Local Development Deployment Guide

This guide walks through running the MSDS reference stack on a developer workstation. It assumes a
Unix-like environment (macOS, Linux, or WSL2) with administrative privileges.

## Prerequisites
- Python 3.11+
- Node.js 18+
- Docker Desktop or Docker Engine with Compose v2
- PostgreSQL 15 (local installation or Docker container)
- Redis 7 (optional, for background job support)

## 1. Clone and Bootstrap
```bash
git clone https://github.com/your-org/msds.git
cd msds
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

## 2. Configure Environment Variables
1. Copy the example environment file:
   ```bash
   cp config/.env.example config/.env
   ```
2. Edit `config/.env` and set:
   - `DATABASE_URL=postgresql://msds:msds@localhost:5432/msds`
   - `REDIS_URL=redis://localhost:6379/0`
   - `SECRET_KEY`, `JWT_AUDIENCE`, `JWT_ISSUER`
   - API client credentials for third-party integrations (optional during local dev).

## 3. Start Dependencies
You may run services via Docker or host-provided packages.

### Option A: Docker Compose
```bash
docker compose -f docker-compose.local.yml up -d postgres redis
```

### Option B: Native Services
- Start PostgreSQL and create database:
  ```bash
  createdb msds
  createuser msds --pwprompt
  psql -c "GRANT ALL PRIVILEGES ON DATABASE msds TO msds;"
  ```
- (Optional) Start Redis locally: `redis-server`

## 4. Apply Database Migrations
```bash
alembic upgrade head
python backend/scripts/seed_demo_data.py
```

## 5. Launch Application Services
```bash
# Terminal 1 - Backend API
uvicorn backend.app:app --reload --port 8000

# Terminal 2 - Workflow worker
python backend/workers/start_workers.py

# Terminal 3 - Frontend dev server
cd frontend
npm run dev -- --open
```

## 6. Access the Application
- Backend API: http://localhost:8000/docs (Swagger UI)
- Operations Console: http://localhost:5173
- Temporal UI (if enabled): http://localhost:7233

## 7. Run Tests
```bash
pytest
npm test
```

## 8. Troubleshooting
- **Port conflicts:** Adjust ports in `docker-compose.local.yml` and `.env`.
- **SSL certificates:** Local dev uses HTTP; disable strict transport security in browsers when
  testing web features.
- **Migrations failing:** Ensure PostgreSQL user has privileges; check Alembic versions table.

## 9. Developer Productivity Tips
- Enable hot-reload for the backend via `uvicorn --reload`.
- Use VS Code Dev Containers or JetBrains Gateway for consistent toolchains.
- Seed demo data frequently to exercise dashboards and audit exports.
