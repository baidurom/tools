#!/bin/bash

PRJROOT=$PWD
ROM=$PORT_ROOT/baidu/rom
LISTPATH=$ROM
SOURCEOTA=$ROM/ota/baidu_update.zip
SOURCEOTAIMG=$ROM/ota/system.img
DEVICEINFO=$PORT_ROOT/devices/deviceinfo/deviceinfo.txt
GIT_DEVICE=http://git.scm.baidu.com:8088/git/chunlei/smali/devices

#tools shell
TOOLDIR=$PORT_ROOT/tools
APKTOOL=$TOOLDIR/apktool
DIFFLIST=$LISTPATH/diff.list
GETPACKAGE=$TOOLDIR/getpackage.sh
SIM2IMG=$TOOLDIR/simg2img
ID2NAME=$TOOLDIR/idtoname.py
RMLINE=$TOOLDIR/rmline.sh
FIX_PLURALS=$TOOLDIR/fix_plurals.sh

#project 
PRJOUT=$PRJROOT/out
OTHER_DIR=$PRJROOT/other
ORIGINOTA=$PRJROOT/origin_zip/origin_image.zip
OEMOTAROM=$PRJROOT/oemotarom.zip
FRAMEWORK_RES=$PRJROOT/framework-res
FRAMEWORK_JAR_OUT=$PRJROOT/framework.jar.out
SERVICES_JAR_OUT=$PRJROOT/services.jar.out
SECONDARY_FRAMEWORK_JAR_OUT=$PRJROOT/secondary_framework.jar.out
SOURCEOTADIR=$PRJROOT/source
SERVERDIR=""
PUBLIC_MASTER=$OTHER_DIR/public_master.xml
MERGE_LIST=$PRJOUT/merge.list

#other and target
OTHERDIR=$PRJROOT/other
SAVED_OEM_TARGET_DIR=$OTHERDIR/oem_target_files

function usage()
{
    echo "$0 --serverdir=XXX --reference=XXX"
    echo "    --serverdir: serverdir you want to get source package"
    echo "    --reference: reference project for automerge: for example: a789, v889m."
    echo "$0 --help to show this information."
}

# directly copy replace and new file
function pre_merge()
{
    if [ ! -d $PRJOUT ];then
        mkdir -p $PRJOUT
    fi

    copylist=$PRJOUT/copy.list
    if [ -f $copylist ];then
        rm -f $copylist
    fi
    if [ -f $MERGE_LIST ];then
        rm -f $MERGE_LIST
    fi

    sed -n '/^replace/p' $DIFFLIST | awk '{print $2}' > $copylist
    sed -n '/^new/p' $DIFFLIST | awk '{print $2}' >> $copylist
    sed -n '/^merge/p' $DIFFLIST | awk '{print $2}' >> $MERGE_LIST
    
    while read line
    do
        echo "copying $SOURCEOTADIR/$line "
        cp $SOURCEOTADIR/$line $PRJROOT/`dirname $line##abcde`
    done < $copylist
    rm -f $copylist
    echo "premerge done!"
}

function getnewpackage()
{
    if [ "$1" != "" ];then
        $GETPACKAGE $1
    else
        echo "The remote OTA dir is NULL!!!"
    fi
}

function prepare_source()
{
    if [ "$SERVERDIR" != "" ];then
        getnewpackage $SERVERDIR 1>/dev/null;
    fi

    cp $ROM/ota/public_master.xml $PUBLIC_MASTER
    if [ -f $SOURCEOTA ];then
        echo "Prepare source files..."
        if [ -d $SOURCEOTADIR ];
        then
            rm -rf $SOURCEOTADIR
        fi
        mkdir -p $SOURCEOTADIR
        unzip -q $SOURCEOTA -d $SOURCEOTADIR
        if [ -d $SOURCEOTADIR/SYSTEM ];then
            mv $SOURCEOTADIR/SYSTEM $SOURCEOTADIR/system
        fi
    elif [ -f $SOURCEOTAIMG ];then
        $SIM2IMG $SOURCEOTAIMG system.img
        if [ -d $SOURCEOTADIR ];
        then
            rm -rf $SOURCEOTADIR
        fi
        mkdir -p $SOURCEOTADIR
        mount -t ext4 -o loop system.img ./source
    else
        echo "$SOURCEOTA not exist! please get the latest master ota package!"
        exit 0
    fi


    cd $SOURCEOTADIR
    $APKTOOL if $SOURCEOTADIR/system/framework/framework-res.apk
    for i in framework-res.apk framework.jar services.jar secondary_framework.jar
    do
        echo "processing $i "
        $APKTOOL d $SOURCEOTADIR/system/framework/$i
        if [ "$i" != framework-res.apk ];then
            $ID2NAME $PUBLIC_MASTER $SOURCEOTADIR/$i.out >> /dev/null
        fi
    done
    cd -
    echo ">>> prepare source done!"
}

function prepare_origin_smali_dir()
{
    echo ">>> prepare smali directories..."
    originPackage=$1/$out/origin_pacakge

    if [ -d $originPackage ];then
        rm -rf $originPackage
    fi
    mkdir -p $originPackage
    unzip -q $1/origin_zip/origin_image.zip -d $originPackage
    cd $1/origin_zip
    for i in framework-res.apk framework.jar services.jar secondary_framework.jar
    do
        echo "processing $i "
        $APKTOOL d -f $originPackage/system/framework/$i
        if [ "$i" != "framework-res.apk" ];then
            $RMLINE $i.out
        fi
    done
    rm -rf $originPackage
    cd -
    echo ">>> prepare smali directories done!"
}

function clear_origin_dir()
{
    for i in framework-res framework.jar.out services.jar.out secondary_framework.jar.out
    do
        if [ -d $1/origin_zip/$i ];then
            rm -rf $1/origin_zip/$i
        fi
    done
}

function ref_merge()
{
    srcDir=$1/origin_zip
    destDir=$2/origin_zip
    srcCopyDir=$1
    destCopyDir=$2
    copyList=$PRJOUT/copy.list

    if [ -f $MERGE_LIST.tmp ];then
        rm -f $MERGE_LIST.tmp
    fi
    if [ -f $copyList ];then
        rm -f $copyList
    fi

    while read line
    do
        diff -q $srcDir/$line $destDir/$line
        if [ $? != 0 ];then
            echo "$line" >> $MERGE_LIST.tmp
        else
            echo "$line" >> $copyList
        fi
    done < $MERGE_LIST
        echo "wtf!"

    if [ -f $copyList ];then
        while read line
        do
            echo "copying $srcCopyDir/$line "
            cp $srcCopyDir/$line $destCopyDir/`dirname $line##abcde`
        done < $copyList
        rm -f $copyList
    fi
    
    if [ -f $MERGE_LIST.tmp ];then
        mv $MERGE_LIST.tmp $MERGE_LIST
    fi
}

if [ $# = 0 ];then
    usage
    exit 0;
fi

# Iterate over the arguments looking for options.
while true; do
    origOption="$1"

    if [ "x${origOption}" = "x--" ]; then
        # A raw "--" signals the end of option processing.
        shift
        break
    fi

    # Parse the option into components.
    optionBeforeValue=`expr -- "${origOption}" : '--\([^=]*\)='`

    if [ "$?" = '0' ]; then
        # Option has the form "--option=value".
        option="${optionBeforeValue}"
        value=`expr -- "${origOption}" : '--[^=]*=\(.*\)'`
        hasValue='yes'
    else
        option=`expr -- "${origOption}" : '--\(.*\)'`
        if [ "$?" = '1' ]; then
            # Not an option.
            break
        fi
        # Option has the form "--option".
        value=""
        hasValue='no'
    fi
    shift

    # Interpret the option
    if [ "${option}" = 'serverdir' -a "${hasValue}" = 'yes' ]; then
        SERVERDIR="${value}"
    elif [ "${option}" = 'reference' -a "${hasValue}" = 'yes' ]; then
        REFERENCE=$value
    elif [ "${option}" = 'help' -a "${hasValue}" = 'no' ]; then
        usage;
        exit 0;
    else
        echo "unknown option: ${origOption}" 1>&2
        bogus='yes'
        usage;
        exit 0;
    fi
done

echo "fix plurals.xml...."
if [ -x $FIX_PLURALS ];then
$FIX_PLURALS framework-res
fi
prepare_source
pre_merge

if [ -n "$REFERENCE" ];then
    cat $DEVICEINFO | awk '{print $3}' | grep -s -w $REFERENCE
    if [ $? != 0 ];then
        echo "reference project $REFERENCE is not exist!"
        usage
        exit 0;
    fi
    platform=$(cat $DEVICEINFO | grep -s -w $REFERENCE | awk '{print $2}')
    if [ "$platform" = "rom-mtk" ];then
        platform=mtk
    elif [ "$platform" = "rom-qualcomm" ];then
        platform=qualcomm
    fi
    refProjectRoot=$PRJOUT/$REFERENCE-reference
    if [ -d $refProjectRoot ];then
        rm -rf $refProjectRoot
    fi
    mkdir -p $refProjectRoot
    git clone -b smali $GIT_DEVICE/$platform/$REFERENCE.git  $refProjectRoot
    if [ $? != 0 ];then
        echo "Retrive reference project fail."
        exit 0;
    fi

    prepare_origin_smali_dir $PRJROOT
    prepare_origin_smali_dir $refProjectRoot
    ref_merge  $refProjectRoot $PRJROOT
    rm -rf $refProjectRoot
    clear_origin_dir $PRJROOT
fi


