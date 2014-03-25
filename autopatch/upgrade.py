#!/usr/bin/python
# Filename: upgrade.py

### File Information ###
"""
Upgrade ROM version automatically.
Usage: upgrade.py FROM [TO]
         - FROM: current version (e.g. ROM40)
         - TO: version that upgrade to (e.g. ROM45). Default to be the latest version.
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'



import os
import sys
import string
from autopatch import AutoPatch
from config import Config, Log


def usage():
    print "\n"
    print " Usage: upgrade.py FROM [TO]                                                                             "
    print "        - FROM: current version (e.g. ROM40)                                                             "
    print "        - TO: version that upgrade to (e.g. ROM45). If not present, will upgrade to the latest available."
    print "\n"


class Upgrade:

    def __init__(self, upgradeFrom, upgradeTo):
        self.run(upgradeFrom, upgradeTo)

    def run(self, oldVersion, newVersion):
        """ Upgrade from old version to new version
        """

        oldVersion = ROMVersion.toDigit(oldVersion)
        newVersion = ROMVersion.toDigit(newVersion)

        curVersion = oldVersion
        for patchName in ROMVersion.mPatches:
            if curVersion >= newVersion:
                break;

            if curVersion < ROMVersion.toDigit(patchName):
                self.applyPatch(patchName)
                curVersion += 1

    def applyPatch(self, patchName):
        """ Apply the patch.
        """

        patchXML = os.path.join(Config.UPGRADE_DIR, patchName)
        Config.setPatchXML(patchXML)

        # Append the last BOSP directory to arguments list
        if os.path.exists(Config.UPGRADE_LAST_BAIDU_DIR) and \
           os.path.exists(Config.UPGRADE_BAIDU_DIR) :
            Config.setDiffDir(Config.UPGRADE_LAST_BAIDU_DIR, Config.UPGRADE_BAIDU_DIR)

        Log.i("\n>>> Patching " + patchName + "\t[Diff from " + Config.OLDER_DIR + " to " + Config.NEWER_DIR + " ]")
        AutoPatch()


class ROMVersion:
    """ Model of the ROM versions.
    """

    mPatches = []

    def __init__(self):
        patches = os.listdir(Config.UPGRADE_DIR)
        for patch in patches:
            if patch.startswith("ROM"):
                ROMVersion.mPatches.append(patch)

        ROMVersion.mPatches.sort(cmp=ROMVersion.comparator);

    def getLatestVersion(self):
        size = len(ROMVersion.mPatches)
        return ROMVersion.mPatches[size-1]

    @staticmethod
    def comparator(patchName1, patchName2):
        """ Comparator to sort the patch name.
            Patch name is like ROM39, ROM40, etc.
        """

        version1 = ROMVersion.toDigit(patchName1)
        version2 = ROMVersion.toDigit(patchName2)
        return version1 - version2

    @staticmethod
    def toDigit(patchName):
        version = filter(str.isdigit, patchName)
        return string.atoi(version)



if __name__ == "__main__":
    argc = len(sys.argv)
    if argc <= 1:
        usage()
        exit(1)

    upgradeTo = ROMVersion().getLatestVersion()
    if argc > 1: upgradeFrom = sys.argv[1]
    if argc > 2: upgradeTo = sys.argv[2]

    Upgrade(upgradeFrom, upgradeTo)
