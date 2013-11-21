#!/bin/bash

TOOL_PATH=$PORT_ROOT/tools
SMALI=$TOOL_PATH/smali
BAKSMALI=$TOOL_PATH/baksmali

function deodex_one_file() {
    local outdir=`mktemp -d /tmp/baksamli.out.XXXXX`
    local class_dex='classes.dex'

    if [ "$1" = '-a' ]
    then
        apilevel=$2
        classpath=$3
        file=$4
        tofile=${file/odex/$5} 
        echo ">>> processing $tofile"
        $BAKSMALI -a $apilevel -c $classpath -d framework -I -x $file -o $outdir/out || return 2
    else
        classpath=$1
        file=$2
        tofile=${file/odex/$3}
        echo "<<< processing $tofile"
        $BAKSMALI -c $classpath -d framework -I -x $file -o $outdir/out || return 2
    fi
	
    tofileFullPath=$PWD/$tofile
    pre_dir=$PWD
    cd $outdir
    $SMALI out -o "$class_dex" || return 2
    
    if [ -f $tofileFullPath ];then
        jar uf $tofileFullPath "$class_dex" || return 2
    else
        jar cf $tofileFullPath "$class_dex" || return 2
    fi

    cd "$pre_dir"
    rm -rf $outdir
    rm $file
    zipalign 4 $tofile $tofile.aligned || return 2
    mv $tofile.aligned $tofile
    echo ">>> deodex $tofile done"
    return 0
}

#usage
if [ "$1" = "--help" -o "$#" -lt "1" ];then
    echo "usage: ./deodex.sh [-a APILevel] absolute_path_to_ota_zip_file -jn"
    echo "  -a    specify APILevel, default Level is 15"
    echo "  -jn   n is the thread num"
    exit 0
fi    

if [ ! -x $BAKSMALI -o ! -x $SMALI ];then
     echo "Error: Can not find baksmali/smali"
     exit -1
fi

if [ "$1" = "-a" ]
then 
    apilevel=$2
    stockzip=$3
    threadnum=${4#-j}
else
    stockzip=$1
    threadnum=${2#-j}
fi

if [ "x$threadnum" = "x" ];then
    threadnum=4
fi

zippath=$(cd "$(dirname "$stockzip")"; pwd)
zipname=$(basename "$stockzip")
deodexfile="$zippath/$zipname.deodex.zip"

tempdir=`mktemp -d /tmp/tempdir.XXXXX`
echo "temp dir: $tempdir"
echo "unzip $stockzip to $tempdir"
unzip -q -o $stockzip -d $tempdir

if [ -d $tempdir/system ]
then
    cd $tempdir/system
elif [ -d $tempdir/SYSTEM ]
then
    cd $tempdir/SYSTEM
else
    echo "can't find system or SYSTEM dir in $tempdir"
    exit -1
fi

if [ ! -f framework/core.odex ];then
    cd -
    rm -rf $tempdir
    echo ">>> $stockzip isnot odex! "
    cp $stockzip $deodexfile
    exit 0
fi

tmp_fifofile="/tmp/$$.fifo"
mkfifo "$tmp_fifofile"
exec 6<>"$tmp_fifofile"
rm $tmp_fifofile

for ((i=0;i<$threadnum;i++));do
    echo
done >&6

ls framework/core.odex > /dev/null
if [ $? -eq 0 ] 
then
    if [ $1 = '-a' ]
    then
        deodex_one_file -a $apilevel "" framework/core.odex jar
    else
        deodex_one_file "" framework/core.odex jar
    fi
fi

for f in framework/*.jar
do
    classpath=$classpath:$f
done

echo "classpath=$classpath"

ls framework/*.odex > /dev/null
if [ $? -eq 0 ]
then
    for file in framework/*.odex
    do
        read -u6
        {
            deodex_out=`mktemp /tmp/deodex_out.XXXXX`
            if [ $1 = '-a' ]
            then
                deodex_one_file -a $apilevel $classpath $file jar 2>&1 | tee $deodex_out
            else
                deodex_one_file $classpath $file jar 2>&1 | tee $deodex_out
            fi
	    deodex_result="$?"
	    hasError=`egrep "Error|Exception" -i $deodex_out`
	    rm $deodex_out -rf
            if [ $deodex_result != "0" -o "x$hasError" != "x" ];then
		    echo ">>> ERROR: deodex $file fail"
		    father_pid=`ps -e | grep "deodex.sh" | awk '{print $1}'`
		    if [ "x$father_pid" != "x" ];then
			    kill -9 $father_pid 
		    fi
		    exit -2
            fi
            echo >&6
        } &
    done
fi

echo ">>> wait for framework deodex done!"
wait
echo ">>> framework deodex done! $?"

ls app/*.odex > /dev/null
if [ $? -eq 0 ]
then
    for file in app/*.odex
    do
        read -u6
        {
            if [ $1 = '-a' ]
            then
                deodex_one_file -a $apilevel $classpath $file apk || exit $?
            else
                deodex_one_file $classpath $file apk || exit $?
            fi
            echo >&6
        } &
    done
fi
echo ">>> wait for app deodex done!"
wait
echo ">>> app deodex done! $?"

cd $tempdir
echo "zip tmp_target_files"
zip -q -r -y "tmp_target_files" *
mv  "tmp_target_files.zip" $deodexfile
cd -
rm -rf $tempdir
echo "deodex done. deodex zip: $stockzip"
