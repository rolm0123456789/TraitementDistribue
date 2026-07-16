#!/bin/bash
# Script de configuration de l'environnement pour les exercices Master-Slave RPyC

echo "=== Configuration de l'environnement ==="

# 1. Installation de la dépendance RPyC
echo "Installation de rpyc via pip..."
python -m pip install rpyc

# 2. Attribution des droits d'exécution aux scripts shell
echo "Configuration des permissions d'exécution pour les scripts..."
chmod +x start_slaves2.sh
chmod +x start_slaves3.sh
chmod +x start_slaves4.sh
chmod +x start_slaves5.sh
chmod +x start_slaves6.sh

echo "Installation et configuration terminées avec succès !"
