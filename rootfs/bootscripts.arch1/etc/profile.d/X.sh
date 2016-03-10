if [ -x /usr/X11R6/bin/X ]; then
    pathappend /usr/X11R6/bin
fi
if [ -d /usr/X11R6/lib/pkgconfig ] ; then
    pathappend /usr/X11R6/lib/pkgconfig PKG_CONFIG_PATH
fi

