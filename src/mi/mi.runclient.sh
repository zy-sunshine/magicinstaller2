ROOT_DIR=
if [ -z $MI_BUILD_TOP ]; then
	echo "not in build mode"
	ROOT_DIR0=/usr/share/MagicInstaller
	export PYTHONPATH=$ROOT_DIR0:$PYTHONPATH
	ROOT_DIR=$ROOT_DIR0/mi
	SCRIPT_SERVER=/usr/bin/mi.runserver
	SCRIPT_CLIENT=$ROOT_DIR/mi.client.py
else
	echo "in build mode"
	ROOT_DIR=$MI_BUILD_TOP/src/mi
	SCRIPT_SERVER=$ROOT_DIR/mi.runserver.sh
	SCRIPT_CLIENT=$ROOT_DIR/mi.client.py
fi

echo $SCRIPT_CLIENT
for layout in LayoutFb LayoutVesa; do
        xinit /usr/bin/python $SCRIPT_CLIENT -- /usr/bin/X :1 -layout $layout
        pid_client=$!
        [ $? -eq 0 ] && break
done

