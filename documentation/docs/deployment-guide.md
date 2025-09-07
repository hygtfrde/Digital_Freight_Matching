# Digital Freight Matching System - Deployment Guide

## Overview

This guide covers deployment from development to production environments.

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores, 2.0 GHz
- **RAM**: 4 GB
- **Storage**: 2 GB free space
- **OS**: Linux, macOS, or Windows
- **Python**: 3.8+

### Recommended Requirements
- **CPU**: 4 cores, 2.5 GHz+
- **RAM**: 8 GB+
- **Storage**: 10 GB free space (SSD preferred)
- **OS**: Ubuntu 20.04 LTS+
- **Python**: 3.9+

## Development Environment

### Prerequisites Installation

#### Ubuntu/Debian
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv git curl -y
sudo apt install build-essential python3-dev -y
```

#### macOS
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python git
```

#### Windows
- Install Python from python.org
- Install Git from git-scm.com
- Or use Windows Subsystem for Linux (WSL)

### Project Setup

#### 1. Clone and Setup
```bash
git clone <repository-url>
cd digital-freight-matching

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Database Initialization
```bash
# Initialize with sample data
python db_manager.py init

# Verify setup
python db_manager.py status
```

#### 3. Service Startup
```bash
# API Server
python app/main.py

# CLI Interface (separate terminal)
python cli_menu_app/main.py
```

## Production Deployment

### Server Preparation

#### Ubuntu Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install packages
sudo apt install python3 python3-pip python3-venv nginx supervisor git -y

# Create application user
sudo useradd -m -s /bin/bash dfm
sudo usermod -aG sudo dfm
sudo su - dfm
```

#### Directory Structure
```bash
mkdir -p /home/dfm/apps/dfm
mkdir -p /home/dfm/logs
mkdir -p /home/dfm/backups
```

### Application Deployment

#### 1. Code Deployment
```bash
cd /home/dfm/apps
git clone <repository-url> dfm
cd dfm

# Production virtual environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn[standard]
```

#### 2. Configuration
```bash
# Production environment file
cat > .env << EOF
DATABASE_URL=sqlite:///./production.db
DEBUG=False
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
EOF

chmod 600 .env
```

#### 3. Database Setup
```bash
python db_manager.py init
python db_manager.py backup --output /home/dfm/backups/initial_backup.sql
```

### Process Management

#### Supervisor Configuration
```bash
sudo tee /etc/supervisor/conf.d/dfm-api.conf << EOF
[program:dfm-api]
command=/home/dfm/apps/dfm/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
directory=/home/dfm/apps/dfm
user=dfm
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/dfm/logs/dfm-api.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=5
environment=PATH="/home/dfm/apps/dfm/venv/bin"
EOF

# Start service
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start dfm-api
```

### Reverse Proxy

#### Nginx Configuration
```bash
sudo tee /etc/nginx/sites-available/dfm << EOF
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /health {
        access_log off;
        proxy_pass http://127.0.0.1:8000/;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/dfm /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### SSL/TLS Setup

#### Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
sudo certbot renew --dry-run
```

## Container Deployment

### Docker Setup

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 dfm && chown -R dfm:dfm /app
USER dfm

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["python", "app/main.py"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  dfm-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./data/production.db
      - DEBUG=False
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - dfm-api
    restart: unless-stopped
```

#### Container Deployment
```bash
# Build and start
docker-compose up -d

# Initialize database
docker-compose exec dfm-api python db_manager.py init

# Check logs
docker-compose logs -f dfm-api
```

## Cloud Deployment

### AWS EC2
```bash
# Launch Ubuntu 20.04 LTS instance
# Security Group: Allow HTTP (80), HTTPS (443), SSH (22)

# Connect and deploy
ssh -i your-key.pem ubuntu@your-instance-ip
# Follow production deployment steps
```

### Google Cloud Platform
```bash
# Create VM instance
gcloud compute instances create dfm-server \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --machine-type=e2-medium

# SSH and deploy
gcloud compute ssh dfm-server
```

### Azure
```bash
# Create resource group and VM
az group create --name dfm-rg --location eastus
az vm create \
    --resource-group dfm-rg \
    --name dfm-server \
    --image UbuntuLTS \
    --admin-username azureuser \
    --generate-ssh-keys
```

## Backup and Recovery

### Database Backup
```bash
# Backup script
cat > /home/dfm/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/dfm/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_FILE="/home/dfm/apps/dfm/production.db"

cp "$DB_FILE" "$BACKUP_DIR/backup_$DATE.db"
gzip "$BACKUP_DIR/backup_$DATE.db"

# Keep 30 days
find "$BACKUP_DIR" -name "backup_*.db.gz" -mtime +30 -delete
EOF

chmod +x /home/dfm/backup.sh

# Schedule daily backups
(crontab -l; echo "0 2 * * * /home/dfm/backup.sh") | crontab -
```

### Recovery
```bash
# Stop services
sudo supervisorctl stop dfm-api

# Restore database
cd /home/dfm/apps/dfm
cp production.db production.db.backup
gunzip -c /home/dfm/backups/backup_YYYYMMDD_HHMMSS.db.gz > production.db

# Restart services
sudo supervisorctl start dfm-api
```

## Monitoring and Maintenance

### Log Management
```bash
# Logrotate configuration
sudo tee /etc/logrotate.d/dfm << EOF
/home/dfm/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 dfm dfm
}
EOF
```

### System Monitoring
```bash
# Monitoring script
cat > /home/dfm/monitor.sh << 'EOF'
#!/bin/bash
echo "=== DFM System Status ==="
echo "Date: $(date)"
echo "Uptime: $(uptime)"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "API Status: $(sudo supervisorctl status dfm-api)"
echo "Database Size: $(ls -lh production.db 2>/dev/null || echo 'Not found')"
EOF

chmod +x /home/dfm/monitor.sh
```

### Performance Tuning

#### Database Optimization
```bash
# SQLite optimization
sqlite3 production.db "
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
CREATE INDEX IF NOT EXISTS idx_order_route ON "order"(route_id);
CREATE INDEX IF NOT EXISTS idx_cargo_order ON cargo(order_id);
"
```

#### Application Tuning
```bash
# Gunicorn optimization
command=/home/dfm/apps/dfm/venv/bin/gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --max-requests 1000 \
    --timeout 30 \
    --keep-alive 2
```

## Security

### System Security
```bash
# Firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

### Application Security
```bash
# File permissions
chmod 600 /home/dfm/apps/dfm/.env
chmod 644 /home/dfm/apps/dfm/production.db
chown dfm:dfm /home/dfm/apps/dfm/production.db
```

## Troubleshooting

### Service Issues
```bash
# Check supervisor logs
sudo supervisorctl tail dfm-api

# Check system logs
sudo journalctl -u supervisor -f

# Test Python environment
source /home/dfm/apps/dfm/venv/bin/activate
python -c "import app.main; print('Import successful')"
```

### Database Issues
```bash
# Check integrity
python db_manager.py verify

# Reset if corrupted
python db_manager.py reset --confirm
python db_manager.py init
```

### Performance Issues
```bash
# Monitor resources
htop
iotop

# Check logs
tail -f /home/dfm/logs/dfm-api.log

# Database performance
sqlite3 production.db "EXPLAIN QUERY PLAN SELECT * FROM route;"
```

This deployment guide provides comprehensive instructions for various deployment scenarios from development to production cloud environments.
