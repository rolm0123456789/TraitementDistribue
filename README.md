# 🍏 Préparation de Salade de Fruits Distribuée - Architecture Master-Slave RPyC

Ce projet est une démonstration complète d'une architecture distribuée de type **Master-Slave** (Maître-Esclave) implémentée en Python avec la bibliothèque **RPyC (Remote Python Call)**.

Le cas d'usage consiste à paralléliser la préparation d'une salade de fruits composée de différents fruits nécessitant chacun un temps de découpe/préparation spécifique. À travers 5 étapes/exercices successifs, nous passons d'une version purement séquentielle à un système distribué de pointe doté d'un tableau de bord dynamique et d'une **tolérance complète aux pannes (résilience)**.

---

## 🛠️ Configuration de l'environnement

Pour pouvoir exécuter les exercices, vous devez d'abord installer la dépendance `rpyc` et configurer les scripts de lancement. Un script automatisé `setup_env.sh` est fourni à cet effet.

### Lancement automatique de la configuration
```bash
bash setup_env.sh
```

Ce script va :
1. Installer la bibliothèque `rpyc` via `pip`.
2. Attribuer les permissions d'exécution (`chmod +x`) aux différents scripts shell de test.

---

## 📂 Détail des Exercices

### ⏱️ Exercice 0 : Version Séquentielle (`0_seq.py`)
Cette version simule la préparation séquentielle (une seule personne/un seul thread) de tous les fruits les uns après les autres.
- **Liste des fruits & Temps de préparation :**
  - Pomme : 5 secondes
  - Banane : 3 secondes
  - Orange : 10 secondes
  - Kiwi : 4 secondes
  - Fraise : 1 seconde
- **Temps total théorique :** $5 + 3 + 10 + 4 + 1 = 23\text{ secondes}$.
- **Lancement :**
  ```bash
  python 0_seq.py
  ```

---

### 🔌 Exercice 1 : Client-Serveur RPyC Simple (`1_server.py` et `1_client.py`)
Introduction à la communication RPC avec RPyC. Un serveur expose une méthode retournant la réponse universelle `42`, et un client s'y connecte pour la récupérer de manière transparente.
- **Lancement du Serveur :**
  ```bash
  python 1_server.py
  ```
- **Lancement du Client (dans un autre terminal) :**
  ```bash
  python 1_client.py
  ```

---

### 📊 Exercice 2 : Système Master-Slave de Base (`2_master.py` & `2_slave.py`)
Implémentation d'une distribution de tâches parallèle.
- **Le Master (`2_master.py`)** maintient l'état global et affiche un **tableau de bord en temps réel dans la console** (avec couleurs ANSI et barre de progression globale). Il écoute sur le port par défaut de RPyC (`18812`).
- **Les Slaves (`2_slave.py`)** se connectent au Master, demandent du travail de manière asynchrone, simulent la découpe du fruit attribué (`time.sleep`), puis soumettent leur résultat.
- **Lancement automatique de 6 esclaves en parallèle :**
  ```bash
  ./start_slaves2.sh
  ```
- *Note :* Lorsque toutes les tâches sont complétées, le Master affiche un message de succès et s'éteint proprement de manière automatique.

---

### 💥 Exercice 3 : Démonstration de Panne (Sans Résilience)
Que se passe-t-il si un esclave s'arrête brusquement au milieu de sa tâche dans le système de base ?
Le script `start_slaves3.sh` lance le Master et les Slaves de l'Exercice 2, puis applique un signal de mort brutale (`SIGKILL -9`) sur le premier esclave (qui venait d'obtenir la préparation de la pomme).
- **Lancement :**
  ```bash
  ./start_slaves3.sh
  ```
- **Observation :** Le fruit assigné à l'esclave tué reste bloqué à l'état `"En cours"` indéfiniment. Le système n'avance plus et la salade de fruits ne peut jamais être complétée. Cela met en évidence la nécessité d'une gestion de la tolérance aux pannes.

---

### 🛡️ Exercice 4 : Système Master-Slave Résilient (`4_master.py` & `4_slave.py`)
Cette version résout le problème de l'exercice 3 en implémentant des mécanismes de **tolérance aux pannes** et de **gestion du cycle de vie**.

#### Concepts clés de la résilience :
1. **Timeout Détecteur :** Le Master (`4_master.py`) suit le temps de début de chaque tâche assignée. Si un esclave met plus de temps que la durée prévue du fruit $+ 3\text{ secondes}$ de marge, le Master considère que l'esclave a crashé.
2. **Réassignation Dynamique :** La tâche expirée est instantanément repassée à l'état `"PENDING"`. Un autre esclave libre (en attente active polie de 1 seconde) la récupère immédiatement.
3. **Protection contre les retours tardifs :** Si un esclave subit un simple ralentissement réseau (faux positif de timeout) et finit par soumettre son résultat alors que la tâche a déjà été réassignée et complétée par un autre, le Master ignore poliment sa soumission tardive.
4. **Déconnexion propre :** Dès que tout est fini, les esclaves reçoivent l'instruction `"SHUTDOWN"` et se déconnectent proprement, évitant les erreurs de socket ou de protocole.

- **Lancement de la simulation du Chaos :**
  Le script `start_slaves4.sh` lance l'environnement, puis applique une roulette russe en tuant aléatoirement entre 1 et 3 esclaves en plein travail :
  ```bash
  ./start_slaves4.sh
  ```
- **Observation :** Malgré les morts brutales d'esclaves, le Master détecte automatiquement les timeouts, réassigne les tâches perdues aux esclaves survivants, met à jour son journal d'événements systèmes en direct, et finalise la salade de fruits avec succès à 100% !

---

## 🤖 Script de Vérification Globale

Un script d'intégration `verify_all.py` a été utilisé pour valider automatiquement les exercices (il n'est pas inclus dans ce dépôt).

Pour reproduire la vérification, exécutez les exercices manuellement (sections ci-dessus) ou fournissez votre propre script d'intégration.

### Résumé attendu de l'exécution :
```text
==============================================
🚀 STARTING VERIFICATION OF ALL EXERCISES 🚀
==============================================

--- Test Exercice 0 (Séquentiel) ---
✅ Exercice 0: SUCCESS (took 23.02s)

--- Test Exercice 1 (RPyC Client/Serveur) ---
✅ Exercice 1: SUCCESS

--- Test Exercice 2 (Master/Slave de base) ---
✅ Exercice 2: SUCCESS

--- Test Exercice 4 (Master/Slave Résilient) ---
✅ Exercice 4: SUCCESS

================ SUMMARY ================
Exercice 0  : PASSED
Exercice 1  : PASSED
Exercice 2  : PASSED
Exercice 4  : PASSED
=========================================
🎉 ALL EXERCISES RUN CORRECTLY!
```

---

## 🌟 Points Forts du Système Distribue
- **Dashboard Réactif :** Interface textuelle fluide affichant l'état précis (En attente, En cours, Terminé) de chaque fruit, l'identité de l'esclave assigné, une barre de progression dynamique de $0\%$ à $100\%$ et les logs des pannes en temps réel.
- **Sécurité & Concurrence :** Utilisation de verrous de threads (`threading.Lock`) sur toutes les requêtes RPC pour éviter les conditions de concurrence critique lors de l'accès aux structures de données partagées du Master.
- **Robustesse :** Résiste à la mort de la moitié de ses travailleurs sans perte de données et sans blocage.
