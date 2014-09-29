#!/bin/bash

# unpack_boot.sh
# Unpack the standard boot.img or recovery.img of Android
#
# @author: duanqizhi01@baidu.com(duanqz)
#

BOOTIMG=$1
OUTPUT=$2

function usage()
{
	echo "Usage unpack_boot.sh BOOTIMG [OUTPUT]"
	echo "   BOOTIMG: the file path of the boot.img to be unpack"
	echo "   OUTPUT:  the output directory. if not present, the OUT/ directory will be used"
}

function init_tools()
{
	local old_pwd=`pwd`
	TOOL_DIR=`cd $(dirname $0); pwd`
	ABOOTIMG=$TOOL_DIR/abootimg
	UNPACK_INITRD=$TOOL_DIR/abootimg-unpack-initrd
	cd $old_pwd
}

function unpack_bootimg()
{
	local old_pwd=`pwd`
	mkdir -p $OUTPUT
	cp $BOOTIMG $OUTPUT/boot.img
	cd $OUTPUT

	# Open the macro variable to filter " *** glibc detected *** " error
	# local tmp_stderr=$LIBC_FATAL_STDERR_
	# export LIBC_FATAL_STDERR_=1

	# Unpack boot image
	$ABOOTIMG -x boot.img
	$UNPACK_INITRD
	rm -rf boot.img

	# export LIBC_FATAL_STDERR_=$tmp_stderr
	cd $old_pwd
}

### Start Script ###

# Check parameters
[ $# -eq 0 ] && usage && exit 1;
[ -z $2 ] && OUTPUT="OUT/";

init_tools;
unpack_bootimg;
