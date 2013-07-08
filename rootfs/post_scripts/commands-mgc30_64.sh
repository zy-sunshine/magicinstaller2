#!/bin/sh

# ARGS:     $1 : The target rootfs directory.
# Remove the backslash at the end of ROOT.
ROOT=$(echo "$1" |sed 's/\/*$//')

if [ -e $ROOT/etc/X11/xorg.conf ]; then
    rm $ROOT/etc/X11/xorg.conf
fi
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
# Create a mtab file.
touch $ROOT/etc/mtab
mkdir -pv $ROOT/var/lib/xkb
mkdir -pv $ROOT/var/lock/rpm
ln -sv usr/lib/systemd/systemd $ROOT/init

# Remove .sconsign
find $ROOT -name .sconsign | xargs rm -frv
# Remove .svn
find $ROOT -name .svn | xargs rm -frv

# Make static device file.
if [ ! -d $ROOT/dev ]; then
    mkdir -pv $ROOT/dev
fi
mknod -m 600 $ROOT/dev/console c 5 1
mknod -m 666 $ROOT/dev/null c 1 3
mknod -m 666 $ROOT/dev/zero c 1 5
mknod -m 666 $ROOT/dev/tty c 5 0
for v in 0 1 2 3 4 5 6;do
    mknod -m 620 $ROOT/dev/tty$v c 4 $v
done

# For static device nodes to /dev
static_dev=$ROOT/lib/udev/devices
mkdir -pv $static_dev
ln -sv /proc/kcore $static_dev/core
ln -sv /proc/self/fd $static_dev/fd
ln -sv /proc/self/fd/2 $static_dev/stderr
ln -sv /proc/self/fd/0 $static_dev/stdin
ln -sv /proc/self/fd/1 $static_dev/stdout
install -dv -m 755 $static_dev/shm
install -dv -m 755 $static_dev/pts
mknod -m 600 $static_dev/mixer c 14 0
#
mknod -m 600 $static_dev/console c 5 1
mknod -m 666 $static_dev/null c 1 3
mknod -m 666 $static_dev/zero c 1 5

# check all the file to root privilege.
chown -R root:root $ROOT/*

# If will create a directory or file, do it like this better.
#install --directory --mode=0755 --owner=root --group=root /etc/profile.d

# Create some neccessary shortcut
if [ ! -d $ROOT/bin ]; then
    mkdir -pv $ROOT/bin
fi
for cmd in \
addgroup  date           fgrep     linux64     mv         rmdir         true \
adduser   dd             fsync     ln          netstat    scriptreplay  umount \
ash       delgroup       getopt    login       nice       sed           uname \
bash      deluser        grep      ls          pidof      setarch       vi \
busybox   df             gunzip    lzop        ping       sh            zcat \
cat       dmesg          gzip      makemime    printenv   sleep \
chgrp     dnsdomainname  hostname  mkdir       ps         stat \
chmod     dumpkmap       ionice    mknod       pwd        stty \
chown     echo           ip        more        reformime  sync \
cp        egrep          kill      mount       rev        tar \
cpio      false          linux32   mountpoint  rm         touch \
    ; do
    if [ ! -f $ROOT/bin/$cmd ]; then
        ln -s ../../usr/sbin/busybox $ROOT/bin/$cmd
    fi
done

if [ ! -d $ROOT/usr/bin ]; then
    mkdir -pv $ROOT/usr/bin
fi
for cmd in \
[         dumpleases  install   nc         rtcwake    tftp        volname \
[[        eject       kbd_mode  nohup      script     tftpd       wall \
arping    env         killall   nslookup   seq        time        wc \
awk       expand      last      od         setsid     timeout     wget \
basename  expr        less      openvt     sha256sum  top         which \
beep      fgconsole   logger    passwd     sha512sum  tr          who \
bunzip2   find        lpq       patch      showkey    traceroute  whoami \
bzcat     flock       lpr       pgrep      smemcap    tty         xargs \
bzip2     free        lspci     pkill      sort       ttysize     xz \
chat      ftpget      lsusb     printf     split      udpsvd      xzcat \
chvt      ftpput      lzcat     pscan      sum        unexpand    yes \
clear     fuser       lzma      readahead  tac        uniq \
cmp       hd          lzopcat   readlink   tail       unlzma \
cut       head        md5sum    realpath   tcpsvd     unlzop \
diff      hexdump     mesg      reset      tee        unxz \
dirname   id          microcom  resize     telnet     unzip \
du        ifplugd     mkfifo    rpm2cpio   test       uptime \
    ; do
    if [ ! -f $ROOT/usr/bin/$cmd ]; then
        ln -s ../../usr/sbin/busybox $ROOT/usr/bin/$cmd
    fi
done


if [ ! -d $ROOT/usr/sbin ]; then
    mkdir -pv $ROOT/usr/sbin
fi
for cmd in \
brctl     dhcprelay  inetd     ntpd        readprofile  telnetd \
chpasswd  dnsd       loadfont  popmaildir  sendmail     udhcpd \
chroot    ftpd       lpd       rdev        setfont \
    ; do
    if [ ! -f $ROOT/usr/sbin/$cmd ]; then
        ln -s busybox $ROOT/usr/sbin/$cmd
    fi
done

if [ ! -d $ROOT/sbin ]; then
    mkdir -pv $ROOT/sbin
fi
for cmd in \
cpid       findfs        init      mkdosfs      pivot_root  swapon \
arp         freeramdisk  insmod    mke2fs       poweroff    switch_root \
blkid       getty        klogd     mkfs.ext2    reboot      sysctl \
bootchartd  halt         loadkmap  mkfs.reiser  rmmod       syslogd \
depmod      hdparm       losetup   mkfs.vfat    route       tunctl \
devmem      hwclock      lsmod     mkswap       setconsole  udhcpc \
fbsplash    ifconfig     man       modinfo      slattach \
fdisk       ifenslave    mdev      modprobe     swapoff \
    ; do
    if [ ! -f $ROOT/sbin/$cmd ]; then
        ln -s ../usr/sbin/busybox $ROOT/sbin/$cmd
    fi
done
