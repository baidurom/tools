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


class AutoPatchXML:
    """ Represent the tree model of the patch XML.
    """

    def parse(self):
        """ Parse the XML with the schema defined in autopatch.xsd
        """

        XMLDom = ET.parse(Config.PATCH_XML)
        for feature in XMLDom.findall('feature'):
            self.handleRevise(feature)

    def handleRevise(self, feature):
        """ Parse the revise node to handle the revise action.
        """

        require = feature.attrib['require']
        description = feature.attrib['description']

        if require == "MUST":
            Log.i("\n>>> [M] " + description)
            for revise in feature:
                ReviseExecutor(revise).run()
 
        elif Config.REVISE_OPTION and require == "OPTION":
            Log.i("\n>>> [O] " + description)
            for revise in feature:
                ReviseExecutor(revise).run()

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


    def run(self):
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
            Log.fail("File not exist. " + source)
            return

        if os.path.exists(target):
            Log.i(" REPLACE  " + target)
        else:
            Log.i(" ADD      " + target)
            self.createIfNotExist(os.path.dirname(target))

        shutil.copy(source, target)

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
            Log.fail("File not exist " + self.mTarget)
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
