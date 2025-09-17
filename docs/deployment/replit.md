# Replit Deployment Guide

This guide explains how to launch a managed demo of MSDS on [Replit](https://replit.com/). Replit is
well-suited for product demos, training sessions, and lightweight pilots.

## 1. Prepare the Repository
1. Ensure the latest code is pushed to GitHub on the `main` branch.
2. Include the following files for Replit compatibility:
   - `.replit` – sets the run command.
   - `replit.nix` – defines the Nix environment (Python, Node.js, PostgreSQL client).
   - `docker-compose.replit.yml` (optional) – orchestrates services in the Replit workspace.

## 2. Create the Repl
1. Visit Replit and click **Create Repl**.
2. Choose **Import from GitHub** and paste the repository URL (`https://github.com/your-org/msds`).
3. Select the `main` branch and import.

## 3. Configure Environment Variables
Open the **Secrets** panel (lock icon) and add:
- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/msds`
- `REDIS_URL=redis://localhost:6379/0`
- `SECRET_KEY` (generate via `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `JWT_AUDIENCE`, `JWT_ISSUER`
- Optional third-party API keys for maps, email, and SMS.

## 4. Install Dependencies
Replit automatically executes `poetry install` or `pip install -r requirements.txt` based on project
files. For the MSDS blueprint:
```bash
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
```

Ensure `replit.nix` includes:
```nix
{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.nodejs-18_x
    pkgs.postgresql
    pkgs.redis
  ];
}
```

## 5. Launch Services
Update `.replit` with the run command:
```
run = "bash start-replit.sh"
```

Create `start-replit.sh` in the repository (tracked) with:
```bash
#!/usr/bin/env bash
set -euo pipefail

# Start PostgreSQL & Redis inside Replit
if pg_ctl -D "$REPL_HOME/postgres" status > /dev/null 2>&1; then
  echo "PostgreSQL is already running."
else
  pg_ctl -D "$REPL_HOME/postgres" -l "$REPL_HOME/postgres/logfile" start
fi
redis-server --daemonize yes

# Apply migrations and seed minimal data
source .venv/bin/activate
alembic upgrade head
python backend/scripts/seed_demo_data.py

# Run backend and frontend concurrently
uvicorn backend.app:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev -- --host --port 3000
```

Ensure the script is executable: `chmod +x start-replit.sh`.

## 6. Configure Webview
In the Replit **Shell**, expose ports:
- Backend: `8000` (set as hidden)
- Frontend: `3000` (set as primary webview)

## 7. Persistent Storage Considerations
- Replit provides ephemeral storage; schedule export jobs to S3 or Google Drive (see
  `docs/usage-examples.md#backup-procedures`).
- Use lightweight datasets and limit attachment sizes for demos.

## 8. Collaboration Features
- Enable **Multiplayer** to collaborate on debugging or training.
- Use the built-in **Version Control** tab to commit documentation updates directly from Replit.

## 9. Maintenance & Cost Controls
- Stop the Repl when not in use to avoid exceeding Replit usage quotas.
- Configure autosleep timers in `.replit` if the workload allows.
- Monitor the Replit console for CPU and memory warnings; adjust service settings accordingly.
