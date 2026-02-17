#!/bin/bash

# Script de déploiement rapide pour Form Defense
# Usage: ./deploy.sh

set -e  # Arrêter en cas d'erreur

echo "🚀 Déploiement de Form Defense..."

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="/var/www/form-defense"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Erreur: Le répertoire $PROJECT_DIR n'existe pas${NC}"
    exit 1
fi

cd $PROJECT_DIR

echo -e "${YELLOW}📦 Mise à jour du code depuis GitHub...${NC}"
git pull origin main || echo "⚠️  Git pull échoué, continuons..."

# Backend
echo -e "${YELLOW}🔙 Configuration du backend...${NC}"
cd $BACKEND_DIR

if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

# Installation des dépendances système pour mysqlclient (si nécessaire)
if ! python -c "import MySQLdb" 2>/dev/null; then
    echo "Installation des dépendances système pour MySQL..."
    apt install -y default-libmysqlclient-dev pkg-config 2>/dev/null || echo "Dépendances déjà installées ou erreur (continuez)"
fi

pip install -r requirements.txt

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Le fichier .env n'existe pas. Créez-le avec les variables d'environnement nécessaires.${NC}"
fi

echo "Application des migrations..."
python manage.py migrate

echo "Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

deactivate

# Frontend
echo -e "${YELLOW}🎨 Configuration du frontend...${NC}"
cd $FRONTEND_DIR

echo "Installation des dépendances..."
npm install

# Vérifier si .env.local existe
if [ ! -f ".env.local" ]; then
    echo -e "${YELLOW}⚠️  Le fichier .env.local n'existe pas. Créez-le avec NEXT_PUBLIC_API_URL.${NC}"
fi

echo "Build de l'application..."
npm run build

# Redémarrer les services
echo -e "${YELLOW}🔄 Redémarrage des services...${NC}"
systemctl restart form-defense-backend
systemctl restart form-defense-frontend
systemctl reload nginx

echo -e "${GREEN}✅ Déploiement terminé avec succès!${NC}"
echo -e "${GREEN}🌐 Votre application est accessible sur http://64.31.4.29${NC}"

# Vérifier le statut des services
echo ""
echo "Statut des services:"
systemctl status form-defense-backend --no-pager -l
echo ""
systemctl status form-defense-frontend --no-pager -l
