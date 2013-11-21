#!/bin/bash

#
# framework_partition.sh
#
# This script is used in the specific device directory.
#
# @author: duanqizhi01@baidu.com(duanqz)
#

FRAMEWORK_PARTITION_DIR=${PORT_ROOT}/.partitions

function usage()
{
	echo "framework-partition.sh OPTION"
	echo "  OPTION:"
	echo "    -combine    Combine the partition of framework.jar.out together. In that way, it is easier to auto patch."
	echo "                The partition might be secondary-framework.jar.out(framework2.jar.out or framework-ext.jar.out)"
	echo ""
	echo "    -revert     Revert the combinated framework.jar.out to partitions. The re-combine process of combine."
}

#
# Retrieve the partitions of framework.jar
# The result is stored in variable PARTITIONS
#
function get_partitions()
{
	if [ -e Makefile ]; then
		local MAKEFILE=Makefile;
	elif [ -e makefile ]; then
		local MAKEFILE=makefile;
	else
		echo "ERROR: No makefile was found!";
		return;
	fi

	# Find out vendor_modify_jars in Makefile. These jars belong to vendor, but we
	# have to do some modifications in them.
	local vendor_modify_jars=`grep ^vendor_modify_jars ${MAKEFILE} | cut -d'=' -f2`;

	# Find out the partitions of framework.jar
	PARTITIONS=`echo ${vendor_modify_jars} | awk '{for(i=1;i<=NF;i++){if($i~/.*framework.*/)print $i}}'`;
}

#
# Combine the partitions into a whole framework.jar.out
#
function combine_frameworks()
{
	local PWD=`pwd`;
	local phone=`basename ${PWD}`;

	get_partitions;
	for partition in ${PARTITIONS}
	do
		# For each partition except framework.jar.out:
		# Firstly, save filenames to FRAMEWORK_PARTITION_DIR;
		# Secondly, move files from partition.jar.out to framework.jar.out
		if [ ${partition} != "framework" ] && [ -d ${partition}.jar.out/smali ]; then
			mkdir -p ${FRAMEWORK_PARTITION_DIR}/;
			find ${partition}.jar.out/smali -type f > "${FRAMEWORK_PARTITION_DIR}/${phone}:${partition}";
			cp -r  ${partition}.jar.out/smali/ framework.jar.out/;
			rm -rf ${partition}.jar.out/smali/;
		fi
	done

	# Also need to combine baidu secondary-framework (if exists) into framework.
	# It is not necessary to revert it.
	if [ -d ${PWD}/baidu/smali/secondary-framework.jar.out ]; then
		cp -r ${PWD}/baidu/smali/secondary-framework.jar.out/smali ${PWD}/baidu/smali/framework.jar.out
	fi
}


#
# Revert the framework.jar.out into the original partitions
#
function revert_frameworks()
{
	local PWD=`pwd`;
	local phone=`basename ${PWD}`;

	if [ ! -e ${FRAMEWORK_PARTITION_DIR} ]; then
		return
	fi

	local partitions="`find ${FRAMEWORK_PARTITION_DIR} -name ${phone}:*`";
    if [ -z "${partitions}" ]; then
        return
    fi

	for partition in ${partitions}
	do
		for partition_file in `cat ${partition}`
		do
			dir=`dirname ${partition_file}`
			mkdir -p ${dir}
			cut_partition_file=`echo ${partition_file} | cut -d'/' -f2-`
			mv "framework.jar.out/${cut_partition_file}" "${partition_file}"
		done
	done

	rm -rf ${partitions}
}

### Entry ###
if [ $# != 1 ];then
	usage;
	exit 1;
elif [ "$1" = "-combine" ];then
	combine_frameworks;
elif [ "$1" = "-revert" ];then
	revert_frameworks;
fi