#!/bin/bash 
#############################################################################################################
# Option: target, ota;                                                                                      #
# target: This shell will pull files from phone, build apkcerts.txt and filesystem_config.txt from device,  #
# create linkinfo.txt from device and recover the device files' symlink information in target_file, then    #
# generate a target zip file.                                                                               #
# ota:    This shell will build a ota package from the target file.                                         #
#############################################################################################################

PRJ_ROOT=`pwd`
TOOL_DIR=$PORT_ROOT/tools
TARGET_FILES_TEMPLATE_DIR=$TOOL_DIR/target_files_template
OTA_FROM_TARGET_FILES=$TOOL_DIR/releasetools/ota_from_target_files

OUT_DIR=$PRJ_ROOT/out
OEM_TARGET_DIR=$OUT_DIR/oem_target_files
SYSTEM_DIR=$OEM_TARGET_DIR/SYSTEM
META_DIR=$OEM_TARGET_DIR/META
RECOVERY_ETC_DIR=$OEM_TARGET_DIR/RECOVERY/RAMDISK/etc
OEM_TARGET_ZIP=$OUT_DIR/oem_target_files.zip
OUTPUT_OTA_PACKAGE=$OUT_DIR/oem_ota_rom.zip

ROOT_STATE="system_root"

# check system root state
function check_root_state {
	echo ">>> check root state of phone ..."
	wait_for_device_online
	SECURE_PROP=$(adb shell cat /default.prop | grep -o "ro.secure=\w")
	if [ x"$SECURE_PROP" = x"ro.secure=0" ];then
		ROOT_STATE="kernel_root"
		echo ">>> system root state: kernel root"
	else
		echo "exit" > exit_command
		wait_for_device_online
		adb push exit_command /data/local/tmp
		rm -f exit_command
		if echo "su < /data/local/tmp/exit_command; exit" | adb shell | grep "not found" > /dev/null;then
			echo ">>> ERROR: Not a root phone, please root this device firstly"
			exit 1;
		fi
		ROOT_STATE="system_root"
		echo ">>> system root state: system root"
	fi
}

# check for files preparing
function check_for_env_prepare {
	if [ ! -f $PRJ_ROOT/recovery.fstab ];then
		echo ">>> can not find $PRJ_ROOT/recovery.fstab"
		exit 1
	fi
}

# copy the whole target_files_template dir
function copy_target_files_template {
    echo ">>> Copy target file template into current working directory"
    rm -rf $OEM_TARGET_DIR
    rm -f $OEM_TARGET_ZIP
    mkdir -p $OEM_TARGET_DIR
    cp -r $TARGET_FILES_TEMPLATE_DIR/* $OEM_TARGET_DIR
}

# wait for the device to be online or timeout
function wait_for_device_online {
	echo ">>> Wait for the device to be online..."

	local timeout=30
	while [ $timeout -gt 0 ]
	do
		if adb shell ls > /dev/null; then
			echo ">>> device is online"
			break
		fi
		echo ">>> device is not online, wait .."
		sleep 3
		timeout=$[$timeout - 3]
	done
	if [ $timeout -eq 0 ];then
		echo ">>> Please ensure adb can find your device and then rerun this script."
		exit 1
	fi
}

# get device system files info
function get_device_system_info {
	adb push $TOOL_DIR/releasetools/getfilesysteminfo /data/local/tmp
	adb shell chmod 0777 /data/local/tmp/getfilesysteminfo

	wait_for_device_online
	if [ "$ROOT_STATE" = "system_root" ];then
		adb push $TOOL_DIR/releasetools/getsysteminfocommand /data/local/tmp
		echo "su < /data/local/tmp/getsysteminfocommand; exit" | adb shell
		adb pull /data/local/tmp/system.info $META_DIR/
		adb pull /data/local/tmp/link.info $META_DIR/
	else
		adb shell /data/local/tmp/getfilesysteminfo --info /system > $META_DIR/system.info
		adb shell /data/local/tmp/getfilesysteminfo --link /system > $META_DIR/link.info
	fi

	if [ -f $META_DIR/system.info -a -f $META_DIR/link.info ];then
		echo ">>> get device system files info done"
	else
		echo ">>> failed to get device system files info"
		exit 1
	fi
}

# build filesystem_config.txt from device
function build_filesystem_config {
    echo ">>> build filesystem_config.txt"
    fs_config=`cat $META_DIR/system.info | col -b | sed -e '/getfilesysteminfo/d'`
    OLD_IFS=$IFS
    IFS=$'\n'
    for line in $fs_config
    do
        echo $line | grep -q -e "\<su\>" && continue
        echo $line | grep -q -e "\<invoke-as\>" && continue
        echo $line >> $META_DIR/tmp.txt
    done
    IFS=$OLD_IFS
    cat $META_DIR/tmp.txt | sort > $META_DIR/filesystem_config.txt
    rm -f $META_DIR/tmp.txt
	if [ ! -f $META_DIR/filesystem_config.txt ];then
		echo ">>> Failed to create filesystem_config.txt"
		exit 1
	fi
	rm -f $META_DIR/system.info
}

# recover the device files' symlink information
function recover_symlink {
    echo ">>> Run recoverylink.py to recover symlink"
    cat $META_DIR/link.info | sed -e '/\<su\>/d;/\<invoke-as\>/d' | sort > $SYSTEM_DIR/linkinfo.txt
    python $TOOL_DIR/releasetools/recoverylink.py $OEM_TARGET_DIR
	mv $SYSTEM_DIR/linkinfo.txt $META_DIR
	rm $META_DIR/link.info
	if [ ! -f $META_DIR/linkinfo.txt ];then
		echo ">>> Failed to create linkinfo.txt"
		exit 1
	fi
}

function deal_with_system_pull_log {
	cat $OUT_DIR/system-pull.log | grep "^failed to copy" > $OUT_DIR/system-pull-failed.log
	if [ -s $OUT_DIR/system-pull-failed.log ];then
		echo "-------------------------------------------------------" > $OUT_DIR/build-info-to-user.txt
		echo "Some files those pull failed you must deal with manually:" >> $OUT_DIR/build-info-to-user.txt
		cat $OUT_DIR/system-pull-failed.log | sed -e "s/.*out\/oem_target_files\/SYSTEM\/\(.*\)'.*/\1/" >> $OUT_DIR/build-info-to-user.txt
		echo "" >> $OUT_DIR/build-info-to-user.txt
		echo "---------" >> $OUT_DIR/build-info-to-user.txt
		echo "pull log:" >> $OUT_DIR/build-info-to-user.txt
		cat $OUT_DIR/system-pull-failed.log >> $OUT_DIR/build-info-to-user.txt
		echo "-------------------------------------------------------" >> $OUT_DIR/build-info-to-user.txt
	fi
}

# build the SYSTEM dir under target_files
function build_SYSTEM {
    echo ">>> Extract the whole /system from device"
    adb pull /system $SYSTEM_DIR 2>&1 | tee $OUT_DIR/system-pull.log
    find $SYSTEM_DIR -name su | xargs rm -f
    find $SYSTEM_DIR -name invoke-as | xargs rm -f
	deal_with_system_pull_log

    build_filesystem_config
    recover_symlink
}

# build apkcerts.txt from packages.xml
function build_apkcerts {
    echo ">>> Build apkcerts.txt"
	if [ x"$ROOT_STATE" = x"system_root" ];then
		echo "chmod 666 /data/system/packages.xml" > chmodcommand
		adb push chmodcommand /data/local/tmp/chmodcommand
		rm chmodcommand
		echo "su < /data/local/tmp/chmodcommand; exit" | adb shell
	else
		adb shell chmod 666 /data/system/packages.xml
	fi
    adb pull /data/system/packages.xml $OEM_TARGET_DIR
    python $TOOL_DIR/apkcerts.py $OEM_TARGET_DIR/packages.xml $META_DIR/apkcerts.txt
    for file in `ls $SYSTEM_DIR/framework/*.apk`
    do
        apk=`basename $file`
        echo "name=\"$apk\" certificate=\"tools/security/platform.x509.pem\" private_key=\"tools/security/platform.pk8\"" >> $META_DIR/apkcerts.txt
    done
    cat $META_DIR/apkcerts.txt | sort > $META_DIR/temp.txt
    mv $META_DIR/temp.txt $META_DIR/apkcerts.txt
    rm -f $OEM_TARGET_DIR/packages.xml
	if [ ! -f $META_DIR/apkcerts.txt ];then
		echo ">>> Failed to create apkcerts.txt"
		exit 1
	fi
}

# prepare boot.img recovery.fstab for target
function prepare_boot_recovery {
	if [ -f $PRJ_ROOT/boot.img ];then
		mkdir -p $OEM_TARGET_DIR/BOOTABLE_IMAGES
		cp -f $PRJ_ROOT/boot.img $OEM_TARGET_DIR/BOOTABLE_IMAGES/boot.img
		echo ">>> Copy boot.img to $OEM_TARGET_DIR/BOOTABLE_IMAGES/boot.img"
	fi
	if [ ! -d $RECOVERY_ETC_DIR ];then
		mkdir -p $RECOVERY_ETC_DIR
	fi
	cp -f $PRJ_ROOT/recovery.fstab $RECOVERY_ETC_DIR/recovery.fstab
	echo ">>> Copy recovery.fstab to $RECOVERY_ETC_DIR/recovery.fstab"
}

# compress the target_files dir into a zip file
function zip_target_files {
    echo ">>> Compress the target_files dir into zip file"
    cd $OEM_TARGET_DIR
    zip -q -r -y $OEM_TARGET_ZIP *
    cd -
	rm -rf $OEM_TARGET_DIR
	if [ ! -f $OEM_TARGET_ZIP ];then
		echo ">>> Failed to create $OEM_TARGET_ZIP"
		exit 1
	fi
}

# pull files from phone and build a target file
function target-from-phone {
	check_root_state
	check_for_env_prepare
	copy_target_files_template
	wait_for_device_online
	get_device_system_info

	build_SYSTEM
	build_apkcerts

	prepare_boot_recovery
	zip_target_files
}

# build a new full ota package
function build_ota_package {
	if [ ! -f $OEM_TARGET_ZIP ];then
		echo ">>> Can not find $OEM_TARGET_ZIP"
		exit 1
	fi
    echo ">>> Build full ota package: $OUTPUT_OTA_PACKAGE from $OEM_TARGET_ZIP"
    $OTA_FROM_TARGET_FILES -n -k $PORT_ROOT/tools/security/testkey $OEM_TARGET_ZIP $OUTPUT_OTA_PACKAGE
	if [ ! -f $OUTPUT_OTA_PACKAGE ];then
		echo ">>> Failed to build $OUTPUT_OTA_PACKAGE"
		exit 1
	fi
}

function usage {
	echo "Usage: $0 target/ota"
	echo "      targe -- pull files from phone"
	echo "      ota   -- build ota from target"
	exit 1
}

if [ $# != 1 ];then
	usage
elif [ "$1" = "target" ];then
	target-from-phone
elif [ "$1" = "ota" ];then
	build_ota_package
else
	usage
fi

