#!/bin/sh

# ARGS:     $1 : The target rootfs directory.
ROOT=$(echo "$1" |sed 's/\/*$//')

# We have the root directory already, 
# so we just create the directory secondary and above there.

mkdir -pv $ROOT/media/{floppy,cdrom}

mkdir -pv $ROOT/usr/{,local/}{bin,include,lib,sbin,src}
mkdir -pv $ROOT/usr/{,local/}share/{doc,info,locale,man}
mkdir -pv $ROOT/usr/{,local/}share/{misc,terminfo,zoneinfo}
mkdir -pv $ROOT/usr/{,local/}share/man/man{1..8}

mkdir -pv $ROOT/etc/opt

for dir in $ROOT/usr $ROOT/usr/local; do 
    ln -sv share/{man,doc,info} $dir 
done 

mkdir -pv $ROOT/var/{lock,log,mail,run,spool} 
mkdir -pv $ROOT/var/{opt,cache,lib/{misc,locate},local}

## Important directory and files.
# Create a simple mtab file.
ln -sv ../proc/mounts $ROOT/etc/mtab
mkdir -pv $ROOT/var/lib/xkb
mkdir -pv $ROOT/var/lock/rpm
ln -sv sbin/busybox $ROOT/init

# Remove .sconsign
find $ROOT -name .sconsign | xargs rm -f
# Remove .svn
find $ROOT -name .svn | xargs rm -f

# Make static device file.
mknod -m 600 $ROOT/dev/console c 5 1
mknod -m 666 $ROOT/dev/null c 1 3
mknod -m 666 $ROOT/dev/zero c 1 5
mknod -m 666 $ROOT/dev/tty c 5 0
for v in 0 1 2 3 4 5 6;do
    mknod -m 620 $ROOT/dev/tty$v c 4 $v
done

