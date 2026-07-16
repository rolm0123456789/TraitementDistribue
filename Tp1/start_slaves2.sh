#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f ".venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

fuser -k 18812/tcp 2>/dev/null
python 2_master.py &
sleep 2
python 2_slave.py 1 &
python 2_slave.py 2 &
python 2_slave.py 3 &
python 2_slave.py 4 &
python 2_slave.py 5 &
python 2_slave.py 6 &
