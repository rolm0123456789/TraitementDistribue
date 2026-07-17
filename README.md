# Traitements Distribués — Master 2 (ESGI)

Ce dépôt regroupe l'ensemble des travaux pratiques et le projet final du cours de **Traitements Distribués**, portant sur les architectures distribuées, le hachage cohérent à grande échelle et les protocoles de diffusion Peer-to-Peer (Gossip).

---

## 👥 Membres du Projet Final (Binôme)

Le projet final et l'ensemble de ces travaux ont été réalisés en binôme par :
- **VERGUET Romain**
- **FUGIER Corentin**

---

## 📂 Structure du Dépôt

Le projet est divisé en trois dossiers principaux :
1. [**Tp1/**](file:///d:/Bureau/TraitementDistribue/Tp1) : Architecture Master-Slave distribuée avec RPyC (cas de la préparation de Salade de Fruits).
2. [**Tp2/**](file:///d:/Bureau/TraitementDistribue/Tp2) : Hachage à grande échelle (du hash naïf au hash cohérent avec nœuds virtuels).
3. [**TP_Final/**](file:///d:/Bureau/TraitementDistribue/TP_Final) : Protocole de Gossip P2P symétrique et mesure de la vitesse de convergence.

---

## 🛠️ Configuration et Utilisation

Tous les exercices sont entièrement compatibles avec **Linux** (via les scripts `.sh`) et **Windows** (via les scripts PowerShell `.ps1`).

### 🍎 TP 1 : Salade de Fruits Distribuée (Master-Slave RPyC)

Ce TP simule la découpe et la préparation de fruits par des nœuds esclaves coordonnés par un nœud maître.

#### Fonctionnalités clés :
- **Tableau de bord dynamique** : Affichage en direct dans le terminal du statut de chaque fruit (couleurs ANSI, barre de progression `█`).
- **Tolérance aux pannes** : Détection des timeouts des esclaves et réassignation dynamique des tâches perdues.
- **Ordonnancement par dépendances** : Les fruits sont préparés en respectant un graphe de dépendance acyclique (ex. la fraise attend la banane et le kiwi).
- **Arrêt propre** : Détection de la mort collective de tous les esclaves et fermeture propre du Master.

#### Exécution sous Windows :
1. Créez l'environnement et installez les dépendances :
   ```powershell
   powershell -File Tp1/setup_env.ps1
   ```
2. Lancez une simulation (ex. Exercice 2, 4, 5, ou 6) :
   ```powershell
   powershell -File Tp1/start_slaves2.ps1
   powershell -File Tp1/start_slaves6.ps1
   ```

#### Exécution sous Linux :
```bash
bash Tp1/setup_env.sh
./Tp1/start_slaves2.sh
./Tp1/start_slaves6.sh
```

---

### 🧮 TP 2 : Hachage à grande échelle (Consistent Hashing)

Ce TP implémente et compare différentes stratégies de distribution de clés sur des nœuds réseau.

#### Les 4 Étapes :
1. **Hash naïf (`h % N`)** : Placement simple et déterministe avec MD5 stable.
2. **Le rehash (`N → N+1`)** : Mesure du chaos où ~80% des clés doivent changer de nœud lors d'un ajout.
3. **Anneau cohérent (`bisect`)** : Placement sur un anneau `[0, 2³²)`. Seul l'arc voisin bouge lors de l'ajout/retrait (déplacement de ~K/N clés).
4. **Nœuds virtuels (Vnodes)** : Lissage de la charge en multipliant les répliques par nœud physique (ex. `V = 150`), réduisant considérablement l'écart-type de charge.

#### Lancement sous Windows (Menu Interactif) :
```powershell
powershell -File Tp2/setup_env.ps1
```

#### Lancement sous Linux (Menu Interactif) :
```bash
bash Tp2/setup_env.sh
```

---

### 🌐 TP Final : Peer-to-Peer Gossip Protocol

Le projet final implémente un protocole épidémique (**Gossip Protocol**) pour propager une information au sein d'un réseau P2P de manière symétrique et décentralisée (sans nœud maître).

#### Fichiers principaux :
- [**1_gossip_paire.py**](file:///d:/Bureau/TraitementDistribue/TP_Final/1_gossip_paire.py) : Gossip simple entre une paire de nœuds avec datation (timestamp) pour privilégier la valeur la plus récente.
- [**2_gossip_n.py**](file:///d:/Bureau/TraitementDistribue/TP_Final/2_gossip_n.py) : Gossip structuré en anneau où chaque nœud est connecté de façon directionnelle à son voisin.
- [**3_gossip_n.py**](file:///d:/Bureau/TraitementDistribue/TP_Final/3_gossip_n.py) : Gossip en graphe aléatoire complet (chaque itération choisit un destinataire au hasard pour faire un échange PUSH-PULL).
- [**mesure_convergence.py**](file:///d:/Bureau/TraitementDistribue/TP_Final/mesure_convergence.py) : Lance $N$ processus en anneau et mesure le nombre d'itérations nécessaires pour que tous les nœuds partagent la même valeur.
- [**convergence_final.py**](file:///d:/Bureau/TraitementDistribue/TP_Final/convergence_final.py) : Lance $N$ processus en graphe P2P aléatoire et suit la convergence globale en direct.

#### Lancement de la mesure de convergence :
Dans l'environnement configuré du TP1, lancez par exemple 5 nœuds en graphe aléatoire :
```powershell
# Windows
Tp1/.venv/Scripts/python TP_Final/convergence_final.py 5

# Linux
source Tp1/.venv/bin/activate
python TP_Final/convergence_final.py 5
```
Ou lancez la version en anneau :
```powershell
# Windows
Tp1/.venv/Scripts/python TP_Final/mesure_convergence.py 5
```
