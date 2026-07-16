# Préparation de Salade de Fruits Distribuée - Architecture Master-Slave RPyC

Ce projet est une démonstration complète d'une architecture distribuée de type **Master-Slave** (Maître-Esclave) implémentée en Python avec la bibliothèque **RPyC (Remote Python Call)**.

Le cas d'usage consiste à paralléliser la préparation d'une salade de fruits composée de différents fruits nécessitant chacun un temps de découpe/préparation spécifique. À travers plusieurs étapes/exercices successifs, nous passons d'une version purement séquentielle à un système distribué de pointe : **tableau de bord dynamique**, **tolérance aux pannes (résilience)**, **ordonnancement par dépendances**, et **arrêt propre du Master** lorsque tous les esclaves meurent.

---

## Configuration de l'environnement

Pour pouvoir exécuter les exercices, vous devez d'abord installer la dépendance `rpyc` et configurer les scripts de lancement. Un script automatisé `setup_env.sh` est fourni à cet effet.

### Lancement automatique de la configuration
```bash
bash setup_env.sh
```

Ce script va :
1. Installer la bibliothèque `rpyc` via `pip`.
2. Attribuer les permissions d'exécution (`chmod +x`) aux différents scripts shell de test.

---

## Détail des Exercices

### Exercice 0 : Version Séquentielle (`0_seq.py`)
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

### Exercice 1 : Client-Serveur RPyC Simple (`1_server.py` et `1_client.py`)
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

### Exercice 2 : Système Master-Slave de Base (`2_master.py` & `2_slave.py`)
Implémentation d'une distribution de tâches parallèle.
- **Le Master (`2_master.py`)** maintient l'état global et affiche un **tableau de bord en temps réel dans la console** (avec couleurs ANSI et barre de progression globale). Il écoute sur le port par défaut de RPyC (`18812`).
- **Les Slaves (`2_slave.py`)** se connectent au Master, demandent du travail de manière asynchrone, simulent la découpe du fruit attribué (`time.sleep`), puis soumettent leur résultat.
- **Lancement automatique de 6 esclaves en parallèle :**
  ```bash
  ./start_slaves2.sh
  ```
- *Note :* Lorsque toutes les tâches sont complétées, le Master affiche un message de succès et s'éteint proprement de manière automatique.

---

### Exercice 3 : Démonstration de Panne (Sans Résilience)
Que se passe-t-il si un esclave s'arrête brusquement au milieu de sa tâche dans le système de base ?
Le script `start_slaves3.sh` lance le Master et les Slaves de l'Exercice 2, puis applique un signal de mort brutale (`SIGKILL -9`) sur le premier esclave (qui venait d'obtenir la préparation de la pomme).
- **Lancement :**
  ```bash
  ./start_slaves3.sh
  ```
- **Observation :** Le fruit assigné à l'esclave tué reste bloqué à l'état `"En cours"` indéfiniment. Le système n'avance plus et la salade de fruits ne peut jamais être complétée. Cela met en évidence la nécessité d'une gestion de la tolérance aux pannes.

---

### Exercice 4 : Système Master-Slave Résilient (`4_master.py` & `4_slave.py`)
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

### Exercice 5 : Ordonnancement par Graphe de Dépendances (`5_master.py` & `5_slave.py`)
Cette version introduit un **ordonnancement par IDs** : certaines tâches ne peuvent démarrer qu'après la complétion d'autres (dépendances).

#### Graphe des fruits :
| ID | Fruit  | Temps | Dépendances      |
|----|--------|-------|------------------|
| 0  | pomme  | 5 s   | —                |
| 1  | orange | 10 s  | —                |
| 2  | banane | 3 s   | pomme (0)        |
| 3  | kiwi   | 4 s   | orange (1)       |
| 4  | fraise | 2 s   | banane (2), kiwi (3) |

- Les tâches sans dépendances démarrent en `"En attente"` ; les autres sont `"Verrouillé"` jusqu'à ce que tous les IDs requis soient `"Terminé"`.
- Le Master conserve la **tolérance aux timeouts** (réassignation) et un tableau de bord avec colonne ID.
- **Lancement :**
  ```bash
  ./start_slaves5.sh
  ```
- *Note :* Le script peut tuer aléatoirement 1 à 3 esclaves (chaos) ; les dépendances restent respectées grâce aux slaves survivants.

---

### Exercice 6 : Arrêt propre si tous les Slaves meurent (`6_master.py` & `6_slave.py`)
Même en version résiliente, si **tous** les esclaves crashent, plus personne ne peut terminer le travail. Cet exercice ajoute la **détection de mort collective** et la **fermeture propre du serveur Master**.

#### Concepts clés :
1. **Suivi des connexions RPyC :** le Master enregistre chaque esclave via `on_connect` / `on_disconnect` et l'ID fourni à `get_task`.
2. **Libération immédiate des tâches :** à la déconnexion (ou au timeout) d'un slave, ses tâches encore `"PROCESSING"` repassent en `"PENDING"`.
3. **Extermination totale → arrêt propre :** dès qu'au moins un slave s'est connecté et qu'il n'en reste plus aucun vivant, le Master affiche un message d'arrêt, ferme le socket (`server.close()`), puis quitte le processus proprement — au lieu de rester bloqué indéfiniment.
4. **Watchdog de secours :** un fil périodique nettoie les connexions mortes non signalées tout de suite (ex. après `kill -9`).
5. **Succès normal :** si toutes les tâches sont quand même complétées, le Master s'arrête aussi proprement (comme en V4).

- **Lancement de la simulation « tous les slaves meurent » :**
  Le script `start_slaves6.sh` démarre le Master V6 et 6 esclaves, attend qu'ils prennent des tâches, puis applique un **SIGKILL sur tous les esclaves**, et vérifie que le Master s'arrête de lui-même :
  ```bash
  ./start_slaves6.sh
  ```
- **Observation :** le journal affiche successivement les morts (`[Mort]`, `[Libéré]`), puis :
  `Tous les esclaves sont morts — tâches restantes abandonnées. Arrêt propre du serveur.`
  Le script shell confirme le succès si le processus Master a disparu sous ~15 secondes.

---