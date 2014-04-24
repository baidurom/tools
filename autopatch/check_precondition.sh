#!/bin/bash

# check_precondition.sh
#
# check_precondition of auto patch:
#
# @author: duanqz@gmail.com
#

DEODEX_THREAD_NUM=4
DEODEX=${PORT_ROOT}/tools/deodex.sh
APKTOOL=${PORT_ROOT}/tools/apktool
ID_TO_NAME_TOOL=${PORT_ROOT}/tools/idtoname.py


function usage()
{
	echo "check_precondition.sh [option] [PRJ_ROOT]                            "
	echo "      - PRJ_ROOT: the current device root.                           "
	echo "                  e.g. check_precondition.sh ~/coron/devices/maguro/ "
	echo "                                                                     "
	echo "      OPTIONS                                                        "
	echo "        --upgrade: check precondition for upgrade.                   "
	echo "        --help:    show help.                                        "
	echo "                                                                     "
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
	[ ! -e ${baidu_zip} ] && echo " ERROR: ${baidu_zip} not exists." && return 0;

	echo " deodex ${baidu_zip}, time-costly, have a drink ...";
	${DEODEX} ${baidu_zip} ${DEODEX_THREAD_NUM} > /dev/null;
	[ ! -e ${deodex_zip} ] && echo " ERROR: deodex ${baidu_zip} failed!" && return 0;

	return 1
}


#
# Decode apk contained in DECODE_APKS to smali
#
DECODE_APKS=()
function decode_apk()
{
	local src_dir=$1
	local dst_dir=$2

	# Decode apks one by one
	echo " decoding ${DECODE_APKS[@]} ...";
	for apk in ${DECODE_APKS[*]} ; do
		${APKTOOL} d -f ${src_dir}/${apk}.apk ${dst_dir}/${apk};
	done
}


#
# Decode jar contained in DECODE_JARS to smali
#
DECODE_JARS=(framework.jar services.jar telephony-common.jar secondary_framework.jar secondary-framework.jar)
function decode_jar()
{
	local src_dir=$1
	local dst_dir=$2

	# Firstly, decode framework-res.apk
	echo " decoding framework-res ...";
	${APKTOOL} d -f ${src_dir}/framework-res.apk ${dst_dir}/framework-res;

	# Secondly, find out the public.xml
	local public_xml=${dst_dir}/framework-res/res/values/public.xml

	# Thirdly, decode jars one by one
	echo " decoding ${DECODE_JARS[@]} ...";
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

	local tempdir=`mktemp -d /tmp/tempdir.XXXXX`
	echo " unzip ${deodex_zip} to ${tempdir} ...";
	unzip -q -o ${deodex_zip} -d ${tempdir};

	[ -d ${tempdir}/SYSTEM/ ] && mv ${tempdir}/SYSTEM/ ${tempdir}/system/;

	decode_jar ${tempdir}/system/framework ${out};
	decode_apk ${tempdir}/system/app       ${out};

	rm -rf $tempdir
}


# Combine framework partitions into framework.jar.out
PARTITIONS=(secondary_framework.jar.out secondary-framework.jar.out)
function combine_framework_partitions()
{
	local dir=$1
	for partition in ${PARTITIONS[*]} ; do
		if [ -d ${dir}/${partition} ]; then
			cp -r  ${dir}/${partition}/smali ${dir}/framework.jar.out
			rm -rf ${dir}/${partition};
		fi
	done
}


#
# Prepare necessary things for upgrade
#
function prepare_upgrade()
{
	# Prepare upgrade list
	local src=$PORT_ROOT/tools/autopatch/upgrade
	local dst=$PRJ_ROOT/autopatch

	[ ! -d ${dst} ] && mkdir -p ${dst}
	cp -r -u ${src} ${dst}


	local last_baidu_zip=${PRJ_ROOT}/baidu/last_baidu.zip
	local baidu_zip=${PRJ_ROOT}/baidu/baidu.zip

	# Check if baidu.zip and last_baidu.zip both exist.
	if [ ! -e ${last_baidu_zip} ] || [ ! -e ${baidu_zip} ]; then
		echo " last_baidu.zip or baidu.zip not found in ${PRJ_ROOT}/baidu"
		prepare_xosp
		return
	fi

	local upgrade_last_baidu=${PRJ_ROOT}/autopatch/upgrade/last_baidu
	local upgrade_baidu=${PRJ_ROOT}/autopatch/upgrade/baidu

	# Decode old baidu base if not exist
	if [ ! -d ${upgrade_last_baidu} ]; then
		deodex_baidu_zip ${last_baidu_zip};
		[ $? -eq 0 ] && return 

		decode_baidu_source ${last_baidu_zip}.deodex.zip ${upgrade_last_baidu};
		combine_framework_partitions ${upgrade_last_baidu}
	fi

	# Decode new baidu base if not exist
	if [ ! -d ${upgrade_baidu} ]; then
		deodex_baidu_zip ${baidu_zip};
		[ $? -eq 0 ] && return

		decode_baidu_source ${baidu_zip}.deodex.zip ${upgrade_baidu};
		combine_framework_partitions ${upgrade_baidu}
	fi

}


#
# Prepare AOSP and BOSP
#
XOSP=(aosp bosp)
function prepare_xosp()
{
	# Copy patches from reference directory to current project
	local src=${PORT_ROOT}/reference
	local dst=${PRJ_ROOT}/autopatch

	echo " prepare ( ${XOSP[@]} ) from ${src} ..."
	for item in ${XOSP[*]} ; do
		cp -r -u ${src}/${item} ${dst}
	done

	# Combine framework partitions of BOSP
	combine_framework_partitions ${dst}/bosp
}


#
# Prepare the XML changelist for auto patching.
# The file to be patched are defined in XML.
#
function prepare_changelist()
{
	# Copy change-list from tools/autopatch/ directory to current project
	local src=$PORT_ROOT/tools/autopatch/changelist
	local dst=$PRJ_ROOT/autopatch

	[ ! -d ${dst} ] && mkdir -p ${dst}

	echo " prepare changelist from ${src} ..."
	cp -r -u ${src} ${dst}
}


#
# Prepare baidu.zip from reference/baidu_base
#
function prepare_baidu_zip()
{
	local baidu_zip=${PRJ_ROOT}/baidu/baidu.zip
	local baidu_base=${PORT_ROOT}/reference/baidu_base

	if [ ! -e ${baidu_zip} ]; then
		echo " prepare baidu.zip from ${baidu_base} ..."
		[ ! -e ${PRJ_ROOT}/baidu ] && mkdir ${PRJ_ROOT}/baidu -p
		cd ${baidu_base}
		zip -q -r ${baidu_zip} *
		cd ${PRJ_ROOT}
	fi
}

### Entry ###
while true ; do
	case "$1" in
		-h|--help) usage ; exit 0 ;;

		-u|--upgrade) UPGRADE=true;
			case "$2" in
				"") PRJ_ROOT=.  ; shift 2 ; break;;
				*)  PRJ_ROOT=$2 ; shift 2 ; break;;
			esac ;;

		"") PRJ_ROOT=.;  shift; break ;;

		*)  PRJ_ROOT=$1; shift; break ;;
	esac
done


# Prepare necessary
prepare_baidu_zip;

# Prepare Optional
if [ ${UPGRADE} ]; then
	prepare_upgrade;
else
	prepare_changelist;
	prepare_xosp;
fi

exit 0;

