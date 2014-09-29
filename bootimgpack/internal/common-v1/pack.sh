#!/bin/bash

# pack_boot.sh
# Pack the directory to boot.img

BOOTDIR=$1
OUTPUT=$2

function usage()
{
	echo "Usage pack_boot.sh BOOTDIR [OUTPUT]"
	echo "   BOOTDIR: the directory containing boot files to be pack"
	echo "   OUTPUT:  the output directory. if not present, the out.img will be used"
}

function init_tools()
{
	local old_pwd=`pwd`
	TOOL_DIR=`cd $(dirname $0); pwd`
	ABOOTIMG=$TOOL_DIR/abootimg
	PACK_INITRD=$TOOL_DIR/abootimg-pack-initrd
	cd $old_pwd
}

function pack_bootimg()
{
	local old_pwd=`pwd`

	cd $BOOTDIR
	$PACK_INITRD newinitrd.img
	if [ -e secondstage ]; then
		$ABOOTIMG --create out.img -f bootimg.cfg -k zImage -r newinitrd.img -s secondstage
	else
		$ABOOTIMG --create out.img -f bootimg.cfg -k zImage -r newinitrd.img
	fi

	cd $old_pwd
	mv $BOOTDIR/out.img $OUTPUT
}

# Check parameters
[ $# -eq 0 ] && usage && exit 1;
[ -z $2 ] && OUTPUT=out.img;

init_tools;
pack_bootimg;
