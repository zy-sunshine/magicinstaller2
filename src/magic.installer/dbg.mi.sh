#!/bin/sh

#export DISPLAY="devhost:1"
export PYTHONPATH=$PWD

python ../etc/init.d/cleanenv.py
mkdir -p /tmpfs/debug
touch /tmpfs/debug/start.step.2

python magic.actions.server.py & 2>&1 | more > /var/log/dbg.magic.actions.server.log
actionid=$!
sleep 1
if [ -n "$1" ] ; then
    python $1
else
    python magic.installer.py
fi
python magic.actions.quit.py
kill $actionid
