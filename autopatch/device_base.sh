#!/bin/bash

# device_base.sh
#
# @author: duanqz@gmail.com
#

BASE_DEVICE=${PORT_ROOT}/devices/base
PWD=`pwd`
MY_DEVICE=`basename ${PWD}`


LAST_HEAD="${BASE_DEVICE}/.git/${MY_DEVICE}:LAST_HEAD"
ORIG_HEAD="${BASE_DEVICE}/.git/${MY_DEVICE}:ORIG_HEAD"


function usage()
{
	echo "Usage: device_base.sh [--last|--orig]                "
	echo "                                                     "
	echo "      OPTIONS:                                       "
	echo "        --last:   set to the last head.              "
	echo "        --orig:   set to the origin remote head.     "
    echo "                                                     "
	echo " You shou use --last and --orig sequencely as a pair."
}


function check_update()
{
    cd ${BASE_DEVICE}

    # If no LAST_HEAD or ORIG_HEAD, using the current head
    [ ! -e ${LAST_HEAD} ] && git rev-parse HEAD > ${LAST_HEAD}
    [ ! -e ${ORIG_HEAD} ] && git rev-parse HEAD > ${ORIG_HEAD}

	local option="-q"

	# Rebase the newest origin head
	local noBranch=`git branch | grep "(no branch)"`
	if [ ! -z "${noBranch}" ]; then
		local branch=`git log -1 --oneline --decorate=short | grep -wo "origin/.*," | cut -d"," -f1`
		git fetch  ${option} --all
		#git rebase --abort
		git rebase ${option} ${branch}
	else
		git pull ${option}
	fi

    local old_orig_head=`cat ${ORIG_HEAD}`
	local new_orig_head=`git rev-parse HEAD`

    if [ x"${old_orig_head}" == x"${new_orig_head}" ]
    then
        echo "already synced with remote origin"
    else
	    echo "sync remote origin, the newest commit is ${new_orig_head}"
        echo ${old_orig_head} > ${LAST_HEAD}
	    echo ${new_orig_head} > ${ORIG_HEAD}
    fi

    cd - > /dev/null
}


function set_last_head()
{
    check_update

	cd ${BASE_DEVICE}

	local commit=`cat ${LAST_HEAD}`
	git reset --hard ${commit}

	echo "the last commit is ${commit}"

	cd - > /dev/null
}



function set_orig_head()
{
	cd ${BASE_DEVICE}

    local commit=`cat ${ORIG_HEAD}`
    git reset --hard ${commit}

    echo "the origin commit is ${commit}"

	cd - > /dev/null
}



### Entry ###
[ $# -lt 1 ] && usage && exit 1;

[ "$1" == "--last" ] && set_last_head && exit 0

[ "$1" == "--orig" ] && set_orig_head && exit 0

