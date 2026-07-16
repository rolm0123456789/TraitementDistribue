#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

# 1. Nettoyage de sécurité
echo "[BASH] Nettoyage des anciens processus..."
fuser -k 18812/tcp 2>/dev/null
sleep 1

# 2. Lancement du Master en arrière-plan
python 5_master.py &
sleep 2

# 3. Lancement des 6 Slaves et capture dynamique de leurs PIDs
echo "[BASH] Lancement des 6 esclaves..."
declare -A SLAVE_PIDS

for i in {1..6}; do
    python 5_slave.py $i &
    SLAVE_PIDS[$i]=$!
done

# 4. On laisse les esclaves démarrer et commencer à travailler
sleep 1.5

# 5. Détermination du chaos (On choisit de tuer entre 1 et 3 esclaves au hasard)
NB_TO_KILL=$(( 1 + RANDOM % 3 ))

# On mélange la liste des IDs d'esclaves (1 à 6) grâce à 'shuf'
SHUFFLED_SLAVES=($(shuf -e {1..6}))

echo -e "\n[BASH] Lancement de la roulette russe : Décision de tuer $NB_TO_KILL esclave(s)..."

# 6. Exécution des sentences capitales
for ((i=0; i<NB_TO_KILL; i++)); do
    SLAVE_ID=${SHUFFLED_SLAVES[$i]}
    PID=${SLAVE_PIDS[$SLAVE_ID]}

    # Vérification que le processus est toujours vivant avant de le tuer
    if kill -0 $PID 2>/dev/null; then
        kill -9 $PID
        echo -e "[BASH] LE SLAVE $SLAVE_ID (PID $PID) A ÉTÉ CRASHÉ BRUTALEMENT !"
    else
        echo -e "[BASH] Le Slave $SLAVE_ID était déjà arrêté."
    fi
done
echo -e ""
