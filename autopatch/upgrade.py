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


        Config.UPGRADE_XML_DIR = sys.argv[1]
        romVersion = sys.argv[2]
        upgradePatch = UpgradePatch()
        if n == 3:
            # No UPGRADE_VERSION is present ,use the latest
            upgradeVersion = upgradePatch.getLatestPatch()
        elif n >= 4:
            upgradeVersion = sys.argv[3]

        Upgrade(upgradePatch).run(romVersion, upgradeVersion)

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

    UPGRADE_XML_DIR = sys.path[0] + "/upgrade/"


class Upgrade:

    versions = []

    def __init__(self, upgradePatch):
        self.initVersions(upgradePatch)

    def initVersions(self, upgradePatch):
        """
        Initial an array of version numbers from upgrade patch
        """

        for item in upgradePatch.patches:
            version = VersionTool.toVersion(item)
            self.versions.append(version)

    def run(self, oldVersion, newVersion):
        """
        Upgrade from old version to new version
        """

        oldVersion = VersionTool.toVersion(oldVersion)
        newVersion = VersionTool.toVersion(newVersion)

        curVersion = oldVersion
        for version in self.versions:
            if curVersion >= newVersion:
                break;

            if curVersion < version:
                self.processRevision(version)
                curVersion += 1

    def processRevision(self, version):
        patchXML = VersionTool.toFilename(version)
        autopatch.AutoPatch.apply(Config.UPGRADE_XML_DIR, patchXML)


class UpgradePatch:
    """
    Patch of upgrade. These patches are in the directory of UPGRADE_XML_DIR.
    """

    patches = []

    def __init__(self):
        files = os.listdir(Config.UPGRADE_XML_DIR)
        for f in files:
            splitFilename = os.path.splitext(f)
            if splitFilename[1] == ".xml":
                self.patches.append(f)

        self.patches.sort(cmp=VersionTool.comparator);
        pass

    def getLatestPatch(self):
        size = len(self.patches)
        return self.patches[size-1]


class VersionTool:
    """
    Tool to handle version format
    """

    @staticmethod
    def comparator(filename1, filename2):
        """
        Comparator to sort the filename contains version number.
        """

        version1 = VersionTool.toVersion(filename1)
        version2 = VersionTool.toVersion(filename2)
        return version1 - version2

    @staticmethod
    def toVersion(filename):
        version = filter(str.isdigit, filename)
        return string.atoi(version)

    @staticmethod
    def toFilename(version):
        # TODO. Traverse the UPGRADE_XML_DIR to find the filename
        return Config.UPGRADE_XML_DIR + ("ROM%s.xml" % version)

if __name__ == "__main__":
    Main()