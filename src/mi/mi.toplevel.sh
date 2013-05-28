#!/bin/bash
ROOT_DIR=
if [ -z $MI_BUILD_TOP ]; then
	echo "not in build mode"
	ROOT_DIR0=/usr/share/MagicInstaller
	export PYTHONPATH=$ROOT_DIR0:$PYTHONPATH
	ROOT_DIR=$ROOT_DIR0/mi
	SCRIPT_SERVER=/usr/bin/mi.runserver
	SCRIPT_CLIENT=$ROOT_DIR/mi.client.py
else
	echo "in build mode"
	ROOT_DIR=$MI_BUILD_TOP/src/mi
	SCRIPT_SERVER=$ROOT_DIR/mi.runserver.sh
	SCRIPT_CLIENT=$ROOT_DIR/mi.client.py
fi

function clean_server(){
	killall -9 $1 >/dev/null 2>&1
	for pid in `ps | grep $1 | awk '{ print $1 }'`;do
		kill -9 $pid >/dev/null 2>&1
	done
}
function clean_servers(){
	for server in mi.client.py mi.client mi.runserver.sh mi.runserver; do
		clean_server $server
	done
}

clean_servers 
echo cd $ROOT_DIR
cd $ROOT_DIR

echo $SCRIPT_SERVER
$SCRIPT_SERVER &
pid_server=$!
sleep 2

pid_client=

function kill_servers(){
	kill $pid_server >/dev/null 2>&1
	kill -9 $pid_client >/dev/null 2>&1
}
pid=
function terminate_signal(){
	echo "get terminate signal."
	echo $pid

	kill_servers

	[[ $pid ]] && kill $pid >/dev/null 2>&1
	wait $pid_server
	exit 0
}

trap terminate_signal SIGINT SIGTERM

echo $SCRIPT_CLIENT
for layout in LayoutFb LayoutVesa; do
	xinit /usr/bin/python $SCRIPT_CLIENT -- /usr/bin/X :1 -layout $layout
	pid_client=$!
	[ $? -eq 0 ] && break
done

kill_servers
wait $pid_server
#while true; do
#	sleep 10000 & pid=$!
#	wait
#done

