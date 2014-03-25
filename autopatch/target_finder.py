#!/usr/bin/python
# Filename: target_finder.py

"""
Find the target file

@hide
  
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'


import sys
import re
import os
import fnmatch

def usage():
    print "Usage: target_finder.py TARGET                        "
    print "          - TARGET the target file defined in XML.    "


class TargetFinder:

    # The framework partitions
    PARTITIONS = []

    @staticmethod
    def parsePartitions():
        """ Parse out the framework partitions.
        """

        makefile = None
        for filename in os.listdir(os.curdir):
            if fnmatch.fnmatch(filename.lower(), "makefile"):
                makefile = filename

        if makefile == None:
            print "No makefile found in " + os.curdir
            sys.exit()

        fileHandle = open(makefile, "r")
        content = fileHandle.read()
        modifyJars = re.compile("\n\s*vendor_modify_jars\s*:=\s*(.*)\n")
        match = modifyJars.search(content)
        if match != None:
            TargetFinder.PARTITIONS = match.group(1).split(" ")

        fileHandle.close()

    def find(self, target):
        """ Find the target out in the current directory.
        """

        # Find directly
        if os.path.exists(target):
            return target

        TargetFinder.parsePartitions()
        return self.findInPartitions(target)

    def findInPartitions(self, target):
        """ Find the target in the partitions.
        """

        # Continue to find in other partitions
        pos = target.index(".")
        for partition in TargetFinder.PARTITIONS:
            newTarget = partition + target[pos:]
            if os.path.exists(newTarget):
                return newTarget

        # Not found
        return target

# End of class TargetFinder

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc != 2 :
        usage()
        sys.exit()

    target = sys.argv[1]
    print TargetFinder().find(target)
