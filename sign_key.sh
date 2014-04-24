#!/bin/bash

# The path for keys could be set when exec sign.sh as: 
#       KEY_PATH=/path/to/key sign.sh ..
# If the path is not set, the default value is:
#       1) if PORT_ROOT is set (after running lunch), it is
#          $PORT_ROOT/porting/tools
#       2) if not running lunch, the default path is ./
if [ -z "$PORT_ROOT" ]
then
    KEYPATH=${KEY_PATH:=.}
else
    KEYPATH=${KEY_PATH:=$PORT_ROOT/tools/security}
fi

SIGNAPK=$PORT_ROOT/tools/signapk.jar
PEMKEY=$KEYPATH/testkey.x509.pem
PK8KEY=$KEYPATH/testkey.pk8

TMPDIR=.tmp_for_sign
ZIP_DIR=zipdir

function delete_meta_info() {
    zip -d $1 "META-INF/*"
}

function sign_for_phone() {
    echo ">>> Sign apks under dir $1..."
    for apk in `adb shell ls $1/*.apk | col -b`
    do
        echo ">>> Sign for $apk"
        file=`basename $apk`
        adb pull $apk $TMPDIR/$file
        delete_meta_info $TMPDIR/$file
        java -jar $SIGNAPK $PEMKEY $PK8KEY $TMPDIR/$file $TMPDIR/$file.signed
        zipalign 4 $TMPDIR/$file.signed $TMPDIR/$file.signed.aligned
        adb push $TMPDIR/$file.signed.aligned $1/$file
    done
}

function sign_for_dir() {
    echo ">>> Sign apks under dir $1..."
    for apk in `find $1 -name "*.apk"`
    do
        echo ">>> Sign for $apk"
        delete_meta_info $apk
        java -jar $SIGNAPK $PEMKEY $PK8KEY $apk $apk.signed
        zipalign 4 $apk.signed $apk.signed.aligned
        mv $apk.signed.aligned $apk
        rm $apk.signed
    done
}


if [ -z "$1" ]
then
    echo "usage: ./sign.sh keyname sign.phone          - to sign all apks for phone"
    echo "       ./sign.sh keyname sign.zip *.zip      - to sign all apks for the unzip-ed zip-file"
    echo "       ./sign.sh keyname sign.dir dir        - to sign all apks for the unzip-ed zip-file in dir"
    echo "       ./sign.sh keyname apk-file [filename] - to sign apk-file and push to phone as filename"
    exit 0
fi


if [ "$1" == "media" ];then
	PEMKEY=$KEYPATH/media.x509.pem
	PK8KEY=$KEYPATH/media.pk8
	PARAMETERA=$2
	PARAMETERB=$3
elif [ "$1" == "platform" ];then
	PEMKEY=$KEYPATH/platform.x509.pem
	PK8KEY=$KEYPATH/platform.pk8
	PARAMETERA=$2
	PARAMETERB=$3
elif [ "$1" == "shared" ];then
	PEMKEY=$KEYPATH/shared.x509.pem
	PK8KEY=$KEYPATH/shared.pk8
	PARAMETERA=$2
	PARAMETERB=$3
elif [ "$1" == "testkey" ];then
	PEMKEY=$KEYPATH/testkey.x509.pem
	PK8KEY=$KEYPATH/testkey.pk8
	PARAMETERA=$2
	PARAMETERB=$3
elif [ "$1" == "releasekey" ];then
	PEMKEY=$KEYPATH/releasekey.x509.pem
	PK8KEY=$KEYPATH/releasekey.pk8
	PARAMETERA=$2
	PARAMETERB=$3
elif [ "$1" != "" ];then
	echo "Keyname wrong! media platform shared testkey releasekey!"
	exit 0
else 
	PARAMETERA=$1
	PARAMETERB=$2
fi

if [ "$PARAMETERA" == "sign.phone" ]
then
    adb remount || { echo "Failed to remount the device"; exit 10;}
    mkdir -p $TMPDIR
    sign_for_phone "/system/app"
    sign_for_phone "/system/framework"
    rm -rf $TMPDIR
    echo Siging Complete
    exit 0
fi

if [ "$PARAMETERA" == "sign.dir" ]
then
    ZIP_DIR=$PARAMETERB
    sign_for_dir "$ZIP_DIR/system/app"
    sign_for_dir "$ZIP_DIR/system/framework"
    echo Siging Complete
    exit 0
fi

if [ "$PARAMETERA" == "sign.zip" ]
then
    if [ -d $ZIP_DIR ];
    then
	rm -rf $ZIP_DIR
    fi
    unzip -q $PARAMETERB -d $ZIP_DIR
    if [ -d "$ZIP_DIR/system" ];
    then 
	    sign_for_dir "$ZIP_DIR/system/app"
	    sign_for_dir "$ZIP_DIR/system/framework"
    else
	    sign_for_dir "$ZIP_DIR/SYSTEM/app"
	    sign_for_dir "$ZIP_DIR/SYSTEM/framework"
    fi
    echo Siging Complete
    zippath=$(cd "$(dirname "$PARAMETERB")"; pwd)
    cd $ZIP_DIR
    zip -q -r -y "$PARAMETERB.sign.zip" *
    mv $PARAMETERB.sign.zip $zippath/
    cd -
    rm -rf $ZIP_DIR
    exit 0
fi

if [ -f "$PARAMETERA" ]
then
    SIGNED=$PARAMETERA.signed
    ALIGNED=$SIGNED.aligned
    delete_meta_info $PARAMETERA
    java -jar $SIGNAPK $PEMKEY $PK8KEY $PARAMETERA $SIGNED
    zipalign 4 $SIGNED $ALIGNED
    if [ -n "$PARAMETERB" ]
    then
        adb remount || { echo "Failed to remount the device"; exit 10;}
        echo "push $ALIGNED $PARAMETERB"
        adb push $ALIGNED $PARAMETERB
        rm $SIGNED
        rm $ALIGNED
    else
        echo "The Signed file: $SIGNED"
    fi
    exit 0
else
    echo "Apk file $PARAMETERA does not exist"
    exit 1
fi
