#!/bin/bash
# Exercice 6 : tue TOUS les esclaves pour vérifier l'arrêt propre du Master

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
echo "[BASH] Démarrage du Master V6..."
python 6_master.py &
MASTER_PID=$!
sleep 2

if ! kill -0 "$MASTER_PID" 2>/dev/null; then
    echo "[BASH] Le Master n'a pas démarré. Abandon."
    exit 1
fi

# 3. Lancement des 6 Slaves et capture des PIDs
echo "[BASH] Lancement des 6 esclaves..."
declare -A SLAVE_PIDS

for i in {1..6}; do
    python 6_slave.py "$i" &
    SLAVE_PIDS[$i]=$!
done

# 4. Laisser les esclaves se connecter et commencer le travail
echo "[BASH] Attente que les esclaves prennent des tâches..."
sleep 2

# 5. Massacre total : tuer TOUS les esclaves
echo -e "\n[BASH] EXTERMINATION : tous les esclaves vont être tués (SIGKILL)...\n"

for i in {1..6}; do
    PID=${SLAVE_PIDS[$i]}
    if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" 2>/dev/null
        echo -e "[BASH] LE SLAVE $i (PID $PID) A ÉTÉ CRASHÉ BRUTALEMENT !"
    else
        echo -e "[BASH] Le Slave $i était déjà arrêté."
    fi
done

echo -e "\n[BASH] Tous les slaves ont été tués."
echo "[BASH] Le Master doit détecter la mort collective et s'arrêter proprement..."
echo "[BASH] Attente de l'arrêt du Master (max 15s)..."

# 6. Vérifier que le Master s'arrête tout seul
for sec in $(seq 1 15); do
    if ! kill -0 "$MASTER_PID" 2>/dev/null; then
        echo -e "\n[BASH] SUCCÈS : le Master (PID $MASTER_PID) s'est arrêté proprement après ~${sec}s."
        exit 0
    fi
    sleep 1
done

echo -e "\n[BASH] ÉCHEC : le Master tourne encore après 15s (PID $MASTER_PID)."
echo "[BASH] Arrêt forcé du Master pour nettoyer..."
kill -9 "$MASTER_PID" 2>/dev/null
fuser -k 18812/tcp 2>/dev/null
exit 1
