#!/bin/bash
ROOT_DIR=
if [ -n $MI_BUILD_TOP ]; then
	echo "not in build mode"
	ROOT_DIR=/usr/local/MagicInstaller
else
	ROOT_DIR=$MI_BUILD_TOP/src/mi
fi
ROOT_DIR=/home/netsec/work/mi2/src/mi
function clean_server(){
	busybox killall -9 $1 >/dev/null 2>&1
	for pid in `busybox ps | grep $1 | busybox awk '{ print $1 }'`;do
		busybox kill -9 $pid >/dev/null 2>&1
	done
}
function clean_servers(){
	for server in mi.server.py mi.ftpd.py mi.logging.py; do
		clean_server $server
	done
}
/root/cleanenv.py >/dev/null 2>&1
clean_servers 
echo cd $ROOT_DIR
cd $ROOT_DIR

./mi.logging.py &
pid_logger=$!
./mi.ftpd.py &
pid_ftpd=$!
./mi.server.py &
pid_server=$!

function kill_servers(){
	busybox kill -9 $pid_server >/dev/null 2>&1
	busybox kill -9 $pid_ftpd >/dev/null 2>&1
	busybox kill -9 $pid_logger >/dev/null 2>&1
}
pid=
function terminate_signal(){
	echo "get terminate signal."
	echo $pid

	kill_servers

	[[ $pid ]] && busybox kill $pid >/dev/null 2>&1
	wait $pid_server
	wait $pid_ftpd
	wait $pid_logger
	exit 0
}
trap terminate_signal INT
while true; do
	sleep 10000 & pid=$!
	wait
done

