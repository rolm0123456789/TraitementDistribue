# TP2 — Le hachage à grande échelle

Du **hash naïf** au **hash cohérent** avec nœuds virtuels.

Répartir des clés sur des nœuds · mesurer le rebalancement · construire un anneau cohérent — implémentation Python (stdlib uniquement).

> Enseignant : Guillaume LE LAY — ESGI · Traitements distribués (Master 2)

---

## Configuration de l'environnement

Zéro dépendance externe (`hashlib`, `bisect`, `collections`). Un venv est créé pour isoler l’environnement et lancer les démos proprement.

### Setup + lancement

```bash
bash setup_env.sh
```

Ce script :
1. Crée un virtualenv local `.venv` s’il n’existe pas
2. L’active
3. Propose un **menu** pour lancer une étape ou toutes les démos

### Commandes utiles

| Commande | Effet |
|----------|--------|
| `bash setup_env.sh` | Setup + menu interactif |
| `bash setup_env.sh setup` | Setup uniquement |
| `bash setup_env.sh all` | Les 4 démos à la suite |
| `bash setup_env.sh 1` | Étape 1 seule (idem `2`, `3`, `4`) |

### Activation manuelle

```bash
source .venv/bin/activate
python etape1_hash_naif.py demo
python etape2_rehash.py demo
python etape3_anneau.py demo
python etape4_vnodes.py demo
```

---

## Les 4 étapes

### 1. Hash naïf — `h % N`

**Fichier :** `etape1_hash_naif.py`

- Fonction `noeud_pour(cle, N)` déterministe
- Hash stable : `int(md5(cle).hexdigest(), 16)` — **pas** `hash()` de Python (randomisé par process)
- Placement : `h(cle) % N`
- Comptage de charge par nœud (`collections.Counter`)

```bash
python etape1_hash_naif.py demo
```

**À retenir :** répartition ~uniforme sur beaucoup de clés, mais **N doit rester fixe**.

---

### 2. Le rehash — `N → N+1`

**Fichier :** `etape2_rehash.py`

- Place K clés avec N nœuds, puis avec N+1
- Compte les clés qui changent de nœud
- Taux attendu : **≈ N/(N+1)** (~80 % pour N=4)

```bash
python etape2_rehash.py demo
```

**À retenir :** avec le modulo, ajouter un seul nœud casse presque tout le placement — inacceptable pour un cache ou un stockage distribué.

---

### 3. Anneau cohérent — `bisect`

**Fichier :** `etape3_anneau.py`

- Positions des nœuds sur un anneau `[0, 2³²)`
- Routage : premier nœud dont la position est **≥ h(clé)** (boucle sur le premier si besoin)
- Ajout / retrait d’un nœud sans tout rehacher

```bash
python etape3_anneau.py demo
```

**À retenir :** seul l’arc voisin bouge (≈ **K/N** clés), pas tout le keyspace.

---

### 4. Nœuds virtuels — `vnodes`

**Fichier :** `etape4_vnodes.py`

- V répliques par nœud physique (`"nœud#i"` sur l’anneau)
- Mapping vnode → nœud réel
- Mesure d’équilibrage (écart-type / coefficient de variation) selon V
- V typique ≈ **100–200** (compromis mémoire / uniformité)

```bash
python etape4_vnodes.py demo
```

**À retenir :** plus de vnodes → charge plus uniforme et déplacement plus fin à l’ajout/retrait. C’est le modèle utilisé par Dynamo, Cassandra, Riak.

---

## Structure du projet

```
Tp2/
├── guide_atelier_hashage_sans_correction.pdf   # énoncé
├── tp.webp                                     # résumé des 4 étapes
├── README.md
├── setup_env.sh                                # venv + lancement
├── etape1_hash_naif.py
├── etape2_rehash.py
├── etape3_anneau.py
└── etape4_vnodes.py
```

---

## Bilan

| Étape | Idée | Coût d’un ajout de nœud |
|-------|------|-------------------------|
| 1 Hash naïf | `h % N` | — (N fixe) |
| 2 Rehash | Mesure N→N+1 | **~80 %** des clés |
| 3 Anneau | Premier nœud ≥ h(clé) | **≈ 1/(N+1)** |
| 4 Vnodes | V points / nœud | même ordre, arcs plus fins + charge lissée |

---

## Pour aller plus loin

- Hachage pondéré (poids par nœud)
- Rendezvous hashing (HRW)
- Jump consistent hash
- Comparer l’anneau à Cassandra / DynamoDB
