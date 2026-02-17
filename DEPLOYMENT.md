# Guide de Déploiement - Form Defense

Guide complet pour déployer l'application Django + Next.js sur le VPS Ubuntu (root@64.31.4.29)

## 📋 Prérequis

- Accès SSH au serveur: `root@64.31.4.29`
- Repository GitHub cloné sur le serveur
- Ubuntu Server installé

---

## 🔧 Étape 1: Préparation du Serveur

### 1.1 Connexion SSH

```bash
ssh root@64.31.4.29
```

### 1.2 Mise à jour du système

```bash
apt update && apt upgrade -y
```

### 1.3 Installation des outils de base

```bash
apt install -y curl wget git ufw build-essential
```

---

## 🐍 Étape 2: Installation de Python et dépendances

### 2.1 Installation de Python 3.11+ et pip

```bash
apt install -y python3 python3-pip python3-venv python3-dev
```

### 2.2 Vérification de l'installation

```bash
python3 --version
pip3 --version
```

---

## 📦 Étape 3: Installation de Node.js et npm

### 3.1 Installation de Node.js 20.x (LTS)

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
```

### 3.2 Vérification de l'installation

```bash
node --version
npm --version
```

---

## 🗄️ Étape 4: Installation et configuration de MySQL

### 4.1 Installation de MySQL Server

```bash
apt install -y mysql-server
```

### 4.2 Sécurisation de MySQL (optionnel mais recommandé)

```bash
mysql_secure_installation
```

Répondez aux questions:
- **Valider le mot de passe?** → `Y` puis entrez un mot de passe root fort
- **Supprimer les utilisateurs anonymes?** → `Y`
- **Désactiver la connexion root à distance?** → `Y`
- **Supprimer la base de test?** → `Y`
- **Recharger les privilèges?** → `Y`

### 4.3 Création de la base de données et de l'utilisateur

```bash
mysql -u root -p
```

Dans le prompt MySQL, exécutez les commandes suivantes:

```sql
-- Créer la base de données
CREATE DATABASE app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Créer l'utilisateur
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'password123';

-- Accorder les privilèges
GRANT ALL PRIVILEGES ON app_db.* TO 'app_user'@'localhost';

-- Appliquer les changements
FLUSH PRIVILEGES;

-- Quitter MySQL
EXIT;
```

### 4.4 Installation des dépendances pour MySQL (optionnel avec PyMySQL)

**Note:** Nous utilisons PyMySQL au lieu de mysqlclient car il est plus facile à installer et compatible avec Python 3.6.

Si vous préférez utiliser mysqlclient, installez ces dépendances:
```bash
apt install -y default-libmysqlclient-dev pkg-config
```

Sinon, PyMySQL sera installé automatiquement via pip (pas besoin de dépendances système).

### 4.5 Vérification de l'installation

```bash
mysql -u app_user -p app_db
# Entrez le mot de passe: password123
# Si la connexion fonctionne, tapez EXIT;
```

### 4.6 Installation de phpMyAdmin (optionnel mais recommandé)

phpMyAdmin permet de gérer la base de données MySQL via une interface web.

#### 4.6.1 Installation de phpMyAdmin

```bash
# Installer PHP et les extensions nécessaires
apt install -y php php-fpm php-mysql php-mbstring php-zip php-gd php-json php-curl

# Installer phpMyAdmin
apt install -y phpmyadmin
```

Pendant l'installation, vous serez invité à:
- **Serveur web à configurer:** Sélectionnez `nginx` (utilisez la touche espace pour sélectionner, puis Entrée)
- **Configurer la base de données:** Choisissez `Oui`
- **Mot de passe de l'application:** Laissez vide ou entrez un mot de passe (optionnel)

#### 4.6.2 Configuration de phpMyAdmin pour Nginx

```bash
# Créer le lien symbolique vers phpMyAdmin
ln -s /usr/share/phpmyadmin /var/www/html/phpmyadmin

# Ou créer un lien dans votre projet
ln -s /usr/share/phpmyadmin /var/www/form-defense/phpmyadmin
```

#### 4.6.3 Configuration PHP-FPM

```bash
# Vérifier que PHP-FPM est démarré
systemctl start php7.4-fpm  # ou php8.1-fpm selon votre version
systemctl enable php7.4-fpm

# Vérifier la version PHP installée
php -v
```

#### 4.6.4 Ajouter phpMyAdmin à la configuration Nginx

Modifiez `/etc/nginx/sites-available/form-defense` pour ajouter la configuration phpMyAdmin:

```bash
nano /etc/nginx/sites-available/form-defense
```

Ajoutez cette section **avant** le bloc `server` principal ou **dans** le bloc server existant:

```nginx
# Configuration phpMyAdmin
location /phpmyadmin {
    alias /usr/share/phpmyadmin;
    index index.php;
    
    location ~ ^/phpmyadmin/(.+\.php)$ {
        alias /usr/share/phpmyadmin/$1;
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;  # Ajustez selon votre version PHP
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $request_filename;
        include fastcgi_params;
    }
    
    location ~ ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
        alias /usr/share/phpmyadmin/$1;
    }
}
```

**Note:** Remplacez `php7.4-fpm` par votre version PHP (vérifiez avec `php -v` et `ls /var/run/php/`).

#### 4.6.5 Sécurisation de phpMyAdmin (recommandé)

Pour sécuriser l'accès à phpMyAdmin, vous pouvez:

**Option 1: Restreindre l'accès par IP**

Ajoutez dans la configuration Nginx:

```nginx
location /phpmyadmin {
    # Autoriser uniquement certaines IPs (remplacez par votre IP)
    allow 64.31.4.29;
    allow VOTRE_IP_PUBLIQUE;
    deny all;
    
    alias /usr/share/phpmyadmin;
    # ... reste de la configuration
}
```

**Option 2: Utiliser une authentification HTTP basique**

```bash
# Installer apache2-utils pour créer les fichiers de mot de passe
apt install -y apache2-utils

# Créer un utilisateur pour phpMyAdmin
htpasswd -c /etc/nginx/.htpasswd admin
# Entrez un mot de passe fort

# Ajouter dans la configuration Nginx avant location /phpmyadmin:
auth_basic "Accès phpMyAdmin";
auth_basic_user_file /etc/nginx/.htpasswd;
```

**Option 3: Changer l'URL d'accès**

Au lieu de `/phpmyadmin`, utilisez une URL personnalisée:

```nginx
location /db-admin-secret-url {
    alias /usr/share/phpmyadmin;
    # ... reste de la configuration
}
```

#### 4.6.6 Recharger Nginx

```bash
# Tester la configuration
nginx -t

# Recharger Nginx
systemctl reload nginx
```

#### 4.6.7 Accéder à phpMyAdmin

Une fois configuré, vous pouvez accéder à phpMyAdmin via:
- `http://64.31.4.29/phpmyadmin`
- Ou l'URL personnalisée que vous avez définie

**Identifiants de connexion:**
- **Serveur:** `localhost` ou `127.0.0.1`
- **Utilisateur:** `app_user`
- **Mot de passe:** `password123`

#### 4.6.8 Vérification

```bash
# Vérifier que PHP-FPM fonctionne
systemctl status php7.4-fpm

# Vérifier les logs en cas d'erreur
tail -f /var/log/nginx/form-defense-error.log
```

---

## 🌐 Étape 5: Installation et configuration de Nginx

### 4.1 Installation de Nginx

```bash
apt install -y nginx
```

### 4.2 Démarrage et activation de Nginx

```bash
systemctl start nginx
systemctl enable nginx
```

### 4.3 Vérification du statut

```bash
systemctl status nginx
```

---

## 📁 Étape 6: Configuration de la structure du projet

### 5.1 Création des répertoires

```bash
mkdir -p /var/www/form-defense
cd /var/www/form-defense
```

### 5.2 Clonage du repository (si pas déjà fait)

```bash
# Si vous avez déjà cloné, passez à l'étape suivante
# Sinon:
git clone <VOTRE_REPO_GITHUB_URL> .
```

### 5.3 Vérification de la structure

```bash
ls -la
# Vous devriez voir: backend/, frontend/, README.md, etc.
```

---

## 🔙 Étape 7: Configuration du Backend Django

### 6.1 Création de l'environnement virtuel Python

```bash
cd /var/www/form-defense/backend
python3 -m venv venv
source venv/bin/activate
```

### 7.2 Installation des dépendances Python

**Note:** PyMySQL sera installé automatiquement via requirements.txt (pas besoin de dépendances système).

```bash
# Mettre à jour pip d'abord
pip install --upgrade pip

# Installer toutes les dépendances depuis requirements.txt
pip install -r requirements.txt
```

**⚠️ IMPORTANT:** Si vous voyez une erreur concernant `rest_framework`, le nom correct du package est `djangorestframework` (avec un tiret). Utilisez toujours `pip install -r requirements.txt` pour installer toutes les dépendances correctement.

**Vérification de l'installation:**

```bash
# Vérifier que Django est installé
python -c "import django; print(django.get_version())"

# Vérifier que DRF est installé
python -c "import rest_framework; print('DRF installé')"

# Vérifier que PyMySQL est installé
python -c "import pymysql; print('PyMySQL installé')"
```

### 7.3 Gunicorn est déjà inclus dans requirements.txt

Gunicorn sera installé automatiquement avec les autres dépendances. Pas besoin de l'installer séparément.

### 7.4 Création du fichier .env pour les variables d'environnement

```bash
cd /var/www/form-defense/backend
nano .env
```

**Contenu du fichier `.env`:**

```env
SECRET_KEY=&6q3u%ot=f-j-fq%z@rnjz!su!()vi$h3%754idqco_t$b9klg
DEBUG=False
ALLOWED_HOSTS=64.31.4.29,tov.afaq.sa
CORS_ALLOWED_ORIGINS=http://64.31.4.29,https://tov.afaq.sa

# Configuration MySQL
USE_MYSQL=True
DB_NAME=app_db
DB_USER=app_user
DB_PASSWORD=password123
DB_HOST=localhost
DB_PORT=3306
```

**Générer une SECRET_KEY sécurisée:**

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 7.5 Vérification de la connexion à MySQL

Avant de continuer, testez la connexion:

```bash
cd /var/www/form-defense/backend
source venv/bin/activate
python manage.py dbshell
```

Si la connexion fonctionne, vous verrez le prompt MySQL. Tapez `exit;` pour quitter.

### 7.6 Modification de settings.py pour la production

```bash
cd /var/www/form-defense/backend/config
nano settings.py
```

**Modifications à apporter:**

```python
# Remplacer les lignes suivantes:
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Ajouter à la fin du fichier:
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# CORS - Mettre à jour avec votre domaine/IP
CORS_ALLOWED_ORIGINS = [
    "http://64.31.4.29",
    "https://64.31.4.29",
    # Ajoutez votre domaine si vous en avez un
]
```

### 7.7 Application des migrations

```bash
cd /var/www/form-defense/backend
source venv/bin/activate
python manage.py migrate
```

### 7.8 Collecte des fichiers statiques

```bash
python manage.py collectstatic --noinput
```

### 7.9 Création d'un superutilisateur (optionnel)

```bash
python manage.py createsuperuser
```

---

## 🎨 Étape 8: Configuration du Frontend Next.js

### 8.1 Installation des dépendances Node.js

```bash
cd /var/www/form-defense/frontend
npm install
```

### 8.2 Modification de l'URL de l'API dans le frontend

```bash
cd /var/www/form-defense/frontend/app
nano page.tsx
```

**Remplacer l'URL de l'API:**

```typescript
// Remplacer cette ligne:
const response = await fetch('http://localhost:8000/api/entries/', {

// Par:
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://64.31.4.29:8000';
const response = await fetch(`${API_URL}/api/entries/`, {
```

### 8.3 Création du fichier .env.local

```bash
cd /var/www/form-defense/frontend
nano .env.local
```

**Contenu:**

```env
NEXT_PUBLIC_API_URL=http://64.31.4.29:8000
```

### 8.4 Build de l'application Next.js

```bash
cd /var/www/form-defense/frontend
npm run build
```

---

## ⚙️ Étape 9: Configuration de Systemd pour les services

### 9.1 Création du service Gunicorn pour Django

```bash
nano /etc/systemd/system/form-defense-backend.service
```

**Contenu du fichier:**

```ini
[Unit]
Description=Form Defense Django Backend
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/form-defense/backend
Environment="PATH=/var/www/form-defense/backend/venv/bin"
ExecStart=/var/www/form-defense/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9.2 Création du service Next.js

```bash
nano /etc/systemd/system/form-defense-frontend.service
```

**Contenu du fichier:**

```ini
[Unit]
Description=Form Defense Next.js Frontend
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/form-defense/frontend
Environment="NODE_ENV=production"
Environment="NEXT_PUBLIC_API_URL=http://64.31.4.29:8000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 9.3 Activation et démarrage des services

```bash
# Recharger systemd
systemctl daemon-reload

# Activer les services au démarrage
systemctl enable form-defense-backend
systemctl enable form-defense-frontend

# Démarrer les services
systemctl start form-defense-backend
systemctl start form-defense-frontend

# Vérifier le statut
systemctl status form-defense-backend
systemctl status form-defense-frontend
```

---

## 🔒 Étape 10: Configuration de Nginx

### 10.1 Création de la configuration Nginx

```bash
nano /etc/nginx/sites-available/form-defense
```

**Contenu du fichier:**

```nginx
# Redirection HTTP vers HTTPS (optionnel, si vous avez un certificat SSL)
# server {
#     listen 80;
#     server_name 64.31.4.29;
#     return 301 https://$server_name$request_uri;
# }

# Configuration principale
server {
    listen 80;
    # Si vous avez un domaine, ajoutez-le ici:
    # listen 443 ssl http2;
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
    
    server_name 64.31.4.29;

    # Logs
    access_log /var/log/nginx/form-defense-access.log;
    error_log /var/log/nginx/form-defense-error.log;

    # Taille maximale des uploads
    client_max_body_size 10M;

    # Frontend Next.js (port 3000)
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

    # Backend Django API (port 8000)
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

    # Fichiers statiques Django
    location /static/ {
        alias /var/www/form-defense/backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Fichiers statiques Next.js
    location /_next/static/ {
        alias /var/www/form-defense/frontend/.next/static/;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Configuration phpMyAdmin
    location /phpmyadmin {
        alias /usr/share/phpmyadmin;
        index index.php;
        
        # Sécurité: Restreindre l'accès par IP (optionnel)
        # allow 64.31.4.29;
        # deny all;
        
        location ~ ^/phpmyadmin/(.+\.php)$ {
            alias /usr/share/phpmyadmin/$1;
            fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;  # Ajustez selon votre version PHP
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME $request_filename;
            include fastcgi_params;
        }
        
        location ~ ^/phpmyadmin/(.+\.(jpg|jpeg|gif|css|png|js|ico|html|xml|txt))$ {
            alias /usr/share/phpmyadmin/$1;
        }
    }

    # Sécurité: Masquer la version de Nginx
    server_tokens off;

    # Headers de sécurité
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 10.2 Activation de la configuration

```bash
# Créer le lien symbolique
ln -s /etc/nginx/sites-available/form-defense /etc/nginx/sites-enabled/

# Supprimer la configuration par défaut (optionnel)
rm /etc/nginx/sites-enabled/default

# Tester la configuration Nginx
nginx -t

# Recharger Nginx
systemctl reload nginx
```

---

## 🔥 Étape 11: Configuration du Firewall (UFW)

### 11.1 Configuration des règles de pare-feu

```bash
# Autoriser SSH (IMPORTANT: faites-le en premier!)
ufw allow 22/tcp

# Autoriser HTTP
ufw allow 80/tcp

# Autoriser HTTPS (si vous utilisez SSL)
ufw allow 443/tcp

# Activer le pare-feu
ufw enable

# Vérifier le statut
ufw status
```

---

## ✅ Étape 12: Vérification et Tests

### 12.1 Vérifier que les services fonctionnent

```bash
# Vérifier le backend
curl http://127.0.0.1:8000/api/entries/

# Vérifier le frontend
curl http://127.0.0.1:3000

# Vérifier via Nginx
curl http://64.31.4.29/api/entries/
curl http://64.31.4.29/
```

### 12.2 Vérifier les logs en cas de problème

```bash
# Logs backend
journalctl -u form-defense-backend -f

# Logs frontend
journalctl -u form-defense-frontend -f

# Logs Nginx
tail -f /var/log/nginx/form-defense-error.log
tail -f /var/log/nginx/form-defense-access.log
```

---

## 🔄 Étape 13: Commandes de maintenance

### 13.0 Script de déploiement automatique (optionnel)

Un script `deploy.sh` est disponible pour automatiser les mises à jour:

```bash
cd /var/www/form-defense
chmod +x deploy.sh
./deploy.sh
```

Ce script:
- Met à jour le code depuis GitHub
- Installe les dépendances backend/frontend
- Applique les migrations
- Collecte les fichiers statiques
- Build le frontend
- Redémarre tous les services

### 13.1 Redémarrer les services

```bash
# Redémarrer le backend
systemctl restart form-defense-backend

# Redémarrer le frontend
systemctl restart form-defense-frontend

# Redémarrer Nginx
systemctl restart nginx
```

### 13.2 Mettre à jour le code depuis GitHub

```bash
cd /var/www/form-defense

# Sauvegarder la base de données (si nécessaire)
cp backend/db.sqlite3 backend/db.sqlite3.backup

# Pull les dernières modifications
git pull origin main

# Backend: Mettre à jour les dépendances et migrations
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart form-defense-backend

# Note: Si vous avez changé les credentials MySQL dans .env, 
# redémarrez le service backend pour qu'il prenne en compte les nouveaux paramètres

# Frontend: Mettre à jour et rebuild
cd ../frontend
npm install
npm run build
systemctl restart form-defense-frontend
```

---

## 📝 Résumé des chemins importants

```
/var/www/form-defense/                    # Racine du projet
├── backend/                              # Application Django
│   ├── venv/                             # Environnement virtuel Python
│   ├── config/                           # Configuration Django
│   │   └── settings.py                   # Settings (modifié pour prod)
│   ├── api/                              # Application API
│   ├── staticfiles/                      # Fichiers statiques collectés
│   ├── .env                              # Variables d'environnement (contient credentials MySQL)
│   └── requirements.txt                  # Dépendances Python
│
# Base de données MySQL
# Base: app_db
# Utilisateur: app_user
# Host: localhost:3306
│
├── frontend/                             # Application Next.js
│   ├── .next/                            # Build de production
│   ├── app/                              # Pages Next.js
│   ├── .env.local                        # Variables d'environnement
│   └── package.json                      # Dépendances Node.js
│
/etc/nginx/
├── sites-available/form-defense          # Configuration Nginx
└── sites-enabled/form-defense            # Lien symbolique activé

/etc/systemd/system/
├── form-defense-backend.service          # Service Django/Gunicorn
└── form-defense-frontend.service         # Service Next.js

/var/log/nginx/
├── form-defense-access.log               # Logs d'accès Nginx
└── form-defense-error.log               # Logs d'erreur Nginx

/usr/share/phpmyadmin/                   # Installation phpMyAdmin
/etc/phpmyadmin/                          # Configuration phpMyAdmin
```

---

## 🛡️ Sécurité supplémentaire (recommandé)

### Masquer la version du serveur

Déjà configuré dans Nginx avec `server_tokens off;`

### Changer les ports par défaut (optionnel)

Si vous voulez changer les ports pour masquer les services:

1. **Modifier le port Django** (dans `/etc/systemd/system/form-defense-backend.service`):
   ```ini
   ExecStart=... --bind 127.0.0.1:8080 ...
   ```

2. **Modifier le port Next.js** (créer `/var/www/form-defense/frontend/.env.local`):
   ```env
   PORT=3001
   ```

3. **Mettre à jour Nginx** pour pointer vers les nouveaux ports

### Configuration SSL/TLS (recommandé pour production)

```bash
# Installation de Certbot
apt install -y certbot python3-certbot-nginx

# Obtenir un certificat SSL (remplacer par votre domaine)
certbot --nginx -d votre-domaine.com

# Renouvellement automatique
certbot renew --dry-run
```

---

## 🐛 Dépannage

### Le backend ne démarre pas

```bash
# Vérifier les logs
journalctl -u form-defense-backend -n 50

# Vérifier que le venv est activé et les dépendances installées
cd /var/www/form-defense/backend
source venv/bin/activate
pip list

# Si des packages manquent, réinstaller depuis requirements.txt
pip install -r requirements.txt

# Vérifier la connexion MySQL
python3 manage.py dbshell
# Si erreur, vérifiez les credentials dans .env
```

### Erreur "No module named 'rest_framework'"

**Cause:** Le package n'est pas installé ou le nom est incorrect.

**Solution:**

```bash
cd /var/www/form-defense/backend
source venv/bin/activate

# Le nom correct est djangorestframework (avec un tiret)
# Installer toutes les dépendances depuis requirements.txt
pip install -r requirements.txt

# Vérifier l'installation
python -c "import rest_framework; print('DRF installé correctement')"
```

**Note:** Ne jamais installer `rest_framework` seul. Utilisez toujours `pip install -r requirements.txt` pour installer toutes les dépendances avec les bonnes versions.

### Erreur de connexion MySQL

```bash
# Vérifier que MySQL est démarré
systemctl status mysql

# Tester la connexion manuellement
mysql -u app_user -p app_db
# Entrez le mot de passe: password123

# Vérifier les variables d'environnement dans .env
cat /var/www/form-defense/backend/.env | grep DB_
```

### Le frontend ne démarre pas

```bash
# Vérifier les logs
journalctl -u form-defense-frontend -n 50

# Vérifier que le build existe
ls -la /var/www/form-defense/frontend/.next
```

### Nginx retourne 502 Bad Gateway

```bash
# Vérifier que les services backend/frontend tournent
systemctl status form-defense-backend
systemctl status form-defense-frontend

# Vérifier les logs Nginx
tail -f /var/log/nginx/form-defense-error.log
```

### Les fichiers statiques ne se chargent pas

```bash
# Vérifier les permissions
chown -R root:root /var/www/form-defense/backend/staticfiles
chmod -R 755 /var/www/form-defense/backend/staticfiles

# Recollecter les fichiers statiques
cd /var/www/form-defense/backend
source venv/bin/activate
python manage.py collectstatic --noinput
```

### phpMyAdmin ne fonctionne pas

```bash
# Vérifier que PHP-FPM est démarré
systemctl status php7.4-fpm  # ou votre version PHP

# Vérifier la version PHP et le socket
php -v
ls /var/run/php/

# Vérifier les logs Nginx
tail -f /var/log/nginx/form-defense-error.log

# Vérifier les permissions
ls -la /usr/share/phpmyadmin

# Redémarrer PHP-FPM
systemctl restart php7.4-fpm
systemctl reload nginx
```

**Erreur 502 Bad Gateway avec phpMyAdmin:**

```bash
# Vérifier que le socket PHP-FPM correspond à votre version
ls -la /var/run/php/

# Mettre à jour la configuration Nginx avec le bon socket
# Exemple: unix:/var/run/php/php8.1-fpm.sock
```

---

## 📞 Support

En cas de problème, vérifiez:
1. Les logs systemd: `journalctl -u form-defense-backend -f`
2. Les logs Nginx: `tail -f /var/log/nginx/form-defense-error.log`
3. Les permissions des fichiers
4. Que les ports 80, 3000, 8000 sont accessibles localement

---

**✅ Votre application devrait maintenant être accessible sur `http://64.31.4.29`**
