#!/bin/bash

TOOLDIR=$PORT_ROOT/tools
MKBOOTFS=$TOOLDIR/mkbootfs
MKIMAGE=$TOOLDIR/mkimage
$MKBOOTFS $1 | minigzip > ramdisk.img
