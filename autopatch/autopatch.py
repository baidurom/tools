#!/usr/bin/python
# Filename: autopatch.py

### File Information ###
"""
Patch the files automatically based on the autopatch.xsd.

Usage: $shell autopatch.py [PATCH_XML]
            - PATCH_XML  : The patch XML definition. Default to be bringup.xml
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'



import os.path
import shutil
import sys
import fnmatch
import traceback
from diff_patch import DiffPatch
from xml_patch import Patcher as XMLPatcher
from target_finder import TargetFinder
from config import Config
from log import Log
from format import Format

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET



class AutoPatch:

    def __init__(self):

        # Parse out the PATCH_XML
        AutoPatchXML().parse()

        Log.conclude()

# End of class AutoPatch


class Version:
    """ Version control for file
    """

    ANDROID_4_0 = 1
    ANDROID_4_1 = ANDROID_4_0 << 1
    ANDROID_4_2 = ANDROID_4_1 << 1
    ANDROID_4_3 = ANDROID_4_2 << 1
    ANDROID_4_4 = ANDROID_4_3 << 1


    CURRENT_VERSION = ~0

    @staticmethod
    def parseCurrentVersion(patchXML):
        """ Parse out current version from the patch XML
        """

        try:
            Version.CURRENT_VERSION = Version.parse(patchXML.getroot().attrib['version'])
        except KeyError:
            pass

    @staticmethod
    def parse(versionStr):
        versionInt = 0
        for version in versionStr.split("|"):
            if version == "4.0" : versionInt |= Version.ANDROID_4_0
            if version == "4.1" : versionInt |= Version.ANDROID_4_1
            if version == "4.2" : versionInt |= Version.ANDROID_4_2
            if version == "4.3" : versionInt |= Version.ANDROID_4_3
            if version == "4.4" : versionInt |= Version.ANDROID_4_4

        Log.d("Version is %d" % versionInt);
        return versionInt

    @staticmethod
    def match(versionStr):
        if versionStr != None:
            version = Version.parse(versionStr)
        else:
            version = Version.CURRENT_VERSION

        return Version.CURRENT_VERSION & version

class AutoPatchXML:
    """ Represent the tree model of the patch XML.
    """

    def parse(self):
        """ Parse the XML with the schema defined in autopatch.xsd
        """

        XMLDom = ET.parse(Config.PATCH_XML)

        Version.parseCurrentVersion(XMLDom)

        for feature in XMLDom.findall('feature'):
            self.handleRevise(feature)

    def handleRevise(self, feature):
        """ Parse the revise node to handle the revise action.
        """

        require = feature.attrib['require']
        description = feature.attrib['description']

        if self.needRevise(require):
            Log.i("\n [%s]" % description)
            for revise in feature:
                ReviseExecutor(revise).run()

    def needRevise(self, require):
        if   require == "MUST"   : require = Config.MUST
        elif require == "OPTION" : require = Config.OPTION
        elif require == "IGNORE" : require = Config.IGNORE

        return require & Config.REQUIRE

# End of class AutoPatchXML


class ReviseExecutor:
    """ Execute revise action to a unique file.
        Actions including ADD, MERGE, REPLACE. 
    """

    ADD     = "ADD"
    MERGE   = "MERGE"
    REPLACE = "REPLACE"

    def __init__(self, revise):
        """ @args revise: the revise XML node.
        """

        self.action = revise.attrib['action']

        # Compose the source and target file path
        target = revise.attrib['target']
        self.mOldSrc = os.path.join(Config.OLDER_DIR, target)
        self.mNewSrc = os.path.join(Config.NEWER_DIR, target)
        self.mTarget = TargetFinder().find(target)

        # Initialize patch if defined
        try: 
            patch = revise.attrib['patch']
            self.mPatch = os.path.join(Config.PATCH_XML_DIR, patch)
        except KeyError:
            self.mPatch = None

        # Initialize version if defined
        try:
            self.mVersion = revise.attrib['version']
        except KeyError:
            self.mVersion = None


    def run(self):
        if Version.match(self.mVersion) == False:
            return

        try:
            if   self.action == ReviseExecutor.ADD:     self.add()
            elif self.action == ReviseExecutor.REPLACE: self.replace()
            elif self.action == ReviseExecutor.MERGE:   self.merge()
        except:
            Log.fail("Failed to " + self.action + "  " + self.mTarget)
            traceback.print_exc()

    def add(self):
        self.replaceOrAddSingleFile(self.mNewSrc, self.mTarget)

    def replaceOrAddSingleFile(self, source, target):
        """ Add a file from source to target.
            Replace the target if exist.
        """

        if not os.path.exists(source):
            Log.fail("File not exist: " + source)
            return

        if os.path.exists(target):
            Log.i(" REPLACE  " + target)
        else:
            Log.i(" ADD      " + target)
            self.createIfNotExist(os.path.dirname(target))

        action = Format.REMOVE_LINE | Format.ACCESS_TO_NAME | Format.RESID_TO_NAME
        formatTarget = Format(Config.NEWER_DIR, source).do(action)
        shutil.copy(source, target)
        formatTarget.undo()

    def createIfNotExist(self, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def replace(self):
        if self.mNewSrc.endswith("*") :
            # Replace all the files match the prefix

            # List all the file in directory
            sourcedir = os.path.dirname(self.mNewSrc)
            basename = os.path.basename(self.mNewSrc)

            targetdir = os.path.dirname(self.mTarget)
            # Match the filename in the directory
            for filename in os.listdir(sourcedir):
                if fnmatch.fnmatch(filename, basename):
                    source = os.path.join(sourcedir, filename)
                    target = os.path.join(targetdir, filename)

                    newTarget = TargetFinder().find(target)
                    self.replaceOrAddSingleFile(source, newTarget)
        else:
            self.add()

    def merge(self): 
        if not os.path.exists(self.mTarget):
            Log.fail("File not exist: " + self.mTarget)
            return

        Log.i(" MERGE    " + self.mTarget)

        if self.mPatch == None:
            # Compare OLDER and NEWER, then patch onto target.
            if not DiffPatch(self.mTarget, self.mOldSrc, self.mNewSrc).run():
                # Collect the reject file of target
                Log.reject(self.mTarget)
                pass

        elif os.path.exists(self.mPatch):
            # Directly patch onto target by patch defined
            if not XMLPatcher(self.mTarget, self.mPatch).run():
                Log.reject(self.mTarget)
                pass
        else:
            Log.fail("Patch not exists " + self.mPatch)

# End of class ReviseExecutor


# End of class Log

if __name__ == "__main__":
    Config.setup(sys.argv[1:])
    AutoPatch()
