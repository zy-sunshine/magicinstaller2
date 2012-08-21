#!/bin/sh

root=$(dirname $0)
source $root/function.sh

if [ ! -d $ckdir/$name ];then
    runbash "mkdir -p $ckdir/$name"
else
    if [[ `mountpoint $ckdir/$name` =~ "is a mountpoint" ]]; then
        echo "$ckdir/$name is a mountpoint"
        runbash "sudo umount $ckdir/$name"
        runbash "rmdir $ckdir/$name"
    elif [[ `mountpoint $ckdir/$name` =~ "is not a mountpoint" ]]; then
        echo "$ckdir/$name is not a mountpoint"
        runbash "rmdir $ckdir/$name"
    else
        echo "check mountpoint of $ckdir/$name failed !!"
        exit -1
    fi
    runbash "mkdir -p $ckdir/$name"
fi

runbash "sudo mount -o loop result/$name.iso $ckdir/$name"

