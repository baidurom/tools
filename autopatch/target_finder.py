#!/usr/bin/python
# Filename: target_finder.py

"""
Fast search the target out.

Usage: target_finder.py TARGET
        - TARGET target path relative to current directory.
"""

__author__ = 'duanqz@gmail.com'


import sys
import re
import os
import fnmatch
import commands

class TargetFinder:

    # The framework partitions
    PARTITIONS = []

    def __init__(self):
        self.__initPartitions()

    def __initPartitions(self):
        """ Parse out the framework partitions.
        """

        makefile = None
        for filename in os.listdir(os.curdir):
            if fnmatch.fnmatch(filename.lower(), "makefile"):
                makefile = filename

        if makefile == None:
            return

        fileHandle = open(makefile, "r")
        content = fileHandle.read()
        modifyJars = re.compile("\n\s*vendor_modify_jars\s*:=\s*(?P<jars>.*)\n")
        match = modifyJars.search(content)
        if match != None:
            TargetFinder.PARTITIONS = match.group("jars").split(" ")

        fileHandle.close()

    def __findInPartitions(self, target):
        """ Find the target in the partitions.
        """

        try:
            # Inner class, set outer class as new target to find
            index = target.index("$")
            newTarget = target[:index] + ".smali"
        except:
            newTarget = target

        # Continue to find in other partitions
        pos = target.index(".")
        tail = newTarget[pos:]
        for partition in TargetFinder.PARTITIONS:
            if os.path.exists(partition + tail):
                return partition + target[pos:]

        # Not found
        return target


    def __findInAll(self, target):
        """ Find the target in all project root
        """

        basename = os.path.basename(target)
        searchPath = []
        for partition in TargetFinder.PARTITIONS:
            if not partition.endswith(".jar.out"):
                partition += ".jar.out"
            searchPath.append(partition)

        cmd = "find %s -name %s" % (" ".join(searchPath), commands.mkarg(basename))
        (sts, text) = commands.getstatusoutput(cmd)
        try:
            if sts == 0:
                text = text.split("\n")[0]
                if len(text) > 0:
                    return text
        except:
            pass

        return target


    def find(self, target):
        """ Find the target out in the current directory.
        """

        # Firstly, check whether target already exists
        if os.path.exists(target):
            return target

        # Secondly, check whether target exist in framework partitions
        # It is more efficiently then find in all files
        target = self.__findInPartitions(target)
        if os.path.exists(target):
            return target

        # Thirdly, still not find the target, search in all sub directories
        return self.__findInAll(target)


# End of class TargetFinder

if __name__ == "__main__":
    argc = len(sys.argv)
    if argc != 2 :
        print __doc__
        sys.exit()

    target = sys.argv[1]
    print TargetFinder().find(target)
