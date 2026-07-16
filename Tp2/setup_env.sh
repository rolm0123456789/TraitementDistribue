#!/bin/bash
# Configuration de l'environnement + lancement des démos du TP2 (hashage)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"

echo "=== TP2 — Hachage à grande échelle ==="
echo ""

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
echo ""
echo "Aucune dépendance externe : hashlib, bisect, collections (stdlib)."
echo ""

# 3. Permissions
chmod u+x setup_env.sh 2>/dev/null || true
chmod u+x etape*.py 2>/dev/null || true

# 4. Menu de lancement
usage() {
    cat <<'EOF'
Usage :
  bash setup_env.sh              # setup + menu interactif
  bash setup_env.sh setup        # setup uniquement (venv)
  bash setup_env.sh all          # lance les 4 démos à la suite
  bash setup_env.sh 1|2|3|4      # lance une étape
  bash setup_env.sh demo         # alias de "all"

Exemples manuels (après setup) :
  source .venv/bin/activate
  python etape1_hash_naif.py demo
  python etape2_rehash.py demo
  python etape3_anneau.py demo
  python etape4_vnodes.py demo
EOF
}

run_etape() {
    local num="$1"
    case "$num" in
        1) python etape1_hash_naif.py demo ;;
        2) python etape2_rehash.py demo ;;
        3) python etape3_anneau.py demo ;;
        4) python etape4_vnodes.py demo ;;
        *) echo "Étape inconnue : $num (1–4)"; return 1 ;;
    esac
}

run_all() {
    for i in 1 2 3 4; do
        echo ""
        echo "########## Étape $i ##########"
        echo ""
        run_etape "$i"
    done
}

ARG="${1:-}"

case "$ARG" in
    setup|--setup)
        echo "Setup terminé. Activez le venv avec : source .venv/bin/activate"
        exit 0
        ;;
    all|demo|--all|--demo)
        run_all
        exit 0
        ;;
    1|2|3|4)
        run_etape "$ARG"
        exit 0
        ;;
    -h|--help|help)
        usage
        exit 0
        ;;
    "")
        # Menu interactif
        echo "Que souhaitez-vous lancer ?"
        echo "  1) Étape 1 — Hash naïf (h % N)"
        echo "  2) Étape 2 — Rehash (N → N+1)"
        echo "  3) Étape 3 — Anneau cohérent"
        echo "  4) Étape 4 — Nœuds virtuels"
        echo "  a) Toutes les étapes"
        echo "  q) Quitter (setup seul)"
        echo ""
        read -r -p "Choix [a] : " choix
        choix="${choix:-a}"
        case "$choix" in
            1|2|3|4) run_etape "$choix" ;;
            a|A|all) run_all ;;
            q|Q) echo "Setup OK. source .venv/bin/activate" ;;
            *) echo "Choix invalide."; usage; exit 1 ;;
        esac
        ;;
    *)
        usage
        exit 1
        ;;
esac
