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

append () {
    # First remove the directory
    local IFS=':'
    local NEWPATH
    for DIR in $PATH; do
        if [ "$DIR" != "$1" ]; then
            NEWPATH=${NEWPATH:+$NEWPATH:}$DIR
        fi
    done
    
    # Then append the directory
    export PATH=$NEWPATH:$1
}

if [ -f "$HOME/.bashrc" ] ; then
    source $HOME/.bashrc
fi

if [ -d "$HOME/bin" ] ; then
    append $HOME/bin
fi

unset append

