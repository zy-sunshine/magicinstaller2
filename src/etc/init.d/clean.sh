#!/bin/bash

ALL_LOOP="/dev/loop0 /dev/loop1 /dev/loop2 /dev/loop3 /dev/loop4 /dev/loop5 /dev/loop6 /dev/loop7"
function detatch_dev(){
	if [ -e $1 ]; then
		losetup -d $1 > /dev/null 2>&1
	else
		return
	fi
	if [ $? == 0 ]; then
		echo detach $1 success
	#else
	#	echo detach $1 failed
		
	fi
}
function umount_dev(){
	umount $1 > /dev/null 2>&1
	if [ $? == 0 ]; then
		echo umount $1 success
	#else
	#	echo umount $1 failed
	fi
}
function is_mountpoint(){
	mountpoint -q $1
	return $?
}

# umount all dir from loop device.
for loopdir in /tmpfs/mnt/loop3; do
	umount_dev $loopdir
done

# detach all iso file from loop device
for loop_dev in $ALL_LOOP; do
	detatch_dev $loop_dev
done

# umount mounted dir.
tmpfs_mnt_dir="/tmpfs/mnt"
if [ -d $tmpfs_mnt_dir ]; then
	for d in `ls $tmpfs_mnt_dir`; do
		umount_dev $tmpfs_mnt_dir/$d
	done
fi

function umount_each_tgtdir(){
	if [ ! -d $1 ]; then
		return
	fi
	if is_mountpoint $1; then
		umount_dev $1
	fi
}
# umount target system dir.
tgtsys_dir="/tmpfs/tgtsys"
if [ -d $tgtsys_dir ]; then
	for d in proc sys dev; do
		umount_each_tgtdir $tgtsys_dir/$d
	done
	umount_each_tgtdir $tgtsys_dir
fi
