#!/bin/bash
fuser -k 18812/tcp 2>/dev/null
python 2_master.py &
sleep 2
python 2_slave.py 1 &
python 2_slave.py 2 &
python 2_slave.py 3 &
python 2_slave.py 4 &
python 2_slave.py 5 &
python 2_slave.py 6 &