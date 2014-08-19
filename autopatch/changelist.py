#!/usr/bin/python
# Filename: changelist.py


"""
Usage: $shell changelist.py [OPTIONS]

              OPTIONS:
                  --make  : Make the change list out
                  --show  : Show the change list out
"""

__author__ = 'duanqz@gmail.com'


import commands
import re
import os, sys

from config import Config
from formatters.log import Log

# try:
#     import xml.etree.cElementTree as ET
# except ImportError:
#     import xml.etree.ElementTree as ET

from lxml import etree as ET

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
            return

        cmd = "diff -rq %s %s" % (commands.mkarg(ChangeList.OLDER_ROOT), commands.mkarg(ChangeList.NEWER_ROOT))
        output = commands.getoutput(cmd)
        Log.d(TAG, output)
        ChangeList.xmlFrom(output)
        pass

    @staticmethod
    def xmlFrom(diffout):
        root = ET.Element('features')
        feature = ET.Element('feature', 
                   {'description' : 'These files are diff from %s and %s'%(ChangeList.OLDER_ROOT, ChangeList.NEWER_ROOT)})
        root.append(feature)

        # Named group REGEX of differ 
        differRE = re.compile("Files (?P<older>.*) and (?P<newer>.*) differ")
        # Named group REGEX of newer
        onlyRE   = re.compile("Only in (?P<path>.*): (?P<name>.*)")

        lines = diffout.split("\n")
        for line in lines:
            match = differRE.search(line)
            if match != None:
                target = os.path.relpath(match.group("newer"), ChangeList.NEWER_ROOT)

                revise = ET.Element('revise',
                           {'action' : 'MERGE',
                            'target' : target})
                feature.append(revise)
                continue

            match = onlyRE.search(line)
            if match != None:
                fullpath= os.path.join(match.group("path"), match.group("name"))
                if fullpath.startswith(ChangeList.NEWER_ROOT):
                    action = "ADD"
                    target = os.path.relpath(fullpath, ChangeList.NEWER_ROOT)
                elif fullpath.startswith(ChangeList.OLDER_ROOT):
                    action = "DELETE"
                    target = os.path.relpath(fullpath, ChangeList.OLDER_ROOT)

                revise = ET.Element('revise',
                           {'action' : action,
                            'target' : target})
                feature.append(revise)
                continue

        tree = ET.ElementTree(root)
        # Using pretty print to format XML
        tree.write(ChangeList.PATCH_XML, pretty_print=True,
               xml_declaration=True, encoding='utf-8')

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
