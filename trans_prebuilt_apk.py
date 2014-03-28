#! /usr/bin/python
# lishaoyan@baidu.com, 2012

import sys, os, shutil
from os.path import join, basename, dirname
import zipfile
import re

def usage():
    print """
Transform the source apk to the destinal apk, while extracting the so 
libraries in apk to /system/lib and removing the so lirary items in 
apk at the same time.

If no 'system_lib_path" parameter is given, the script will not extract 
or remove so files in apk and only transfer the apk to the destination.

usage: trans_prebuilt_apk.py source_apk dest_apk [system_lib_path]

"""

def extract_so_from_apk(apk, so_target):
    """ extract the so in apk to specified path """
    target_dir = dirname(so_target)
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except OSError:
            pass

    so_zip_path = join('lib/armeabi', basename(so_target))
    apk_zip = zipfile.ZipFile(apk, "r")
    f = open(so_target, 'w')
    f.write(apk_zip.read(so_zip_path))
    f.close()

def get_apk_so_list(src):
    z = zipfile.ZipFile(src, "r")
    so_list = []
    for x in z.namelist():
        if x.endswith(".so"):
            so_list.append(x)
    return so_list

def transform_prebuilt_apk(src, dst, syslib_dir=None):
    d = os.path.dirname(dst)
    if len(d) > 1 and not os.path.exists(d):
        try:
            os.makedirs(d)
        except OSError:
            pass

    if syslib_dir is None:
        # copy apk to target
        shutil.copy(src, dst);
    else:
        # get so list
        so_list = get_apk_so_list(src)

        # extract to system lib dir
        for s in so_list:
            if re.search(r'/armeabi/', s) is not None:
                sp = syslib_dir + "/" + os.path.basename(s)
                if not os.path.exists(sp):
                    extract_so_from_apk(src, sp)

        # copy apk to dst while removing so in apk
        zin = zipfile.ZipFile(src, 'r')
        zout = zipfile.ZipFile(dst, 'w')
        for i in zin.infolist():
            if not i.filename.endswith(".so"):
                data = zin.read(i)
                zout.writestr(i, data)

if __name__ == "__main__":
    if (len(sys.argv) != 4) and (len(sys.argv) != 3):
        print "invalid input parameters!"
        usage()
        sys.exit(1)

    if not sys.argv[1].endswith(".apk"):
        print "only for apk transform!"
        sys.exit(1)

    if len(sys.argv) == 4:
        transform_prebuilt_apk(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        transform_prebuilt_apk(sys.argv[1], sys.argv[2])

