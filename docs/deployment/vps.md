# VPS Deployment Guide

This guide describes deploying MSDS to a self-managed virtual private server (VPS) such as Digital
Ocean, Linode, or AWS Lightsail. It assumes Ubuntu 22.04 LTS, root SSH access, and familiarity with
basic Linux administration.

## 1. Provision Infrastructure
- **Server size:** 4 vCPU, 8 GB RAM, 80 GB SSD (adjust for production load).
- **Networking:** Enable static IP, configure DNS `msds.example.gov`.
- **Security groups/firewall:** Allow inbound ports 22 (SSH), 80 (HTTP), 443 (HTTPS).

## 2. Harden the Host
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y fail2ban ufw unattended-upgrades
sudo adduser msds --disabled-password
sudo usermod -aG sudo msds
sudo cp ~/.ssh/authorized_keys /home/msds/.ssh/authorized_keys
sudo chown -R msds:msds /home/msds/.ssh
sudo chmod 700 /home/msds/.ssh && sudo chmod 600 /home/msds/.ssh/authorized_keys
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## 3. Install Runtime Dependencies
```bash
sudo apt install -y nginx certbot python3-certbot-nginx docker.io docker-compose-plugin postgresql redis-server
sudo systemctl enable docker postgresql redis-server
```

Create PostgreSQL roles and database:
```bash
sudo -u postgres createuser msds --pwprompt
sudo -u postgres createdb msds -O msds
```

## 4. Fetch Application Code
```bash
sudo mkdir -p /opt/msds
sudo chown -R msds:msds /opt/msds
sudo -i -u msds bash <<'SCRIPT'
cd /opt/msds
git clone https://github.com/your-org/msds.git .
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && npm run build && cd ..
npm install -g pm2
SCRIPT
```

## 5. Configure Environment
Create `/opt/msds/config/.env` with production secrets:
```
DATABASE_URL=postgresql://msds:<PASSWORD>@127.0.0.1:5432/msds
REDIS_URL=redis://127.0.0.1:6379/0
SECRET_KEY=<generate>
JWT_ISSUER=https://msds.example.gov
JWT_AUDIENCE=msds-users
FILE_STORAGE_BUCKET=s3://msds-prod-attachments
```

Ensure `config/settings.prod.yaml` reflects production toggles (caching, logging, CDN endpoints).

## 6. Database Migrations & Seed
```bash
sudo -i -u msds bash <<'SCRIPT'
cd /opt/msds
source .venv/bin/activate
alembic upgrade head
python backend/scripts/seed_reference_data.py
SCRIPT
```

## 7. Process Management
Use `pm2` (Node) and `systemd` (Python workers) to manage services.

### Backend API (`systemd`)
Create `/etc/systemd/system/msds-api.service`:
```
[Unit]
Description=MSDS API
After=network.target

[Service]
User=msds
WorkingDirectory=/opt/msds
Environment="ENV_FILE=/opt/msds/config/.env"
ExecStart=/opt/msds/.venv/bin/uvicorn backend.app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Reload and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now msds-api
```

### Workflow Worker (`systemd`)
Repeat with `/etc/systemd/system/msds-worker.service` invoking
`/opt/msds/.venv/bin/python backend/workers/start_workers.py`.

### Frontend (`pm2`)
```bash
sudo -i -u msds pm2 serve frontend/dist 4173 --name msds-frontend --spa
sudo -i -u msds pm2 save
sudo pm2 startup systemd -u msds --hp /home/msds
```

## 8. Reverse Proxy & TLS
Configure Nginx `/etc/nginx/sites-available/msds`:
```
server {
    listen 80;
    server_name msds.example.gov;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://127.0.0.1:4173/;
        try_files $uri $uri/ /index.html;
    }
}
```
Enable and secure:
```bash
sudo ln -s /etc/nginx/sites-available/msds /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d msds.example.gov
```

## 9. Monitoring & Backups
- Install Prometheus Node Exporter and configure scraping.
- Forward logs to centralized syslog (e.g., Graylog).
- Schedule nightly PostgreSQL dumps via `pg_dump` to encrypted object storage (see
  `docs/usage-examples.md#backup-procedures`).

## 10. Disaster Recovery Drills
- Test restoring PostgreSQL dumps to staging.
- Validate Redis persistence or use `redis-cli --rdb` for snapshots.
- Simulate failover by rotating DNS to standby VPS; ensure automation scripts run cleanly.
