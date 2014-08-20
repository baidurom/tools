#!/usr/bin/python
# Filename: autopatch.py

"""
Patch the files automatically based on the autopatch.xsd.

Usage: $autopatch.py [OPTIONS]
              OPTIONS:
                --patchall, -p : Patch all the changes
                --upgrade,  -u : Patch the upgrade changes
                --porting,  -t : Porting changes from the other device

                Loosely, make sure you have prepared the autopatch directory by your self
                --patchall-loose, -pl : Patch all the changes loosely, not update AOSP and BOSP again
                --upgrade-loose,  -ul : Patch all the changes loosely, not update LAST_BOSP and BOSP again
"""

__author__ = 'duanqz@gmail.com'



import shutil
import os, sys
import fnmatch
import traceback

from diff_patch import DiffPatch
from target_finder import TargetFinder
from config import Config
from error import Error
from rejector import Rejector
from precondition import preparePatchall, prepareUpgrade, preparePorting

from formatters.format import Format
from formatters.log import Paint


try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


TAG="autopatch"


class AutoPatch:


    def __init__(self, targetRoot, olderRoot, newerRoot, patchXML):
        AutoPatch.TARGET_ROOT = targetRoot
        AutoPatch.OLDER_ROOT  = olderRoot
        AutoPatch.NEWER_ROOT  = newerRoot
        AutoPatch.PATCH_XML   = patchXML


    def run(self):
        # Parse out the PATCH_XML
        AutoPatchXML().parse()

        Error.report()

# End of class AutoPatch


class AutoPatchXML:
    """ Represent the tree model of the patch XML.
    """

    def parse(self):
        """ Parse the XML with the schema defined in autopatch.xsd
        """

        XMLDom = ET.parse(AutoPatch.PATCH_XML)

        for feature in XMLDom.findall('feature'):
            self.handleRevise(feature)


    def handleRevise(self, feature):
        """ Parse the revise node to handle the revise action.
        """

        description = feature.attrib['description']

        print "\n [%s]" % description
        for revise in feature:
            ReviseExecutor(revise).run()

# End of class AutoPatchXML


class ReviseExecutor:
    """ Execute revise action to a unique file.
        Actions including ADD, MERGE, REPLACE. 
    """

    ADD     = "ADD"
    MERGE   = "MERGE"
    DELETE  = "DELETE"
    REPLACE = "REPLACE"

    TARGET_FINDER = TargetFinder()

    def __init__(self, revise):
        """ @args revise: the revise XML node.
        """

        self.action = revise.attrib['action']

        # Compose the source and target file path
        target = revise.attrib['target']
        self.mTarget = target
        self.mOlder  = os.path.join(AutoPatch.OLDER_ROOT,  target)
        self.mNewer  = os.path.join(AutoPatch.NEWER_ROOT,  target)


    def run(self):
        if   os.path.isfile(self.mNewer) or os.path.isfile(self.mOlder):
            self.singleAction(self.mTarget, self.mOlder, self.mNewer)

        elif os.path.isdir(self.mNewer): self.handleDirectory(self.mNewer)
        elif os.path.isdir(self.mOlder): self.handleDirectory(self.mOlder)

        elif self.mNewer.endswith("*"): self.handleRegex(self.mNewer)
        elif self.mOlder.endswith("*"): self.handleRegex(self.mOlder)

        else:
            print Paint.red("  Can not handle : %s" % self.mTarget)


    def handleDirectory(self, directory):
        """ Handle target is a directory
        """

        if   directory.startswith(AutoPatch.OLDER_ROOT):
            relpathStart = AutoPatch.OLDER_ROOT
        elif directory.startswith(AutoPatch.NEWER_ROOT):
            relpathStart = AutoPatch.NEWER_ROOT

        for (dirpath, dirnames, filenames) in os.walk(directory):

            dirnames = dirnames # No use, just avoid of warning

            for filename in filenames:
                path =  os.path.join(dirpath, filename)

                target = os.path.relpath(path, relpathStart)
                older  = os.path.join(AutoPatch.OLDER_ROOT,  target)
                newer  = os.path.join(AutoPatch.NEWER_ROOT,  target)

                self.singleAction(target, older, newer)


    def handleRegex(self, regex):
        """ Handle target ends with *
        """

        targetdir = os.path.dirname(self.mTarget)
        olderdir  = os.path.dirname(self.mOlder)
        newerdir  = os.path.dirname(self.mNewer)

        regexdir = os.path.dirname(regex)
        regexbase = os.path.basename(regex)

        # Match the filename in the directory
        for filename in os.listdir(regexdir):
            if fnmatch.fnmatch(filename, regexbase):
                target = os.path.join(targetdir, filename)
                older  = os.path.join(olderdir,  filename)
                newer  = os.path.join(newerdir,  filename)

                self.singleAction(target, older, newer)


    def singleAction(self, target, older, newer):
        """ action for a single file
        """

        try:
            if   self.action == ReviseExecutor.ADD:     result = ReviseExecutor.singleReplaceOrAdd(target, newer)
            elif self.action == ReviseExecutor.MERGE:   result = ReviseExecutor.singleMerge(target, older, newer)
            elif self.action == ReviseExecutor.DELETE:  result = ReviseExecutor.singleDelete(target)
            elif self.action == ReviseExecutor.REPLACE: result = ReviseExecutor.singleReplaceOrAdd(target, newer)

            print result
        except:
            Error.fail("  * Failed to %s  %s" % (self.action, target))
            traceback.print_exc()


    @staticmethod
    def singleReplaceOrAdd(target, source):
        """ Add a file from source to target.
            Replace the target if exist.
        """

        # Find out the actual target
        target = ReviseExecutor.TARGET_FINDER.find(target)

        if os.path.exists(target):
            execute = "REPLACE  " + target
        else:
            execute = "    ADD  " + target
            ReviseExecutor.createIfNotExist(os.path.dirname(target))

        if not os.path.exists(source):
            Error.fileNotFound(source)

            return "%s %s" % (Paint.red("  [FAIL]"), execute)

        # Only format access method and res id
        action = Format.ACCESS_TO_NAME | Format.RESID_TO_NAME
        formatSource = Format(AutoPatch.NEWER_ROOT, source).do(action)
        formatTarget = Format(AutoPatch.TARGET_ROOT, target).do(action)

        shutil.copy(source, target)

        # Would not change res name back
        action = Format.ACCESS_TO_NAME
        formatSource.undo(action)
        formatTarget.undo(action)

        return "%s %s" % (Paint.green("  [PASS]"), execute)


    @staticmethod
    def singleMerge(target, older, newer):
        """ Incorporate changes from older to newer into target
        """

        # Find out the actual target loosely
        target = ReviseExecutor.TARGET_FINDER.find(target, loosely=True)

        execute = "  MERGE  " + target

        if not os.path.exists(target) :
            Error.fileNotFound(target)
            return "%s %s" % (Paint.red("  [FAIL]"), execute)

        action = Format.REMOVE_LINE | Format.ACCESS_TO_NAME | Format.RESID_TO_NAME
        formatTarget = Format(AutoPatch.TARGET_ROOT, target).do(action)
        formatOlder  = Format(AutoPatch.OLDER_ROOT,  older).do(action)
        formatNewer  = Format(AutoPatch.NEWER_ROOT,  newer).do(action)

        DiffPatch(target, older, newer).run()

        # Would not change res name back
        action = Format.REMOVE_LINE | Format.ACCESS_TO_NAME
        formatTarget.undo(action)
        formatOlder.undo(action)
        formatNewer.undo(action)

        conflictNum = Rejector(target).getConflictNum()

        if conflictNum > 0 :
            Error.conflict(conflictNum, target)
            return "%s %s" % (Paint.yellow("  [CFLT]"), execute)
        else:
            return "%s %s" % (Paint.green("  [PASS]"), execute)


    @staticmethod
    def singleDelete(target):
        """ delete the target
        """

        # Find out the actual target
        target = ReviseExecutor.TARGET_FINDER.find(target)

        execute = " DELETE  " + target

        if os.path.exists(target):
            os.remove(target)
            return "%s %s" % (Paint.green("  [PASS]"), execute)

        return "%s %s" % (Paint.red("  [FAIL]"), execute)


    @staticmethod
    def createIfNotExist(dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)


# End of class ReviseExecutor


def patchall(loose=False):
    if not loose: preparePatchall()

    AutoPatch(Config.PRJ_ROOT, Config.AOSP_ROOT, Config.BOSP_ROOT, Config.PATCHALL_XML).run()


def upgrade(loose=False):
    if not loose: prepareUpgrade()

    AutoPatch(Config.PRJ_ROOT, Config.LAST_BOSP_ROOT, Config.BOSP_ROOT, Config.UPGRADE_XML).run()


def porting(argv):
    (olderRoot, newerRoot) = preparePorting(argv)

    AutoPatch(Config.PRJ_ROOT, olderRoot, newerRoot, Config.PORTING_XML).run()




if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2:
        print __doc__
        sys.exit(0)

    arg1 = sys.argv[1]
    if   arg1 in ("--patchall,-p"): patchall()
    elif arg1 in ("--upgrade, -u"): upgrade()
    elif arg1 in ("--porting, -t"): porting(sys.argv[2:])
    elif arg1 in ("--patchall-loose, -pl"): patchall(loose=True)
    elif arg1 in ("--upgrade-loose,  -ul"): upgrade(loose=True)

