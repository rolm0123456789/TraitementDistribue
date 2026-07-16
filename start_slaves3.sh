#!/bin/bash
fuser -k 18812/tcp 2>/dev/null
# 1. Lancement du Master en arrière-plan
python 2_master.py &
sleep 2

# 2. Lancement du Slave 1 et capture immédiate de son PID
python 2_slave.py 1 &
SLAVE_1_PID=$!

# 3. Lancement des autres Slaves
python 2_slave.py 2 &
python 2_slave.py 3 &
python 2_slave.py 4 &
python 2_slave.py 5 &
python 2_slave.py 6 &

# 4. Attente active d'une seconde puis crash provoqué du Slave 1
sleep 1
kill -9 $SLAVE_1_PID
echo -e "\n[BASH] LE SLAVE 1 A ÉTÉ CRASHÉ BRUTALEMENT (SIGKILL) !\n"