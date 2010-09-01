#!/bin/sh

export DISPLAY="devhost:0"
export PYTHONPATH=$PWD

touch /tmpfs/debug/start.step.2

python magic.actions.server.py &
sleep 1
if [ -n "$1" ] ; then
    python $1
else
    python magic.installer.py
fi
python magic.actions.quit.py
