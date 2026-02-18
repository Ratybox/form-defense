# Form Defense - Production Deployment Guide

> **Server:** `root@64.31.4.29`
> **Domain:** `tov.afaq.sa`
> **Stack:** Django 5.1 (Gunicorn) + Next.js 14 + MySQL + Nginx + aaPanel
> **OS:** Ubuntu 24.04 LTS (Noble Numbat)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [aaPanel Installation (FIRST)](#2-aapanel-installation-first)
3. [System Dependencies](#3-system-dependencies)
4. [MySQL Setup](#4-mysql-setup)
5. [Project Setup](#5-project-setup)
6. [Backend Configuration (Django)](#6-backend-configuration-django)
7. [Frontend Configuration (Next.js)](#7-frontend-configuration-nextjs)
8. [Systemd Services](#8-systemd-services)
9. [Nginx Configuration](#9-nginx-configuration)
10. [SSL/TLS Certificate](#10-ssltls-certificate)
11. [Firewall (UFW)](#11-firewall-ufw)
12. [Verification](#12-verification)
13. [deploy.sh - Automated Updates](#13-deploysh---automated-updates)
14. [Maintenance & Troubleshooting](#14-maintenance--troubleshooting)
15. [File Map](#15-file-map)

---

## 1. Prerequisites

- SSH access: `ssh root@64.31.4.29`
- Domain `tov.afaq.sa` DNS A record pointing to `64.31.4.29`
- GitHub repository cloned or accessible

```bash
ssh root@64.31.4.29
```

Update the system first:

```bash
apt update && apt upgrade -y
apt install -y curl wget git ufw build-essential software-properties-common
```

---

## 2. aaPanel Installation (FIRST)

> **IMPORTANT:** Install aaPanel BEFORE deploying the app. aaPanel installs its own
> Nginx/MySQL stack. We will use aaPanel's Nginx and MySQL for the app.

### 2.1 Install aaPanel

```bash
wget -O install.sh http://www.aapanel.com/script/install-ubuntu_6.0_en.sh && bash install.sh aapanel
```

At the end of installation you will see:

```
==================================================================
Congratulations! Installed successfully!
==================================================================
aaPanel Internet Address: http://64.31.4.29:7800/XXXXXX
aaPanel Internal Address: http://127.0.0.1:7800/XXXXXX
username: XXXXXX
password: XXXXXX
==================================================================
```

**Save these credentials immediately.**

### 2.2 First Login & Software Selection

1. Open `http://64.31.4.29:7800/XXXXXX` in your browser.
2. Log in with the provided credentials.
3. aaPanel will prompt you to install a software stack. Choose **LNMP**:
   - **Nginx** (REQUIRED - select Nginx, NOT Apache)
   - **MySQL 5.7 or 8.0** (REQUIRED)
   - **PHP** (optional - useful for phpMyAdmin)
   - **phpMyAdmin** (optional - GUI for MySQL management)
4. Click **One-Click Install** and wait for installation to complete.

> **CRITICAL:** You MUST select **LNMP** (Linux + **Nginx** + MySQL + PHP),
> NOT LAMP (Linux + Apache). The entire deployment relies on Nginx as the
> reverse proxy. Apache will conflict with the configuration below.

### 2.3 Verify aaPanel Services

After installation, confirm the services are running:

```bash
# Check Nginx installed by aaPanel
/www/server/nginx/sbin/nginx -v

# Check MySQL installed by aaPanel
mysql --version

# Check aaPanel status
bt default
```

### 2.4 Secure aaPanel

From aaPanel **Settings > Panel Settings**:

| Setting | Action |
|---------|--------|
| Panel Port | Change from `7800` to a custom port (e.g., `7923`) |
| Security Entry | Change the `/XXXXXX` path to a custom one |
| Panel Username | Change to a non-default username |
| Panel Password | Set a strong password |
| Authorized IPs | Add only your personal IP (optional) |

After changing the port:

```bash
# Allow the new aaPanel port in UFW
ufw allow 7923/tcp
ufw deny 7800/tcp
```

### 2.5 aaPanel Useful Commands

```bash
bt default          # Show panel URL, username, port
bt restart          # Restart aaPanel
bt stop             # Stop aaPanel
bt start            # Start aaPanel
bt 5                # Change password
bt 14               # Show panel port
```

---

## 3. System Dependencies

> aaPanel installs Nginx and MySQL. You still need Python and Node.js.

### 3.1 Python 3.10+

```bash
apt install -y python3 python3-pip python3-venv python3-dev
python3 --version
```

### 3.2 Node.js 20.x LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
node --version && npm --version
```

---

## 4. MySQL Setup

> MySQL was installed by aaPanel in step 2. Now we create the database and user
> for the application. You can do this via CLI or via aaPanel GUI.

### 4.1 Option A: Create Database & User via CLI

```bash
# Connect to MySQL as root
# aaPanel sets a root password during install - find it in aaPanel > Database > root password
mysql -u root -p
```

Run the following SQL commands:

```sql
-- Create the database with UTF-8 support
CREATE DATABASE form_defense_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user (replace YOUR_STRONG_PASSWORD with a real password)
CREATE USER 'form_defense_user'@'127.0.0.1'
  IDENTIFIED BY 'YOUR_STRONG_PASSWORD';

-- Also allow connection from 'localhost' (some drivers use localhost vs 127.0.0.1)
CREATE USER 'form_defense_user'@'localhost'
  IDENTIFIED BY 'YOUR_STRONG_PASSWORD';

-- Grant all privileges on the app database only
GRANT ALL PRIVILEGES ON form_defense_db.*
  TO 'form_defense_user'@'127.0.0.1';

GRANT ALL PRIVILEGES ON form_defense_db.*
  TO 'form_defense_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify the database was created
SHOW DATABASES;

-- Verify the user was created
SELECT User, Host FROM mysql.user WHERE User = 'form_defense_user';

EXIT;
```

### 4.2 Option B: Create Database via aaPanel GUI

1. Open aaPanel in your browser.
2. Go to **Database** in the left sidebar.
3. Click **Add Database**.
4. Fill in:
   - **Database Name:** `form_defense_db`
   - **Username:** `form_defense_user`
   - **Password:** click Generate or enter a strong password
   - **Access:** Local Server Only
   - **Character Set:** `utf8mb4`
5. Click **Submit**.

> **Note:** Copy the password you set - it goes into `backend/.env` as `DB_PASSWORD`.

### 4.3 Find MySQL Root Password (if needed)

If you forgot the root password set by aaPanel:

```bash
# View root password from aaPanel
bt default
# Or check in aaPanel GUI: Database > root password (eye icon)
```

### 4.4 Verify Database Connection

```bash
# Test connection with the app user
mysql -u form_defense_user -p -h 127.0.0.1 form_defense_db

# Inside MySQL, verify:
SHOW TABLES;    -- Should be empty for now
STATUS;         -- Shows connection info and charset
EXIT;
```

### 4.5 MySQL Security Hardening

```bash
# Run the MySQL secure installation script
mysql_secure_installation
```

Answer the prompts:

| Prompt | Answer |
|--------|--------|
| Validate password plugin? | `Y` |
| Password strength | Choose `MEDIUM` or `STRONG` |
| Remove anonymous users? | `Y` |
| Disallow root login remotely? | `Y` |
| Remove test database? | `Y` |
| Reload privilege tables? | `Y` |

---

## 5. Project Setup

### 5.1 Clone Repository

```bash
mkdir -p /var/www
cd /var/www
git clone <YOUR_GITHUB_REPO_URL> form-defense
cd /var/www/form-defense
```

### 5.2 Directory Structure (expected)

```
/var/www/form-defense/
├── backend/          # Django + DRF
├── frontend/         # Next.js 14
├── deploy.sh         # Automated deploy script
├── DEPLOYMENT.md     # This file
└── README.md
```

---

## 6. Backend Configuration (Django)

### 6.1 Virtual Environment & Dependencies

```bash
cd /var/www/form-defense/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify installation:

```bash
python -c "import django; print(f'Django {django.get_version()}')"
python -c "import rest_framework; print('DRF OK')"
python -c "import pymysql; print('PyMySQL OK')"
python -c "import dotenv; print('python-dotenv OK')"
```

### 6.2 Create Production `.env`

```bash
cp .env.example .env
nano .env
```

Fill in the values:

```env
# --- Django Core ---
SECRET_KEY=<GENERATE_ONE_BELOW>
DEBUG=False
ALLOWED_HOSTS=64.31.4.29,tov.afaq.sa
CORS_ALLOWED_ORIGINS=https://tov.afaq.sa,http://tov.afaq.sa,http://64.31.4.29
CSRF_TRUSTED_ORIGINS=https://tov.afaq.sa,http://64.31.4.29

# --- MySQL Database ---
USE_MYSQL=True
DB_NAME=form_defense_db
DB_USER=form_defense_user
DB_PASSWORD=YOUR_STRONG_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=3306
```

Generate a Django SECRET_KEY:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output and paste it as the `SECRET_KEY` value in `.env`.

### 6.3 Verify Database Connection from Django

```bash
source venv/bin/activate
python manage.py dbshell
```

You should see the MySQL prompt (`mysql>`). Type `EXIT;` to quit.

If you get a connection error, double-check:
- `DB_PASSWORD` in `.env` matches what you set in step 4
- `DB_HOST` is `127.0.0.1`
- MySQL service is running: `systemctl status mysql`

### 6.4 Run Migrations & Collect Static Files

```bash
source venv/bin/activate

# Create all database tables
python manage.py migrate

# Verify tables were created
python manage.py dbshell -c "SHOW TABLES;"

# Collect static files for Nginx to serve
# This includes Django admin static files and custom admin CSS
python manage.py collectstatic --noinput

# Create admin superuser (optional but recommended)
python manage.py createsuperuser
```

**Note:** The custom admin CSS file (`api/static/admin/css/custom_admin.css`) will be automatically collected during `collectstatic`. This CSS file removes white backgrounds and ensures proper dark theme compatibility for the Django admin interface.

---

## 7. Frontend Configuration (Next.js)

### 7.1 Install Dependencies

```bash
cd /var/www/form-defense/frontend
npm install
```

### 7.2 Create Production `.env.local`

```bash
cp .env.example .env.local
nano .env.local
```

Content:

```env
NEXT_PUBLIC_API_URL=https://tov.afaq.sa
```

> In production, the frontend calls the API through the same domain via Nginx.
> Nginx proxies `/api/` requests to Gunicorn on port 8000 internally.
> No direct port exposure is needed.

### 7.3 Build

```bash
npm run build
```

---

## 8. Systemd Services

### 8.1 Create Log Directory

```bash
mkdir -p /var/log/form-defense
```

### 8.2 Backend Service (Gunicorn)

```bash
nano /etc/systemd/system/form-defense-backend.service
```

```ini
[Unit]
Description=Form Defense - Django Backend (Gunicorn)
After=network.target mysql.service
Requires=mysql.service

[Service]
User=root
Group=root
WorkingDirectory=/var/www/form-defense/backend
EnvironmentFile=/var/www/form-defense/backend/.env
ExecStart=/var/www/form-defense/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /var/log/form-defense/gunicorn-access.log \
    --error-logfile /var/log/form-defense/gunicorn-error.log \
    config.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8.3 Frontend Service (Next.js)

```bash
nano /etc/systemd/system/form-defense-frontend.service
```

```ini
[Unit]
Description=Form Defense - Next.js Frontend
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/form-defense/frontend
Environment=NODE_ENV=production
Environment=PORT=3000
EnvironmentFile=/var/www/form-defense/frontend/.env.local
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 8.4 Enable & Start Services

```bash
systemctl daemon-reload
systemctl enable form-defense-backend form-defense-frontend
systemctl start form-defense-backend form-defense-frontend

# Verify both are running
systemctl status form-defense-backend
systemctl status form-defense-frontend
```

---

## 9. Nginx Configuration

> aaPanel installs Nginx at `/www/server/nginx/`. Its config structure differs
> from the standard apt-installed Nginx. We create our server block in
> aaPanel's vhost directory.

### 9.1 Determine Nginx Config Path

```bash
# aaPanel Nginx config location
ls /www/server/panel/vhost/nginx/

# If using standard apt Nginx instead:
ls /etc/nginx/sites-available/
```

### 9.2 Create Server Block (aaPanel Nginx)

```bash
nano /www/server/panel/vhost/nginx/form-defense.conf
```

> **Alternative:** If you installed Nginx via apt (not aaPanel), use
> `/etc/nginx/sites-available/form-defense` and symlink to `sites-enabled/`.

```nginx
server {
    listen 80;
    server_name tov.afaq.sa 64.31.4.29;

    # --- Logging ---
    access_log /var/log/nginx/form-defense-access.log;
    error_log  /var/log/nginx/form-defense-error.log;

    # --- Limits ---
    client_max_body_size 10M;

    # --- Security Headers ---
    server_tokens off;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # --- Frontend (Next.js on port 3000) ---
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # --- Backend API (Gunicorn on port 8000) ---
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # --- Django Admin (proxied to Gunicorn) ---
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # --- Django Static Files ---
    location /static/ {
        alias /var/www/form-defense/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # --- Next.js Static Assets ---
    location /_next/static/ {
        alias /var/www/form-defense/frontend/.next/static/;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 9.3 Enable the Site

**If using aaPanel Nginx:**

```bash
# Test config
/www/server/nginx/sbin/nginx -t

# Reload
/www/server/nginx/sbin/nginx -s reload
```

**If using apt Nginx:**

```bash
ln -sf /etc/nginx/sites-available/form-defense /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

### 9.4 Adding the Site via aaPanel GUI (alternative)

If you prefer using aaPanel's interface:

1. Go to **Website** > **Add Site**
2. Domain: `tov.afaq.sa`
3. After creation, click the site name to open settings
4. Go to **Config** tab
5. Replace the entire server block with the Nginx config above
6. Click **Save**

---

## 10. SSL/TLS Certificate

### 10.1 Via aaPanel (recommended - simplest)

1. In aaPanel, go to **Website** > click on `tov.afaq.sa`
2. Go to the **SSL** tab
3. Select **Let's Encrypt**
4. Check the domain `tov.afaq.sa`
5. Click **Apply**
6. Enable **Force HTTPS** toggle

### 10.2 Via Certbot (alternative)

```bash
apt install -y certbot

# For aaPanel Nginx:
certbot certonly --webroot -w /var/www/form-defense/frontend -d tov.afaq.sa

# For apt Nginx:
apt install -y python3-certbot-nginx
certbot --nginx -d tov.afaq.sa
```

Verify auto-renewal:

```bash
certbot renew --dry-run
```

### 10.3 Post-SSL: Update Environment

After SSL is active, ensure these values use `https://`:

**`backend/.env`:**
```env
CORS_ALLOWED_ORIGINS=https://tov.afaq.sa,http://64.31.4.29
CSRF_TRUSTED_ORIGINS=https://tov.afaq.sa
```

**`frontend/.env.local`:**
```env
NEXT_PUBLIC_API_URL=https://tov.afaq.sa
```

Then restart services:

```bash
systemctl restart form-defense-backend form-defense-frontend
```

---

## 11. Firewall (UFW)

```bash
# SSH - ALWAYS allow this first
ufw allow 22/tcp

# HTTP & HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# aaPanel (use your custom port from step 2.4)
ufw allow 7923/tcp

# Enable firewall
ufw enable

# Verify
ufw status numbered
```

> **DO NOT** expose ports 3000 or 8000 externally. They are accessed only by Nginx
> on `127.0.0.1`. This is intentional for the defense scenario.

---

## 12. Verification

### 12.1 Service Health

```bash
systemctl status form-defense-backend
systemctl status form-defense-frontend
systemctl status mysql
# aaPanel Nginx:
/www/server/nginx/sbin/nginx -t
# Or apt Nginx:
systemctl status nginx
```

### 12.2 Endpoint Tests

```bash
# Backend API (internal - should return JSON)
curl -s http://127.0.0.1:8000/api/entries/ | head -c 200

# Frontend (internal - should return HTML)
curl -s http://127.0.0.1:3000 | head -c 200

# Through Nginx (external)
curl -s http://tov.afaq.sa/api/entries/
curl -s http://tov.afaq.sa/
```

### 12.3 MySQL Connection

```bash
cd /var/www/form-defense/backend
source venv/bin/activate
python manage.py dbshell
# Should show mysql> prompt. Type: SHOW TABLES; then EXIT;
```

### 12.4 Django Admin

Open `https://tov.afaq.sa/admin/` in your browser and log in with the superuser credentials you created.

**Admin Features:**
- Custom admin interface optimized for dark theme
- Enhanced form entry display with message preview, hash preview, and age indicators
- Advanced filtering by creation date
- Search functionality across name, email, message, and password hash
- Entry statistics showing message length, word count, hash length, and creation date
- Export selected entries to CSV
- All interface text in English
credentials created in step 6.4.

---

## 13. deploy.sh - Automated Updates

A `deploy.sh` script is included in the repository root. For subsequent deployments:

```bash
cd /var/www/form-defense
chmod +x deploy.sh
./deploy.sh
```

This script pulls the latest code, installs dependencies, runs migrations,
builds the frontend, and restarts all services.

---

## 14. Maintenance & Troubleshooting

### Logs

```bash
# Gunicorn (Django)
journalctl -u form-defense-backend -f
tail -f /var/log/form-defense/gunicorn-error.log

# Next.js
journalctl -u form-defense-frontend -f

# Nginx (aaPanel)
tail -f /www/wwwlogs/form-defense-access.log
tail -f /www/wwwlogs/form-defense-error.log
# Or standard Nginx:
tail -f /var/log/nginx/form-defense-error.log

# MySQL
tail -f /var/log/mysql/error.log

# aaPanel
tail -f /www/server/panel/logs/error.log
```

### Common Issues

| Problem | Solution |
|---------|----------|
| `502 Bad Gateway` | Backend/frontend service is down. Check `systemctl status` for both services |
| `No module named 'rest_framework'` | `source venv/bin/activate && pip install -r requirements.txt` |
| MySQL connection refused | Verify `DB_HOST=127.0.0.1` and `DB_PASSWORD` in `.env`, check `systemctl status mysql` |
| `OperationalError: access denied` | Re-check MySQL user/password created in step 4 matches `.env` |
| Static files 404 | Run `python manage.py collectstatic --noinput`, check `alias` paths in Nginx config, verify `STATICFILES_DIRS` in settings.py includes `api/static` |
| Admin CSS not loading | Ensure `api/static/admin/css/custom_admin.css` exists, run `collectstatic`, check browser cache |
| SSL cert expired | aaPanel: Website > SSL > Renew. Or: `certbot renew` |
| aaPanel inaccessible | Check port with `bt default`, verify UFW allows it |
| Nginx config test fails | aaPanel: `/www/server/nginx/sbin/nginx -t`. apt: `nginx -t` |

### Service Restart

```bash
systemctl restart form-defense-backend form-defense-frontend

# aaPanel Nginx:
/www/server/nginx/sbin/nginx -s reload
# apt Nginx:
systemctl reload nginx
```

### Database Backup

```bash
mkdir -p /root/backups
mysqldump -u form_defense_user -p form_defense_db > /root/backups/form_defense_db_$(date +%F).sql
```

### Database Restore

```bash
mysql -u form_defense_user -p form_defense_db < /root/backups/form_defense_db_YYYY-MM-DD.sql
```

---

## 15. File Map

```
Server filesystem:
==================

/var/www/form-defense/                     # Project root
├── backend/
│   ├── .env                               # Production env vars (MySQL creds, SECRET_KEY)
│   ├── venv/                              # Python virtual environment
│   ├── config/settings.py                 # Django settings (reads .env via python-dotenv)
│   ├── api/                               # API application
│   │   └── static/                        # Custom static files
│   │       └── admin/css/
│   │           └── custom_admin.css       # Custom admin dark theme CSS
│   ├── staticfiles/                       # Collected static files (served by Nginx)
│   └── requirements.txt                   # Python dependencies
├── frontend/
│   ├── .env.local                         # Frontend env vars (API URL)
│   └── .next/                             # Production build output
├── deploy.sh                              # Automated deployment script
└── DEPLOYMENT.md                          # This guide

/etc/systemd/system/
├── form-defense-backend.service           # Gunicorn service (port 8000)
└── form-defense-frontend.service          # Next.js service (port 3000)

Nginx config (aaPanel):
/www/server/panel/vhost/nginx/form-defense.conf

Nginx config (apt - alternative):
/etc/nginx/sites-available/form-defense -> /etc/nginx/sites-enabled/

Logs:
/var/log/form-defense/                     # Gunicorn access & error logs
/var/log/nginx/form-defense-*.log          # Nginx access & error logs (apt)
/www/wwwlogs/                              # Nginx logs (aaPanel)

aaPanel:
/www/server/panel/                         # aaPanel installation
/www/server/nginx/                         # Nginx installed by aaPanel
/www/server/mysql/                         # MySQL installed by aaPanel
```

---

## Deployment Order Summary

```
 1. SSH into server
 2. Install aaPanel               <- installs Nginx (NOT Apache) + MySQL
 3. Secure aaPanel                <- change port, password, entry URL
 4. Install Python + Node.js
 5. Create MySQL database + user  <- via aaPanel GUI or CLI
 6. Secure MySQL                  <- mysql_secure_installation
 7. Clone project to /var/www/
 8. Configure backend .env        <- MySQL creds, SECRET_KEY
 9. Run migrations + collectstatic (includes custom admin CSS)
10. Configure frontend .env.local
11. Build frontend (npm run build)
12. Create systemd services
13. Configure Nginx server block
14. Enable SSL (via aaPanel or Certbot)
15. Configure UFW firewall
16. Verify everything works
```
