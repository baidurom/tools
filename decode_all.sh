#!/bin/bash

#####################################################
#
#  use to decode all of the apk and jar in the system
#  note: unzip the zip first
#
#####################################################

APKTOOL="$PORT_ROOT/tools/apktool"

if [ $# -eq 0 ]
then
	echo "usage: decode_all.sh SYSTEM_DIR [OUT_DIR]"
	echo "eg: decode_all.sh system/framework"
#	file_path="."
else
	file_path=$1
fi

if [ $# -eq 1 ]
then
	out_path="."
else
	out_path=$2
fi

threadnum=4
tmp_fifofile="/tmp/$$.fifo"

mkfifo "$tmp_fifofile"
exec 6<>"$tmp_fifofile"
rm $tmp_fifofile

for ((i=0;i<$threadnum;i++));do
    echo
done >&6

find $file_path -name "*.apk" > apk_file
find $file_path -name "*.jar" > jar_file

if [ ! -d $out_path ]
then
	mkdir -p $out_path
fi

cat apk_file | while read line
do
    read -u6
    {
        echo ">>> begin decode $line"
    	out_file=${line:${#file_path}:${#line}}
    	let "len=${#out_file}-4"
    	out_file=${out_file:0:$len}
    	$APKTOOL d $line $out_path"/"$out_file
        echo "<<< decode $line done"
	echo >&6
    } &
done

wait

cat jar_file | while read line
do
    read -u6
    {
         echo ">>> begin decode $line"
         out_file=${line:${#file_path}:${#line}}
         $APKTOOL d $line $out_path"/"$out_file".out"
         echo "<<< decode $line done"
	 echo >&6
    } &

done

wait
rm apk_file
rm jar_file
