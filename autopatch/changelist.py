#!/usr/bin/python
# Filename: changelist.py


"""


Usage: $shell changelist.py [PATCH_XML]
            - PATCH_XML  : The patch XML definition. Default to be patchall.xml
"""

__author__ = 'duanqz@gmail.com'



import os.path
import sys

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def usage():
    print "Usage : changelist.py [OPTIONS] [PATCH_XML]                                       "
    print "                                                                                  "
    print " As to incorporate from newer to older changes into vendor, we handle             "
    print " three files, using option to get the appropriate file list.                      "
    print " Default to get vendor's change list if OPTION not presented.                     "
    print "                                                                                  "
    print "        - OPTIONS                                                                 "
    print "            --vendor change list of vendor file                                   "
    print "            --older  diff list of older file                                      "
    print "            --newer  diff list of newer file                                      "
    print "                                                                                  "
    print "        - PATCH_XML the patch XML contains the change list definition             "
    print "                                                                                  "



class ChangeList:

    PRJ_ROOT = os.getcwd()

    PATCH_XML = os.path.join(PRJ_ROOT, "autopatch/changelist/patchall.xml")

    # List of targets defined in patch xml
    LIST = []

    # Each entry represents a map from type to path
    TYPE_MAP = { "vendor" : "",
                 "older"  : "autopatch/aosp",
                 "newer"  : "autopatch/bosp" }

    def __init__(self, patchXML=PATCH_XML):

        revises = ET.parse(patchXML).findall("feature/revise")
        for revise in revises:
            target = revise.attrib["target"]
            if target.endswith("*") :
                self.__appendTargetGroup(target)
            else:
                ChangeList.LIST.append(target)

        self.__reviseOlderAndNewerIfNeeded()

    def __appendTargetGroup(self, target):
        """ Append a group of targets if name of target ends with "*"
        """

        # List all the file in directory
        targetPath = os.path.join(ChangeList.PRJ_ROOT, os.path.dirname(target))
        files = os.listdir(targetPath)

        # Match the filename in the directory
        prefix = os.path.basename(target)
        index = prefix.index("*")
        prefix = prefix[0:index]
        for filename in files:
            if filename.startswith(prefix):
                target = os.path.join(os.path.dirname(target), filename)
                ChangeList.LIST.append(target)

    def __reviseOlderAndNewerIfNeeded(self):
        """ Revise the older and newer path if needed.
        """

        oldRoot = "autopatch/upgrade/last_baidu"
        newRoot = "autopatch/upgrade/baidu"
        if os.path.exists(os.path.join(ChangeList.PRJ_ROOT, oldRoot)) and \
           os.path.exists(os.path.join(ChangeList.PRJ_ROOT, newRoot)) :
            ChangeList.TYPE_MAP['older'] = oldRoot
            ChangeList.TYPE_MAP['newer'] = newRoot

    def get(self, option="vendor"):
        changeList = []

        try:
            top = ChangeList.TYPE_MAP[option]
        except KeyError:
            top = ChangeList.TYPE_MAP['vendor']

        for item in ChangeList.LIST:
            changeList.append(os.path.join(top, item))

        return changeList


def formatList(changeList):
    print "\n".join(changeList)


if __name__ == "__main__":
    option = "vendor"
    patchXML = ChangeList.PATCH_XML
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith("--"):
            option = arg[2:]
        else:
            patchXML = arg

    if option == "help":
        usage()
        sys.exit()
    else:
        formatList(ChangeList(patchXML).get(option))
