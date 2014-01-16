#!/usr/bin/python
# Filename: autopatch.py

### File Information ###
"""
Patch the files automatically based on the autopatch.xsd.

Usage: $shell autopatch.py
         Use the default baidu_patch.xml

       $shell autopatch.py path_to_patch.xml
         To provide a patch.xml, should firstly referenced to
         the XML schema autopatch.xsd
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'



### import block ###

import commands
import os.path
import shutil
import sys
import ApplyPatch

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET



### Class definition ###

class AutoPatch:
    """
    Entry of the script.
    """

    def __init__(self):
        argLen = len(sys.argv)
        if argLen == 1:
            patchesDir = Config.PATCHES_DIR
            patchXML = Config.DEFAULT_REVISION_XML
        elif argLen == 2:
            patchesDir = Config.PATCHES_DIR
            patchXML = sys.argv[1]
        elif argLen >= 3:
            patchesDir = sys.argv[1]
            patchXML = sys.argv[2]

        AutoPatch.apply(patchesDir, patchXML)

    @staticmethod
    def apply(patchesDir, patchXML):
        Config.PATCHES_DIR = patchesDir
        AutoPatchXML().parse(patchXML)
        pass

# End of class Main

class Config:
    """
    Configuration.
    """
    DEBUG = False

    PROJECT_DIR = os.getcwd() + "/"
    SCRIPT_DIR = sys.path[0] + "/"

    # Default patch.xml to be parsed
    DEFAULT_REVISION_XML = PROJECT_DIR + "demo_patch.xml"

    # Source and destination directory holding the file to be handled
    SOURCE_DIR = PROJECT_DIR + "baidu/smali/"
    TARGET_DIR = PROJECT_DIR

    # Patches directory
    PATCHES_DIR = PROJECT_DIR + "patches/"

    # Whether to revise OPTION feature, default to be True
    REVISE_OPTION = True

    @staticmethod
    def initConfigFrom(XMLDom):
        """
        Initialize configuration from XML document.
        """

        try:
            config = XMLDom.find('config')
        except AttributeError:
            Log.i("Using default configuration")
            return

        sourceDir = Config.findAttrib(config, 'source_dir')
        if sourceDir != None:
            Config.SOURCE_DIR = sourceDir.text

        targetDir = Config.findAttrib(config, 'target_dir')
        if targetDir != None:
            Config.SOURCE_DIR = targetDir.text

        patchesDir = Config.findAttrib(config, 'patches_dir')
        if patchesDir != None:
            Config.PATCHES_DIR = patchesDir.text

        reviseOption = Config.findAttrib(config, 'revise_option')
        if reviseOption != None:
            Config.REVISE_OPTION = reviseOption.text

    @staticmethod
    def findAttrib(config, attribKey):
        try:
            return config.find(attribKey)
        except AttributeError:
            return None

    @staticmethod
    def toString():
        Log.i("--------------------------------------------")
        Log.i("Source_Dir\t=\t" + Config.SOURCE_DIR)
        Log.i("Target_Dir\t=\t" + Config.TARGET_DIR)
        Log.i("Patches_Dir\t=\t" + Config.PATCHES_DIR)
        Log.i("--------------------------------------------")

# End of class Config


class AutoPatchXML:
    """
    Represent the tree of an input XML.
    """

    def __init__(self):
        pass

    def parse(self, autoPatchXML):
        """
        Parse the XML with the schema defined in autopatch.xsd
        """

        XMLDom = ET.parse(autoPatchXML)
        Config.initConfigFrom(XMLDom)
        #Config.toString()

        for feature in XMLDom.findall('feature'):
            self.handleRevise(feature)

        self.showRejectFilesIfNeeded()

    def handleRevise(self, feature):
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

    def showRejectFilesIfNeeded(self):
        rejectDir = Config.PROJECT_DIR + "out/reject/"
        if os.path.exists(rejectDir) == False:
            return

        rejectFiles = os.listdir(rejectDir)
        if len(rejectFiles) > 0:
            Log.i("\nThere are reject files in " +  rejectDir + ", please check it out!")
            Log.i(rejectFiles)
            Log.i("\n")
# End of class Revision


class ReviseExecutor:
    """
    Execute revise.
    """

    ADD = "ADD"
    MERGE = "MERGE"
    REPLACE = "REPLACE"
    ROUTINE = "ROUTINE"

    def __init__(self, revise):
        """
        @args revise: the revise XML node.
        """

        self.action = revise.attrib['action']

        # Compose the source and target file path
        target = revise.attrib['target']
        self.mSource = Config.SOURCE_DIR + target
        self.mTarget = Config.TARGET_DIR + target

        try: 
            patch = revise.attrib['patch']
            self.mPatch = Config.PATCHES_DIR + patch
        except KeyError: pass

        try:
            routine =  revise.attrib['routine']
            self.mRoutine = Config.SCRIPT_DIR + routine
        except KeyError: pass


    def run(self):
        if self.action == ReviseExecutor.ADD:
            self.add()
        elif self.action == ReviseExecutor.REPLACE:
            self.replace()
        elif self.action == ReviseExecutor.MERGE:
            self.merge()
        elif self.action == ReviseExecutor.ROUTINE:
            self.routine()

    def add(self):
        if not self.checkExists(self.mSource) :
            return

        Log.i(" ADD  " + self.mTarget)
        shutil.copy(self.formatPath(self.mSource), \
                    self.formatPath(self.mTarget))

    def replace(self):
        if not self.checkExists(self.mSource) or \
           not self.checkExists(self.mTarget) :
            return

        Log.i(" REPLACE  " + self.mTarget)
        shutil.copy(self.formatPath(self.mSource), \
                    self.formatPath(self.mTarget))

    def merge(self):
        if not self.checkExists(self.mTarget) or \
           not self.checkExists(self.mPatch):
            return

        Log.i(" MERGE  " + self.mTarget)
        try:
            ApplyPatch.MergeExecutor(ReviseExecutor.formatPath(self.mTarget), \
                                     ReviseExecutor.formatPath(self.mPatch)).run()
        except: pass

    def routine(self):
        Log.i(" ROUTINE  " + self.mRoutine)
        result = commands.getstatusoutput(self.mRoutine)
        if result[0] != 0:
            Log.e(" Execute routine error.")

    @staticmethod
    def checkExists(filename):
        if os.path.exists(ReviseExecutor.formatPath(filename)):
            return True

        Log.w("File not exists. " + filename)
        return False

    @staticmethod
    def formatPath(path):
        return path.replace("\\", "")

# End of class Target


class Log:

    @staticmethod
    def d(message):
        if Config.DEBUG:
            print " " + message

    @staticmethod
    def i(message):
        print message

    @staticmethod
    def w(message):
        print "Waring: " + message

    @staticmethod
    def e(message):
        print "Error: " + message

# End of class Log

if __name__ == "__main__":
    AutoPatch()
