#!/bin/bash
ROOT_DIR=
if [ -z $MI_BUILD_TOP ]; then
	echo "not in build mode"
	ROOT_DIR=/usr/local/MagicInstaller
	SCRIPT_LOGGING=$ROOT_DIR/mi.logging.py
	SCRIPT_FTPD=$ROOT_DIR/mi.ftpd.py
	SCRIPT_SERVER=$ROOT_DIR/mi.server.py
else
	echo "in build mode"
	ROOT_DIR=$MI_BUILD_TOP/src/mi
	SCRIPT_LOGGING=$ROOT_DIR/mi.logging.py
	SCRIPT_FTPD=$ROOT_DIR/mi.ftpd.py
	SCRIPT_SERVER=$ROOT_DIR/mi.server.py
fi

function clean_server(){
	killall -9 $1 >/dev/null 2>&1
	for pid in `ps | grep $1 | awk '{ print $1 }'`;do
		kill -9 $pid >/dev/null 2>&1
	done
}
function clean_servers(){
	for server in mi.server.py mi.server mi.ftpd.py mi.ftpd mi.logging.py mi.logging; do
		clean_server $server
	done
}
/root/clean.sh >/dev/null 2>&1
clean_servers 
echo cd $ROOT_DIR
cd $ROOT_DIR

echo $SCRIPT_LOGGING ...
$SCRIPT_LOGGING &
pid_logger=$!

echo $SCRIPT_FTPD ...
$SCRIPT_FTPD &
pid_ftpd=$!

echo $SCRIPT_SERVER ...
$SCRIPT_SERVER &
pid_server=$!

function kill_servers(){
	kill $pid_server >/dev/null 2>&1
	kill $pid_ftpd >/dev/null 2>&1
	kill $pid_logger >/dev/null 2>&1
}
pid=
function terminate_signal(){
	echo "get terminate signal."
	echo $pid

	kill_servers

	[[ $pid ]] && kill $pid >/dev/null 2>&1
	wait $pid_server
	wait $pid_ftpd
	wait $pid_logger
	clean_servers
	exit 0
}
trap terminate_signal SIGINT SIGTERM
while true; do
	sleep 10000 & pid=$!
	wait
done

