#!/bin/bash
# Configuration de l'environnement : venv Python + dépendance RPyC
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"

echo "=== Configuration de l'environnement ==="

# 1. Création du virtualenv (si absent)
if [ ! -d "$VENV_DIR" ]; then
    echo "Création de l'environnement virtuel ($VENV_DIR)..."
    python3 -m venv "$VENV_DIR"
else
    echo "Environnement virtuel déjà présent ($VENV_DIR)."
fi

# 2. Activation
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Python : $(command -v python)"
echo "Version : $(python --version)"

# 3. Installation des dépendances dans le venv
echo "Installation de rpyc dans le venv..."
python -m pip install --upgrade pip
python -m pip install rpyc

# 4. Droits d'exécution des scripts de test
echo "Configuration des permissions d'exécution pour les scripts..."
chmod u+x start_slaves2.sh start_slaves3.sh start_slaves4.sh start_slaves5.sh start_slaves6.sh
chmod u+x setup_env.sh 2>/dev/null || true

echo ""
echo "Installation et configuration terminées avec succès !"
echo ""
echo "Pour activer l'environnement manuellement :"
echo "  source .venv/bin/activate"
echo ""
echo "Les scripts start_slaves*.sh activent automatiquement le venv s'il est présent."
