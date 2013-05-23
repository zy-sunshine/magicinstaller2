# /etc/profile
# Written for Beyond Linux From Scratch
# by James Robertson <jameswrobertson@earthlink.net>
# modifications by Dagmar d'Surreal <rivyqntzne@pbzpnfg.arg>
# modifications by zy.sunshine <zy.netsec@gmail.com>

# System wide environment variables and startup programs should go into
# /etc/profile.

# System wide aliases and functions should go in /etc/bashrc. 
# Personal environment variables and startup programs should go into
# ~/.bash_profile. 
# Personal aliases and functions should go into ~/.bashrc.

if [ -f "/etc/bashrc" ] ; then
    source /etc/bashrc
fi

