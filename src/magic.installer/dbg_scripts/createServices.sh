tar xvf ../../../bindir/root_ext/busybox-1.17.2.bin.tar.bz2
cp bin/busybox /bin/busybox
cp usr/bin/tftpd /usr/bin/tftpd
cp usr/sbin/inetd /usr/sbin/inetd

cp ../../etc/init.d/inetd.conf /etc/inetd.conf

inetd
