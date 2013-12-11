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
	UNPACKBOOTIMG=$TOOL_DIR/unpackbootimg
	UNPACKBOOTIMGPL=$TOOL_DIR/unpack-bootimg.pl
	cd $old_pwd
}

function unpack_bootimg()
{
	local old_pwd=`pwd`
	cp $BOOTIMG $TOOL_DIR/boot.img
	cd $TOOL_DIR

	# Open the macro variable to filter " *** glibc detected *** " error
	local tmp_stderr=$LIBC_FATAL_STDERR_
	export LIBC_FATAL_STDERR_=1

	# Unpack boot image
	$UNPACKBOOTIMG -i boot.img -o ./
	$UNPACKBOOTIMGPL boot.img

	export LIBC_FATAL_STDERR_=$tmp_stderr
	cd $old_pwd
}

function handle_output()
{
	mkdir $OUTPUT -p
	cp $TOOL_DIR/boot.img-ramdisk   $OUTPUT/RAMDISK -r
	cp $TOOL_DIR/boot.img-zImage    $OUTPUT/kernel
	cp $TOOL_DIR/boot.img-cmdline   $OUTPUT/cmdline
	cp $TOOL_DIR/boot.img-base      $OUTPUT/base
	cp $TOOL_DIR/boot.img-pagesize  $OUTPUT/pagesize
	rm -rf $TOOL_DIR/boot.img*
}

### Start Script ###

# Check parameters
[ $# -eq 0 ] && usage && exit 1;
[ -z $2 ] && OUTPUT="OUT/";

init_tools;
unpack_bootimg;
handle_output;