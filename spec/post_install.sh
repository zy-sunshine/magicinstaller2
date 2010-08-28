#!/bin/sh

rpm_run_post() {
     rpm -q --qf "%{POSTIN}" $1 > t.sh
     sh t.sh >> /var/log/post.log 2>&1
     rm t.sh
}

rpm_run_pre() {
    rpm -q --qf "%{PREIN}" $1 > t.sh
    sh t.sh >> /var/log/pre.log 2>&1
    rm t.sh
}

#通用 rpm 脚本修正
#/sbin/depmod -a  
/sbin/ldconfig

#其它 rpm 脚本修正
for i in  ncurses-libs pam rsyslog ; do
    rpm_run_pre $i || :
    rpm_run_post $i || :
done

# Fix /etc/inittab at MI Windows.py.
/bin/sed -i s/id:.:initdefault/id:5:initdefault/ /etc/inittab

#关闭不必要服务
chkconfig --level 2345 dhcpd off
chkconfig --level 2345 dhcrelay off
chkconfig --level 2345 network on
chkconfig --level 234 wine off
chkconfig --level 2345 smb off
#修正用户权限
chmod 755 /etc/X11 -R
#chmod 755 /etc/kde -R
chmod 755 /usr/{lib,include,share}
#修正CD版本自动挂载问题
/sbin/chkconfig --add haldaemon
#修正普通用户挂载问题
#/usr/sbin/useradd -u 58 -d / -s /sbin/nologin -c "Haldeamon User" -M haldaemon
groupadd plugdev
/usr/sbin/addplug
#设置默认fbsplash主题
#设置 KDM
echo "DESKTOP=KDE4" > /etc/sysconfig/desktop
echo "DISPLAYMANAGER=KDE4" >> /etc/sysconfig/desktop
echo "Thank you for using MagicInstaller!"
