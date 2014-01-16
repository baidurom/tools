#!/bin/bash

# predication.sh
#
# Predications of auto patch:
# Baidu smali files should be decoded firstly.
#
# @Parameter 1: baidu direcotry. e.g.: ~/coron/devices/maguro/baidu/
#
# @author: duanqizhi01@baidu.com(duanqz)
#

BAIDU_DIR=$1
BAIDU_ZIP=${BAIDU_DIR}/baidu.zip
BAIDU_BASE_ZIP=${BAIDU_DIR}/baidu.deodex.zip

BAIDU_FRAMEWORK_DIR=${BAIDU_DIR}/system/framework
BAIDU_SMALI_DIR=${BAIDU_DIR}/smali
BAIDU_PUBLIC_XML=${BAIDU_SMALI_DIR}/framework-res/res/values/public.xml

DEODEX_THREAD_NUM=4
DEODEX=${PORT_ROOT}/tools/deodex.sh
APKTOOL=${PORT_ROOT}/tools/apktool
ID_TO_NAME_TOOL=${PORT_ROOT}/tools/idtoname.py


function usage()
{
	echo "predication.sh BAIDU_DIR";
	echo "  e.g.: predication.sh ~/coron/devices/maguro/baidu/";
}

function check_file_exist()
{
	if [ -e ${1} ]; then
		return 1;
	else
		# File not exists
		return 0;
	fi
}

#
# De-odex baidu.zip to baidu.deodex.zip
#
function deodex_baidu_zip()
{
	check_file_exist ${BAIDU_BASE_ZIP};
	if [ $? -eq 0 ]; then
		check_file_exist ${BAIDU_ZIP};
		if [ $? -eq 0 ]; then
			echo "ERROR: ${BAIDU_ZIP} not exists.";
		else
			echo ">>> Deodex ${BAIDU_ZIP} ..."
			${DEODEX} ${BAIDU_ZIP} ${DEODEX_THREAD_NUM};
			if [ -e ${BAIDU_ZIP}.deodex.zip ];then 
				mv ${BAIDU_ZIP}.deodex.zip ${BAIDU_BASE_ZIP};
			else
				echo ">>> ERROR: deodex ${BAIDU_ZIP} failed!";
			fi
		fi
	fi
}

#
# Decode apk contained in BAIDU_APKS to smali
#
BAIDU_APKS=(framework-res) 
function decode_apk()
{
	echo ">>> decoding ${BAIDU_APKS[@]} ...";
	for apk in ${BAIDU_APKS[*]} ; do
		${APKTOOL} d -f ${BAIDU_FRAMEWORK_DIR}/${apk}.apk ${BAIDU_SMALI_DIR}/${apk};
	done
}

#
# Decode jar contained in BAIDU_JARS to smali
#
BAIDU_JARS=(framework.jar services.jar telephony-common.jar secondary_framework.jar)
function decode_jar()
{
	echo ">>> decoding ${BAIDU_JARS[@]} ...";
	for jar in ${BAIDU_JARS[*]} ; do
		check_file_exist ${BAIDU_FRAMEWORK_DIR}/${jar}
		if [ $? -gt 0 ]; then
			${APKTOOL} d -f ${BAIDU_FRAMEWORK_DIR}/${jar} ${BAIDU_SMALI_DIR}/${jar}.out;
			${ID_TO_NAME_TOOL} ${BAIDU_PUBLIC_XML} ${BAIDU_SMALI_DIR}/${jar}.out > /dev/null;
		fi
	done
}

#
# Decode apk and jar to smali
#
function decode_baidu_source()
{
	if [ ! -d ${BAIDU_FRAMEWORK_DIR} ]; then
		unzip -q -o ${BAIDU_BASE_ZIP} -d ${BAIDU_DIR};
	fi

	decode_apk;
	decode_jar;
}

#
# Prepare the baidu smali source for auto patching.
# Firstly, de-odex the baidu.zip
# Secondly, decode the necessary apk and jar to smali
#
function prepare_baidu_smali_source()
{

	if [ -d ${BAIDU_DIR}/SYSTEM/ ]; then
		mv ${BAIDU_DIR}/SYSTEM/ ${BAIDU_DIR}/system/
	fi

	if [ -d ${BAIDU_SMALI_DIR} ]; then
		exit 0;
	fi

	deodex_baidu_zip;
	decode_baidu_source;
}

### Entry ###
if [ $# != 1 ];then
	usage;
	exit 1;
else
	prepare_baidu_smali_source
fi