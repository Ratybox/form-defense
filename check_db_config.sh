#!/bin/bash

# Script pour vérifier la configuration de la base de données

echo "=========================================="
echo "Vérification de la configuration MySQL"
echo "=========================================="
echo ""

# Vérifier le fichier .env
ENV_FILE="/var/www/form-defense/backend/.env"

if [ -f "$ENV_FILE" ]; then
    echo "📄 Configuration depuis .env:"
    echo "----------------------------"
    grep -E "^DB_|^USE_MYSQL" "$ENV_FILE" | sed 's/PASSWORD=.*/PASSWORD=***HIDDEN***/'
    echo ""
else
    echo "⚠️  Fichier .env non trouvé à: $ENV_FILE"
    echo ""
fi

# Vérifier les valeurs par défaut dans settings.py
echo "📋 Valeurs par défaut dans settings.py:"
echo "----------------------------------------"
cd /var/www/form-defense/backend
source venv/bin/activate 2>/dev/null
python3 << EOF
import os
import sys
sys.path.insert(0, '/var/www/form-defense/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Charger les settings
from django.conf import settings

print(f"USE_MYSQL: {os.environ.get('USE_MYSQL', 'True')}")
print(f"DB_NAME: {os.environ.get('DB_NAME', 'app_db')}")
print(f"DB_USER: {os.environ.get('DB_USER', 'app_user')}")
print(f"DB_HOST: {os.environ.get('DB_HOST', 'localhost')}")
print(f"DB_PORT: {os.environ.get('DB_PORT', '3306')}")
print(f"DB_PASSWORD: {'***' if os.environ.get('DB_PASSWORD') else 'Non défini'}")
EOF

echo ""
echo "=========================================="
echo "Test de connexion MySQL"
echo "=========================================="
echo ""

# Récupérer les credentials depuis .env ou utiliser les valeurs par défaut
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

DB_NAME=${DB_NAME:-app_db}
DB_USER=${DB_USER:-app_user}
DB_PASSWORD=${DB_PASSWORD:-password123}
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-3306}

echo "Tentative de connexion avec:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Tester la connexion MySQL
mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SELECT 'Connexion réussie!' AS Status, DATABASE() AS Current_Database, USER() AS Current_User;" 2>&1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connexion MySQL réussie!"
    echo ""
    echo "Informations de la base de données:"
    mysql -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e "SHOW VARIABLES LIKE 'port'; SELECT DATABASE() AS 'Current Database', USER() AS 'Current User';" 2>/dev/null
else
    echo ""
    echo "❌ Échec de la connexion MySQL"
    echo ""
    echo "Vérifications à faire:"
    echo "  1. MySQL est-il démarré? (systemctl status mysql)"
    echo "  2. Les credentials sont-ils corrects?"
    echo "  3. L'utilisateur a-t-il les permissions?"
fi

echo ""
echo "=========================================="
echo "Vérification via Django"
echo "=========================================="
echo ""

cd /var/www/form-defense/backend
source venv/bin/activate 2>/dev/null

python3 manage.py dbshell << EOF
SELECT 'Connexion Django réussie!' AS Status;
SELECT DATABASE() AS 'Current Database';
SHOW VARIABLES LIKE 'port';
EXIT;
EOF
