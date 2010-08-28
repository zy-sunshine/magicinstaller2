for var in `ls ../*xml`;do echo $var && perl each_pkg_ver_ch.pl $var > `basename $var`;done
