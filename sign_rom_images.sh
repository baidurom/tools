#!/bin/bash
#**************************************************#
#
#This shell used to sign the target files and 
#pre-odex the apk or jar, generate the singed 
#system.img, and replace the key of recovery 
#	
#**************************************************#

TOOLDIR=$PORT_ROOT/tools
PROJECT=""
PRJROOT=$PWD

function usage()
{
	echo "./sign_rom_images.sh --project=a789"
	echo "                     --project: which project you want to sign"
	exit 0
}

function markpara()
{
	if [ $1 ];then
		TMP=$1
		LEFT=${TMP%%=*}
		RIGHT=${TMP##*=}
		if [ $LEFT = "--project" ];then
			PROJECT=$RIGHT
		else
			usage;
			exit 0;		
		fi
	fi
}

function getcurprjpath()
{
	if [ $1 ];then
		for DIR in $(find $PORT_ROOT -type d  -name $1)
		do
			if [ -d $DIR/other ];then
				PRJROOT=$DIR
				break
			fi
		done
	else
		if [ ! -d $PRJROOT/other ];then
			usage;
			exit 0;
		fi
	fi
}

if [ $1 ];then
   markpara $1;
else
   usage;
fi

getcurprjpath $PROJECT;

[ -d .repo ] || { echo "please run me from android root dir!"; exit 1; }

# prepare product key
KEY_DIR=baidu/security
GIT_SECURITY=http://git.scm.baidu.com:8088/git/chunlei/baidu/security.git
if [ ! -d $KEY_DIR ]; then
    git clone -b master $GIT_SECURITY $KEY_DIR
fi
[ -d $KEY_DIR/key/rom ] || { echo "failed to find rom product key!"; exit 1; }

PRODUCT_OUT=$PRJROOT/out
TARGET_FILE=$PRODUCT_OUT/target_files.zip
TARGET_FILE_ODEX=$PRODUCT_OUT/target_files.zip.odex.zip
SIGNED_TARGET_FILE=$PRODUCT_OUT/$PROJECT-target-file-signed.zip
SIGNED_ODEX_TARGET_FILE=$PRODUCT_OUT/$PROJECT-target-file-signed.zip.odex.zip
SIGNED_IMAGES=$PRODUCT_OUT/signed-images.zip
DEXOPT=$TOOLDIR/dex-opt.sh

#preodex the jar and apks
echo ">>> pre-odex signed target files  ...."
$DEXOPT --project=$PROJECT $TARGET_FILE $TARGET_FILE_ODEX

# sign target file with product key
echo ">>> sign target file '$TARGET_FILE_ODEX'...."
$TOOLDIR/releasetools/sign_target_files_apks -d $KEY_DIR/key/rom -o $TARGET_FILE_ODEX $SIGNED_TARGET_FILE
[ -f $SIGNED_TARGET_FILE ] || { echo "failed to sign target file!"; exit 2; }

# re-generate the images (including system,userdata,boot,recovery) from signed target file
echo ">>> generate signed images ...."
$TOOLDIR/releasetools/img_from_target_files $SIGNED_TARGET_FILE $SIGNED_IMAGES

# replace those images in out dir with signed images
unzip -o $SIGNED_IMAGES -d $PRODUCT_OUT
rm -f $SIGNED_IMAGES

echo ">>> Succeeded to sign product images."
