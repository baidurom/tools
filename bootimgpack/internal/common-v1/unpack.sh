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
	[ $? != 0 ] && exit 1

	$UNPACK_INITRD
	[ $? != 0 ] && exit 1

	rm -rf boot.img

	# Remove the bootsize
	mv bootimg.cfg bootimg.cfg~
	sed {1d} bootimg.cfg~ > bootimg.cfg

	# export LIBC_FATAL_STDERR_=$tmp_stderr
	cd $old_pwd
}

function check_result()
{
	[ ! -e $OUTPUT/zImage ] && exit 1
	[ ! -e $OUTPUT/RAMDISK/init.rc ] && exit 1
}


### Start Script ###

# Check parameters
[ $# -eq 0 ] && usage && exit 1;
[ -z $2 ] && OUTPUT="OUT/";

init_tools;
unpack_bootimg;
check_result;
exit 0