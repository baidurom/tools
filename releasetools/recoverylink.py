#!/usr/bin/python
import os
import sys

linkfile = sys.argv[1]
rootpath = sys.argv[2]

try:
    file_object = open(linkfile)
    linelist = file_object.read().split()
    for line in linelist:
        line = line.rstrip()
        filepath = line.split('|')
        if len(filepath) >= 2:
            """ linkfile -> dstfile """
            linkfile = filepath[0].replace('system', 'SYSTEM')
            dstfile = filepath[1]
            linkpath = os.path.join(rootpath, linkfile)
            if (os.path.exists(linkpath)):
                os.remove(linkpath)
            linkdir=os.path.join(rootpath, os.path.dirname(linkfile))
            linkname = os.path.basename(linkfile)
            dstname = os.path.basename(dstfile)
            if not (os.path.exists(linkdir)):
                os.makedirs(linkdir)
            if cmp(dstfile[0], "/") == 0: # use a absolute path
                lncmd = "cd " + linkdir + "; " + "ln -sf " + dstfile + " " + linkname
            else:
                lncmd = "cd " + linkdir + "; " + "ln -sf " + dstname + " " + linkname
            #print "lncmd: " + lncmd
            os.popen(lncmd)
except IOError:
    print r"%s isn't exist" % linkfile
    sys.exit(1)

file_object.close( )
print r"Recovery link files success"
sys.exit(0)
