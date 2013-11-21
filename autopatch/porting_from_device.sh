#!/bin/bash


#
# Porting commits from DEVICE to current
#
# @Parameter 1: DEVICE
# @Parameter 2: BRANCH on DEVICE
#
# @author: duanqizhi01@baidu.com(duanqz)
#


DEVICE=${1}
BRANCH=${2}

DEVICES_DIR=${PORT_ROOT}/devices

function usage()
{
	echo "Usage: porting_from_device.sh DEVICE BRANCH"
	echo "    e.g.: porting_from_device.sh maguro coron-4.2"
	echo ""
}

#
# Check whether the device exists or not.
#
function check_device_exists()
{
	local device_dir=${DEVICES_DIR}/${DEVICE};

	if 	[ ! -e ${device_dir}/Makefile ] && \
		[ ! -e ${device_dir}/makefile ]; then
		echo "ERROR: Invalid device ${DEVICE}.";
		exit 1;
	fi
}

#
# Fetch the DEVICE repository to local url, so that we can pick commits.
# The local url is named by DEVICE
#
# Note: It is time-cost when first time fetch.
#
function fetch_device_repository()
{
	# The first time should fetch the git repository of source device.
	local result=`git remote -v | grep -w "(fetch)" | grep -w "${DEVICE}"`;

	# Local url is named by DEVICE
	if [ -z "${result}" ]; then
		local old_pwd=`pwd`;
		cd ${DEVICES_DIR}/${DEVICE};
		git checkout -b ${BRANCH};
		cd ${old_pwd};

		git remote add ${DEVICE} ${DEVICES_DIR}/${DEVICE};
	fi

	git fetch ${DEVICE}
}

#
# Initialize all commits of device on branch.
# The result will be stored in ALL_COMMITS
#
ALL_COMMITS=
function init_device_all_commits()
{
	# Retrieve all commits of the device.
	ALL_COMMITS=$(git log ${DEVICE}/${BRANCH} --oneline | cut -d' ' -f1);
}

#
# Retrieve a range of commits of the device.
#
# @parameter 1: lower commit id in all commits
# @parameter 2: upper commit id in all commits
# The result will be stored in variable COMMITS_RANGE
#
COMMITS_RANGE=
function get_commits_by_range()
{
	local lower_commit=${1};
	local upper_commit=${2};

	local array;
	local index=0;
	local upper=-1;
	local lower=-1;
	for commit in `echo ${ALL_COMMITS}`
	do
		# Record the index of lower and upper
		[ ! -z ${upper_commit} ] && [ "${commit}" = "${upper_commit}" ] && upper=${index};
		[ ! -z ${lower_commit} ] && [ "${commit}" = "${lower_commit}" ] && lower=${index};

		# Record the commit to an COMMITS_RANGE
		array[$index]=${commit};
		((index++))
	done

	# Revise the lower and upper value
	if [ ${lower} -lt 0 ] && [ ${upper} -lt 0 ]; then
		lower=0;
		upper=${#array[@]};
	elif [ ${lower} -lt 0 ]; then
		echo "No lower commit ${lower_commit} found, use the ${array[0]} instead."
		lower=0
	elif [ ${upper} -lt 0 ]; then
		# Only one commit id is provided.
		upper=${lower}
	fi

	# Swap the upper and lower if necessary
	if [ ${upper} -lt ${lower} ]; then
		local swap=${upper};
		upper=${lower};
		lower=${swap};
	fi

	# Retrieve an sub array by range
	COMMITS_RANGE=${array[@]:${lower}:$[upper-lower+1]}
}

#
# choose a range of commits automatically.
#
function choose_commits_range_automatically()
{
	LOWER_COMMIT=`echo ${ALL_COMMITS} | cut -d" " -f1`
	UPPER_COMMIT=`echo $ALL_COMMITS | awk '{print $(NF-2)}'`
	echo ">>> Automatically choose a range of commits: [$UPPER_COMMIT  $LOWER_COMMIT]"
}

#
# Read LOWER_COMMIT and UPPER_COMMIT from user.
#
LOWER_COMMIT=
UPPER_COMMIT=
function read_user_input()
{
	echo ">>> All the commits on branch [${BRANCH}] of [${DEVICE}] are:";
	git log ${DEVICE}/${BRANCH} --oneline;
	echo "";
	echo ">>> Choose a range of commits you would like to pick...";
	read -p "(Press Enter will pick automatically): " LOWER_COMMIT UPPER_COMMIT;

	[ -z ${LOWER_COMMIT} ] && [ -z ${UPPER_COMMIT} ] && choose_commits_range_automatically && return;

	echo ">>> Manually choose a range of commits [${LOWER_COMMIT} ${UPPER_COMMIT}]";
}

#
# Pick each commit independently.
#
function pick_one_commit()
{
	local commit=${1};

	local result=`git cherry-pick ${commit}`;

	local error=`echo ${result} | grep -w "error:" | cut -d":" -f1`;
	if [ "${error}" = "error" ]; then
		exit 1;
	fi

	echo "Pick ${commit} successfully."
}

#
# Pick commits from DEVICE and porting to current device
#
function porting_commits()
{
	read_user_input;

	get_commits_by_range ${LOWER_COMMIT} ${UPPER_COMMIT};

	# Pick each commit in COMMITS_RANGE reversely
	for commit in `echo ${COMMITS_RANGE} | tac -s" "`
	do
		pick_one_commit $commit
	done
}


function main()
{
	check_device_exists;

	fetch_device_repository;

	init_device_all_commits;

	porting_commits;
}

### Entry ###
if [ $# -lt 1 ];then
	usage;
	exit 1;
else
	main;
fi
