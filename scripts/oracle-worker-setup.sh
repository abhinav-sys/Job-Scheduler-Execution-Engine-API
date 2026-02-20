#!/bin/bash
# Run this on your Oracle Cloud Ubuntu VM (as the user that owns the repo)
# to install the worker and optionally run it as a systemd service on boot.
#
# Usage:
#   1. Clone repo, install deps, set DATABASE_URL (see DEPLOY-FREE.md section 4).
#   2. Optional - install as service: sudo ./scripts/oracle-worker-setup.sh install
#   3. You must set DATABASE_URL in the environment or in /etc/job-worker.env (see below).

set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_NAME="job-scheduler-worker"
ENV_FILE="/etc/job-worker.env"

install_service() {
    if [ "$(id -u)" -ne 0 ]; then
        echo "Run with sudo: sudo $0 install"
        exit 1
    fi
    if [ ! -f "$ENV_FILE" ]; then
        echo "Create $ENV_FILE with: DATABASE_URL=postgresql+asyncpg://..."
        echo "Example: echo 'DATABASE_URL=postgresql+asyncpg://user:pass@host/neondb?sslmode=require' | sudo tee $ENV_FILE"
        exit 1
    fi
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Job Scheduler Worker
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$REPO_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$REPO_DIR/.venv/bin/python -m app.worker.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl start "$SERVICE_NAME"
    echo "Service installed and started. Check: systemctl status $SERVICE_NAME"
}

case "${1:-}" in
    install) install_service ;;
    *)
        echo "Usage: sudo $0 install"
        echo "Before install: create $ENV_FILE with DATABASE_URL=your_neon_url"
        exit 0
        ;;
esac
