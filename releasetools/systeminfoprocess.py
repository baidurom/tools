#!/usr/bin/env python

__author__ = 'zhangweiping@baiyi-mobile.com'

import os
import sys
import string

"""
    This is the master Users and Groups config for the platform.
    follow system/core/include/private/android_filesystem_config.h
"""
AID_ROOT         =     0  # traditional unix root user

AID_SYSTEM       =  1000  # system server

AID_RADIO        =  1001  # telephony subsystem, RIL
AID_BLUETOOTH    =  1002  # bluetooth subsystem
AID_GRAPHICS     =  1003  # graphics devices
AID_INPUT        =  1004  # input devices
AID_AUDIO        =  1005  # audio devices
AID_CAMERA       =  1006  # camera devices
AID_LOG          =  1007  # log devices
AID_COMPASS      =  1008  # compass device
AID_MOUNT        =  1009  # mountd socket
AID_WIFI         =  1010  # wifi subsystem
AID_ADB          =  1011  # android debug bridge (adbd)
AID_INSTALL      =  1012  # group for installing packages
AID_MEDIA        =  1013  # mediaserver process
AID_DHCP         =  1014  # dhcp client
AID_SDCARD_RW    =  1015  # external storage write access
AID_VPN          =  1016  # vpn system
AID_KEYSTORE     =  1017  # keystore subsystem
AID_USB          =  1018  # USB devices
AID_DRM          =  1019  # DRM server
AID_MDNSR        =  1020  # MulticastDNSResponder (service discovery)
AID_GPS          =  1021  # GPS daemon
AID_UNUSED1      =  1022  # deprecated, DO NOT USE
AID_MEDIA_RW     =  1023  # internal media storage write access
AID_MTP          =  1024  # MTP USB driver access
AID_UNUSED2      =  1025  # deprecated, DO NOT USE
AID_DRMRPC       =  1026  # group for drm rpc
AID_NFC          =  1027  # nfc subsystem
AID_SDCARD_R     =  1028  # external storage read access

AID_SHELL        =  2000  # adb and debug shell user
AID_CACHE        =  2001  # cache access
AID_DIAG         =  2002  # access to diagnostic resources

AID_NET_BT_ADMIN =  3001  #  bluetooth: create any socket
AID_NET_BT       =  3002  #  bluetooth: create sco, rfcomm or l2cap sockets
AID_INET         =  3003  #  can create AF_INET and AF_INET6 sockets
AID_NET_RAW      =  3004  #  can create raw INET sockets
AID_NET_ADMIN    =  3005  #  can configure interfaces and routing tables.
AID_NET_BW_STATS =  3006  #  read bandwidth statistics
AID_NET_BW_ACCT  =  3007  #  change bandwidth statistics accounting
AID_NET_BT_STACK =  3008  #  bluetooth: access config files

AID_CCCI         =  9996
AID_NVRAM        =  9997
AID_MISC         =  9998  #  access to misc storage
AID_NOBODY       =  9999

android_ids = {
    "root"         : AID_ROOT,
    "system"       : AID_SYSTEM,
    "radio"        : AID_RADIO,
    "bluetooth"    : AID_BLUETOOTH,
    "graphics"     : AID_GRAPHICS,
    "input"        : AID_INPUT,
    "audio"        : AID_AUDIO,
    "camera"       : AID_CAMERA,
    "log"          : AID_LOG,
    "compass"      : AID_COMPASS,
    "mount"        : AID_MOUNT,
    "wifi"         : AID_WIFI,
    "dhcp"         : AID_DHCP,
    "adb"          : AID_ADB,
    "install"      : AID_INSTALL,
    "media"        : AID_MEDIA,
    "drm"          : AID_DRM,
    "mdnsr"        : AID_MDNSR,
    "nfc"          : AID_NFC,
    "drmrpc"       : AID_DRMRPC,
    "shell"        : AID_SHELL,
    "cache"        : AID_CACHE,
    "diag"         : AID_DIAG,
    "net_bt_admin" : AID_NET_BT_ADMIN,
    "net_bt"       : AID_NET_BT,
    "net_bt_stack" : AID_NET_BT_STACK,
    "sdcard_r"     : AID_SDCARD_R,
    "sdcard_rw"    : AID_SDCARD_RW,
    "media_rw"     : AID_MEDIA_RW,
    "vpn"          : AID_VPN,
    "keystore"     : AID_KEYSTORE,
    "usb"          : AID_USB,
    "mtp"          : AID_MTP,
    "gps"          : AID_GPS,
    "inet"         : AID_INET,
    "net_raw"      : AID_NET_RAW,
    "net_admin"    : AID_NET_ADMIN,
    "net_bw_stats" : AID_NET_BW_STATS,
    "net_bw_acct"  : AID_NET_BW_ACCT,
    "misc"         : AID_MISC,
    "nvram"        : AID_NVRAM,
    "nobody"       : AID_NOBODY,
    "ccci"         : AID_CCCI,
}

def nameToID(name):
    if name not in android_ids.keys():
        id = android_ids["root"]
        print "WARNING: can't find "+name+" in android_ids, use root instead"
    else:
        id = android_ids[name]
    return str(id)

def turnModToNum(mod):
    num = 0
    if cmp(mod[0], "r") == 0:
        num += 4
    if cmp(mod[1], "w") == 0:
        num += 2
    if cmp(mod[2], "x") == 0 or cmp(mod[2], "s") == 0:
        num += 1
    return str(num)

def modToNum(mod):
    ownMod=mod[1:4]
    grpMod=mod[4:7]
    otrMod=mod[7:10]
    newMod=turnModToNum(ownMod)+turnModToNum(grpMod)+turnModToNum(otrMod)
    return newMod

def main(fileinfo, systeminfo, linkinfo):
    fFile = open(fileinfo, 'r')
    sFile = open(systeminfo, 'w')
    lFile = open(linkinfo, 'w')
    for line in fFile.readlines():
        pList = line.split()
        if cmp(pList[0][0],"l") == 0:
            prop = modToNum(pList[0]) #prop
            uid = nameToID(pList[1])  #uid
            gid = nameToID(pList[2])  #gid
            name = pList[-4]  # file name
            lname = pList[-2]  # link name
            dir = pList[-1]   # file directory
            path = os.path.join(dir, name)
            if cmp(lname[0], "/") == 0:  # file is a absolute path, not need to combine
                lpath = lname
            else:
                lpath = os.path.join(dir, lname)
            lFile.write(path+"|"+lpath+"\n")
        else:
            prop = modToNum(pList[0]) #prop
            uid = nameToID(pList[1])  #uid
            gid = nameToID(pList[2])  #gid
            name = pList[-2]  # file name
            dir = pList[-1]   # file directory
            path = os.path.join(dir, name)
            sFile.write(path+" "+uid+" "+gid+" "+prop+"\n")
    fFile.close()
    sFile.close()
    lFile.close()

def Usage():
    print "Usage: systeminfoprocess.py  file.info  system.info  link.info "

if __name__ == '__main__':
    argLen = len(sys.argv)
    if argLen == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        Usage()
