# Form Defense - Projet de Stage

Site minimaliste avec Django REST Framework (backend) et Next.js (frontend) pour exercice de sécurité.

## Structure du projet


```
form-defense/
├── backend/          # Django + DRF
│   ├── api/         # Application API
│   ├── config/      # Configuration Django
│   └── manage.py
└── frontend/        # Next.js
    └── app/         # Pages Next.js
```

## Installation et démarrage

### Backend (Django)

**⚠️ IMPORTANT:** Ce projet nécessite Python 3.11 ou 3.12. Python 3.13 n'est pas compatible avec Django 3.2.25.

```bash
cd backend

# Vérifier votre version Python (doit être 3.11 ou 3.12)
python3 --version

# Si vous avez Python 3.13, installez Python 3.11 ou 3.12:
# Sur macOS avec Homebrew:
# brew install python@3.11
# ou
# brew install python@3.12

# Créer l'environnement virtuel avec Python 3.11 ou 3.12
python3.11 -m venv venv  # ou python3.12 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser

# Démarrer le serveur
python manage.py runserver
```

Le backend sera accessible sur `http://localhost:8000`

### Frontend (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Le frontend sera accessible sur `http://localhost:3000`

## API Endpoints

- `GET /api/entries/` - Liste toutes les entrées
- `POST /api/entries/` - Crée une nouvelle entrée
- `GET /api/entries/{id}/` - Détails d'une entrée
- `PUT /api/entries/{id}/` - Met à jour une entrée
- `DELETE /api/entries/{id}/` - Supprime une entrée

## Format des données

### POST /api/entries/
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "message": "Message de test",
  "password": "monMotDePasse123"
}
```

**Note:** Le mot de passe est automatiquement hashé en SHA-256 côté backend avant d'être stocké dans la base de données. Le champ `password_hash` est retourné dans la réponse mais le mot de passe en clair ne l'est jamais.

## Notes de sécurité

⚠️ Ce projet est configuré pour le développement. Pour la production, pensez à:
- Changer `SECRET_KEY` dans `settings.py`
- Désactiver `DEBUG`
- Configurer `ALLOWED_HOSTS` correctement
- Ajouter des mesures de sécurité supplémentaires (rate limiting, validation, etc.)
