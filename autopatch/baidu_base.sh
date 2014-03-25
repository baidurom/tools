#!/bin/bash

# baidu_base.sh
#
#
# @author: duanqz@gmail.com
#

BAIDU_ZIP=$1
BAIDU_BASE=$2

DEODEX_THREAD_NUM=4
DEODEX=${PORT_ROOT}/tools/deodex.sh
APKTOOL=${PORT_ROOT}/tools/apktool
ID_TO_NAME_TOOL=${PORT_ROOT}/tools/idtoname.py

function usage()
{
	echo "baidu_base.sh BAIDU.ZIP [BAIDU_BASE]                                 "
	echo "      - BAIDU.ZIP: Zip package of baidu ROM.                         "
}


#
# De-odex baidu.zip to baidu.deodex.zip
# Parameter : baidu.zip
#
# If deodexed sucessfully, return 1; Otherwise return 0
#
function deodex_baidu_zip()
{
	local baidu_zip=$1

	local deodex_zip=${baidu_zip}.deodex.zip

	# Already de-odexed, just return
	[ -e ${deodex_zip} ] && return 1;

	# baidu_zip not exist, report error
	[ ! -e ${baidu_zip} ] && echo "ERROR: ${baidu_zip} not exists." && return 0;

	${DEODEX} ${baidu_zip} ${DEODEX_THREAD_NUM};
	[ -e ${deodex_zip} ] && return 1;

	echo ">>> ERROR: deodex ${baidu_zip} failed!"
	return 1
}



#
# Decode apk contained in DECODE_APKS to smali
#
DECODE_APKS=(Phone)
function decode_apk()
{
	local src_dir=$1
	local dst_dir=$2

	echo ">>> decoding ${DECODE_APKS[@]} ...";
	for apk in ${DECODE_APKS[*]} ; do
		${APKTOOL} d -f ${src_dir}/${apk}.apk ${dst_dir}/${apk};
	done
}



#
# Decode jar contained in DECODE_JARS to smali
#
DECODE_JARS=(framework.jar services.jar telephony-common.jar android.policy.jar \
			 secondary_framework.jar secondary-framework.jar)
function decode_jar()
{
	local src_dir=$1
	local dst_dir=$2

	echo ">>> decoding framework-res ...";
	${APKTOOL} d -f ${src_dir}/framework-res.apk ${dst_dir}/framework-res;

	local public_xml=${dst_dir}/framework-res/res/values/public.xml
	echo ">>> decoding ${DECODE_JARS[@]} ...";
	for jar in ${DECODE_JARS[*]} ; do
		if [ -e ${src_dir}/${jar} ]; then
			${APKTOOL} d -f ${src_dir}/${jar} ${dst_dir}/${jar}.out;
			${ID_TO_NAME_TOOL} ${public_xml} ${dst_dir}/${jar}.out > /dev/null;
		fi
	done
}



#
# Decode apk and jar to smali
#
function decode_baidu_source()
{
	local deodex_zip=$1
	local out=$2

	echo ">>> unzip ${deodex_zip} ...";
	[ -z ${BAIDU_BASE} ] && BAIDU_BASE=${PORT_ROOT}/reference/baidu_base
	[ ! -e ${BAIDU_BASE} ] && mkdir ${BAIDU_BASE} -p
	unzip -q -o ${deodex_zip} -d ${BAIDU_BASE};

	[ -d ${BAIDU_BASE}/SYSTEM/ ] && mv ${BAIDU_BASE}/SYSTEM/ ${BAIDU_BASE}/system/;

	decode_jar ${BAIDU_BASE}/system/framework $out;
	decode_apk ${BAIDU_BASE}/system/app $out;

}


# Combine framework partitions into framework.jar.out
PARTITIONS=(secondary_framework.jar.out secondary-framework.jar.out)
function combine_framework_partitions()
{
	local dir=$1
	for partition in ${PARTITIONS[*]} ; do
		if [ -d ${dir}/${partition} ]; then
			cp -r  ${dir}/${partition}/smali ${dir}/framework.jar.out
			rm -rf ${dir}/${partition}/smali;
		fi
	done
}


function prepare_bosp()
{
	local baidu_zip=$1
	local bosp=${PORT_ROOT}/reference/bosp

	deodex_baidu_zip ${baidu_zip};
	[ $? -gt 0 ] && decode_baidu_source ${baidu_zip}.deodex.zip ${bosp};
	combine_framework_partitions ${baidu_base}
}





### Entry ###
[ -z $1 ] && usage && exit 1

prepare_bosp $1