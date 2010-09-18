#!/bin/sh

### temp directory and files
touch /var/run/utmp
# Don't use the {} ,because chroot system is based on busybox.
#touch /var/log/{btmp,lastlog,wtmp}
for f in btmp lastlog wtmp;do
    touch /var/log/$f
done
chgrp -v utmp /var/run/utmp /var/log/lastlog 
chmod -v 664 /var/run/utmp /var/log/lastlog

/sbin/ldconfig
