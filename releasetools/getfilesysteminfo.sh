#!/system/bin/sh

FILE_INFO=/data/local/tmp/file.info

function traverse_dir {
	local root=$1
	ls -l ${root} | while read line
	do
		name=${line##* }
		if [ "${line:0:1}" = "d" ]; then # directory
			traverse_dir ${root}/${name}
		fi
	echo "$line ${root:1}" >> ${FILE_INFO}
	done
}

rm -f ${FILE_INFO}
traverse_dir "/system"
chmod 666 ${FILE_INFO}