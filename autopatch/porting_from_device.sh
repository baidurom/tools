#!/bin/bash


#
# Porting commits from DEVICE to current
#
#
# @author: duanqz@gmail.com
#


DEVICE=${1}
NUM=${2}


DEVICE_DIR=${PORT_ROOT}/devices/${DEVICE}

function usage()
{
	echo "Usage: porting_from_device.sh DEVICE [NUM]                                            "
	echo "                                                                                      "
	echo "       - DEVICE the source device you porting from                                    "
	echo "                                                                                      "
	echo "       - NUM the number of latest commits you would like to pick                      "
	echo "             if not present, an interactive UI will show for you to choose the commit "
	echo "                                                                                      "
	echo "      e.g. porting_from_device.sh maguro                                              "
	echo "           Porting commits from maguro interactively, maguro is an existing device    "
	echo "                                                                                      "
	echo "      e.g. porting_from_device.sh maguro 3                                            "
	echo "           Porting the latest 3 commits from maguro quietly.                          "
	echo "                                                                                      "
}

#
# Check whether the device exists or not.
#
function check_device_exists()
{
	if 	[ ! -e ${DEVICE_DIR}/Makefile ] && \
		[ ! -e ${DEVICE_DIR}/makefile ]; then
		echo "ERROR: Invalid device ${DEVICE}.";
		exit 1;
	fi
}


#
# Initialize all commits of device on branch.
# The result will be stored in ALL_COMMITS
#
ALL_COMMITS=
function init_device_all_commits()
{
	cd ${DEVICE_DIR}

	# Retrieve all commits of the device.
	ALL_COMMITS=$(git log --oneline | cut -d' ' -f1);

	cd - > /dev/null
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
	#UPPER_COMMIT=`echo ${ALL_COMMITS} | awk '{print $(NF-2)}'`
	echo ">>> Automatically choose lastest commits: [$LOWER_COMMIT]"
}

#
# Read LOWER_COMMIT and UPPER_COMMIT from user.
#
LOWER_COMMIT=
UPPER_COMMIT=
function read_user_input()
{
	echo ">>> All the commits of [${DEVICE}] are:";
	cd ${DEVICE_DIR}
	git log --oneline | tee
	cd - > /dev/null

	echo ""
	echo "  +-----------------------------------------------------------------------";
	echo "  |  Each 7 bits SHA1 code identify a specific commit on [${DEVICE}],     ";
	echo "  |  you could select one of them to port onto your own device.           ";
	echo "  |  If you would like to port a range of commits, select two as a range. ";
	echo "  +-----------------------------------------------------------------------";
	echo ""

	read -p ">>> Select the 7 bits SHA1 commit ID (q to exit): " LOWER_COMMIT UPPER_COMMIT;

	[ ${LOWER_COMMIT} == "q" ] && exit 0 

	[ -z ${LOWER_COMMIT} ] && [ -z ${UPPER_COMMIT} ] && choose_commits_range_automatically && return;

	echo ">>> Manually choose a range of commits [${LOWER_COMMIT} ${UPPER_COMMIT}]";
}



#
# Pick each commit independently.
#
function pick_one_commit()
{
	local commit=${1};

	local old_pwd=`pwd`
	local porting_dir=${old_pwd}/autopatch/porting
	[ ! -e ${porting_dir} ] && mkdir -p ${porting_dir}

	cd ${DEVICE_DIR}
	local patch=`git format-patch -1 ${commit}`
	mv ${patch} ${porting_dir}
	cd ${old_pwd}

	# -m Merge using conflict markers instead of creating reject files.
	# -t Ask no questions; skip bad-Prereq patches; assume reversed.
	patch -p1 -t -m < ${porting_dir}/${patch}

	rm ${porting_dir}/${patch}
}



#
# Pick commits from DEVICE and porting to current device
#
function porting_commits()
{
	if [ -z ${NUM} ]; then
		read_user_input;
	elif [ ${NUM} -gt 0 ]; then
		LOWER_COMMIT=`echo ${ALL_COMMITS} | cut -d" " -f1`
		UPPER_COMMIT=`echo ${ALL_COMMITS} | cut -d" " -f${NUM}`
	fi

	get_commits_by_range ${LOWER_COMMIT} ${UPPER_COMMIT};

	# Pick each commit in COMMITS_RANGE
	for commit in `echo ${COMMITS_RANGE} | tac -s" "`
	do
		pick_one_commit ${commit}
	done

	# Delete unnecessary files
	find . -name *.orig | xargs rm -rf
}


function main()
{
	check_device_exists;

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
