#!/usr/bin/python
# Filename: changelist.py


"""
Usage: $shell changelist.py [OPTIONS]

              OPTIONS:
                  --make  : Make the change list out
                  --show  : Show the change list out
"""

__author__ = 'duanqz@gmail.com'


import shutil
import os, sys
import subprocess
import tempfile

from config import Config
from formatters.log import Log

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

#from lxml import etree as ET

TAG="changelist"

class ChangeList:


    def __init__(self, olderRoot, newerRoot, patchXML):
        ChangeList.OLDER_ROOT = olderRoot
        ChangeList.NEWER_ROOT = newerRoot
        ChangeList.PATCH_XML  = patchXML

    def make(self, force=True):
        """ Generate the change list into XML.
            Set force as False not to generate again if exists.  
        """

        if not force and os.path.exists(ChangeList.PATCH_XML):
            Log.d(TAG, "Using the existing %s" % ChangeList.PATCH_XML)
            return True

        hasChange = ChangeList.XMLFromDiff()

        return hasChange


    @staticmethod
    def XMLFromDiff():
        (root, feature) = ChangeList.createXML()

        tmp = ChangeList.fuse()

        hasChange = False

        for (dirpath, dirnames, filenames) in os.walk(tmp):

            dirnames = dirnames # No use, just avoid of warning

            for filename in filenames:
                path =  os.path.join(dirpath, filename)

                target = os.path.relpath(path, tmp)
                older  = os.path.join(ChangeList.OLDER_ROOT,  target)
                newer  = os.path.join(ChangeList.NEWER_ROOT,  target)

                olderExists = os.path.exists(older)
                newerExists = os.path.exists(newer)
                if olderExists and newerExists:
                    subp = subprocess.Popen(["diff",  older, newer], stdout=subprocess.PIPE)
                    subp.wait()
                    # 0 if inputs are the same
                    # 1 if different
                    # 2 if trouble, we do not handle this case
                    if subp.returncode == 1:
                        ChangeList.appendReivse(feature, "MERGE", target)
                        hasChange = True
                elif olderExists:
                    ChangeList.appendReivse(feature, "DELETE", target)
                    hasChange = True
                elif newerExists:
                    ChangeList.appendReivse(feature, "ADD", target)
                    hasChange = True

        shutil.rmtree(tmp)

        ChangeList.writeXML(root)

        return hasChange


    @staticmethod
    def fuse():
        tmp = tempfile.mktemp()
        os.makedirs(tmp)
        for subdir in os.listdir(ChangeList.OLDER_ROOT):
            src = os.path.join(ChangeList.OLDER_ROOT, subdir)
            subprocess.Popen(["cp", "-frp", src, tmp], stdout=subprocess.PIPE).wait()

        for subdir in os.listdir(ChangeList.NEWER_ROOT):
            src = os.path.join(ChangeList.NEWER_ROOT, subdir)
            subprocess.Popen(["cp", "-frp", src, tmp], stdout=subprocess.PIPE).wait()

        return tmp


    @staticmethod
    def createXML():
        root = ET.Element('features')
        feature = ET.Element('feature',
                   {'description' : 'These files are diff from %s and %s' %(ChangeList.OLDER_ROOT, ChangeList.NEWER_ROOT)})
        root.append(feature)

        return (root, feature)


    @staticmethod
    def writeXML(root):
        tree = ET.ElementTree(root)
        tree.write(ChangeList.PATCH_XML, #pretty_print=True,
               xml_declaration=True, encoding='utf-8')

        Log.i(TAG, "%s is generated" % ChangeList.PATCH_XML)


    @staticmethod
    def appendReivse(feature, action, target):
        revise = ET.Element('revise',
                           {'action' : action,
                            'target' : target})
        feature.append(revise)


    def show(self):
        if not os.path.exists(ChangeList.PATCH_XML):
            print ChangeList.PATCH_XML + " not exists. Use `make` to generate."
            return

        changelist = []

        revises = ET.parse(ChangeList.PATCH_XML).findall("feature/revise")
        for revise in revises:
            target = revise.attrib["target"]
            changelist.append(target)

        print "\n".join(changelist)


if __name__ == "__main__":
    for arg in sys.argv:
        if arg in ("--make", "-m"):
            ChangeList(Config.AOSP_ROOT, Config.BOSP_ROOT, Config.PATCHALL_XML).make()
            sys.exit(0)
        elif arg in ("--show", "-s"):
            ChangeList(Config.AOSP_ROOT, Config.BOSP_ROOT, Config.PATCHALL_XML).show()
            sys.exit(0)

    print __doc__
