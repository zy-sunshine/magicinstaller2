#!/bin/bash

root=$(dirname $0)
source $root/function.sh

initrd_path="$ckdir/$name"_initrd
if [ ! -d $initrd_path ]; then
    runbash "mkdir -p $initrd_path"
else
    runbash "rm -rf $initrd_path"
    runbash "mkdir -p $initrd_path"
fi

rootfs=$ckdir/$name/boot/mirootfs.gz
if [ -f $rootfs ]; then
    runbash "gunzip -c $rootfs > $initrd_path/mirootfs"
    runbash "cd $initrd_path"
    runbash "cpio -di < mirootfs"
    runbash "cd -"
fi
echo $initrd_path
