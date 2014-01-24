#!/usr/bin/python
# Filename: upgrade.py

### File Information ###
"""
Upgrade ROM version automatically.
Upgrade patches are defined in XML.
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'



### import block ###

import os
import sys
import string

import autopatch

### Class definition ###

class Main:

    def __init__(self):
        n = len(sys.argv)
        if n <= 2:
            Main.usage()
            exit(1)

        upgradeDir = sys.argv[1]
        VersionTool.init(upgradeDir)

        romVersion = sys.argv[2]
        if n == 3:
            # No UPGRADE_VERSION is present ,use the latest
            upgradeVersion = VersionTool.getLatestVersion()
        elif n >= 4:
            upgradeVersion = sys.argv[3]

        Upgrade().run(romVersion, upgradeVersion)

    @staticmethod
    def usage():
        print "Usage: upgrade.py UPGRADE_DIR ROM_VERSION [UPGRADE_VERSION]"
        print "        - UPGRADE_DIR: directory that contains upgrade patches (e.g. reference/autopatch/upgrade)"
        print "        - ROM_VERSION: current version (e.g. ROM35)"
        print "        - UPGRADE_VERSION: version that upgrade to (e.g. ROM39)."
        print "                           if not present, will upgrade to the latest available"


class Config:
    """
    Configuration.
    """

    UPGRADE_DIR = sys.path[0] + "/upgrade/"

class Upgrade:


    def run(self, oldVersion, newVersion):
        """
        Upgrade from old version to new version
        """

        oldVersion = VersionTool.toVersionDigit(oldVersion)
        newVersion = VersionTool.toVersionDigit(newVersion)

        curVersion = oldVersion
        for versionName in VersionTool.mVersions:
            if curVersion >= newVersion:
                break;

            if curVersion < VersionTool.toVersionDigit(versionName):
                self.applyPatch(versionName)
                curVersion += 1

    def applyPatch(self, versionName):
        patchDir = Config.UPGRADE_DIR + versionName + "/"
        patchXML = VersionTool.getPatch(versionName)
        print "\n>>> " + versionName + " patches ..."
        autopatch.AutoPatch.apply(patchDir, patchXML)


class VersionTool:

    mVersions = []

    @staticmethod
    def init(upgradeDir):
        Config.UPGRADE_DIR = upgradeDir
        subdirs = os.listdir(Config.UPGRADE_DIR)
        for subdir in subdirs:
            if subdir.startswith("ROM"):
                VersionTool.mVersions.append(subdir)

        VersionTool.mVersions.sort(cmp=VersionTool.comparator);
        pass

    @staticmethod
    def getLatestVersion():
        size = len(VersionTool.mVersions)
        return VersionTool.mVersions[size-1]

    @staticmethod
    def getPatch(versionName):
        # Compose the path of patch
        return Config.UPGRADE_DIR + versionName + "/" + versionName + ".xml"

    @staticmethod
    def comparator(versionName1, versionName2):
        """
        Comparator to sort the version name.
        version name is like ROM39, ROM40, etc.
        """

        version1 = VersionTool.toVersionDigit(versionName1)
        version2 = VersionTool.toVersionDigit(versionName2)
        return version1 - version2

    @staticmethod
    def toVersionDigit(versionName):
        version = filter(str.isdigit, versionName)
        return string.atoi(version)



if __name__ == "__main__":
    Main()
