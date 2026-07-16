# Guide de Configuration : Environnement Virtuel Python (venv)

## Configuration Étape par Étape

1. **Créer l'environnement virtuel:** Étape 1.
Ouvre un terminal dans le dossier de ton projet et génère le dossier `.venv` :

```bash
python -m venv .venv

```

2. **Activer l'environnement:** Étape 2.
Active l'environnement pour que ton terminal utilise le Python et le `pip` isolés du projet :

```bash
source .venv/bin/activate

```

*(Tu devrais maintenant voir le préfixe `(.venv)` s'afficher au début de ta ligne de commande !)*


3. **Mettre à jour pip et installer RPyC:** Étape 3.
Installe la bibliothèque de communication RPC :

```bash
pip install --upgrade pip
pip install rpyc

```

---

# Projet Traitement Distribué : Salade de Fruits RPyC

Ce projet implémente un système de calcul distribué Master-Slave tolérant aux pannes basé sur **RPyC**. Les esclaves (Slaves) se connectent au Maître (Master) pour récupérer des tâches de découpe de fruits, simuler le traitement, et renvoyer le résultat. Le Master affiche un tableau de bord dynamique de l'état d'avancement.

## Prérequis & Installation (Arch Linux)

### 1. Création et activation de l'environnement virtuel

```bash
# 1. Créez l'environnement dans le dossier .venv
python -m venv .venv

# 2. Activez-le
source .venv/bin/activate

```

### 2. Installation des dépendances

Une fois l'environnement activé (le prompt de votre terminal doit afficher `(.venv)`), installez RPyC :

```bash
pip install --upgrade pip
pip install rpyc

```

---

## Comment lancer le projet

### Option 1 : Lancement manuel (Trois terminaux requis)
Fait et tester sur linux avec les script sh
Version de base 
```bash
./start_slaves2.sh
```

Version Crash
```bash
./start_slaves3.sh
```

Version timeout
```bash
./start_slaves4.sh
```

Version PowerShell

Version de base 
```bash
./start_slaves2.ps1
```

Version Crash
```bash
./start_slaves3.ps1
```

Version timeout
```bash
./start_slaves4.ps1
```

## Quitter l'environnement virtuel

Lorsque vous avez terminé de travailler, vous pouvez désactiver l'environnement virtuel pour revenir au Python global du système en tapant simplement :

```bash
deactivate

```