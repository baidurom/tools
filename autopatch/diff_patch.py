#!/usr/bin/python

### File Information ###
"""
Incorporate changes from older to newer into target.
"""

__author__ = 'duanqz@gmail.com'


import os
import commands
import shutil
import fnmatch

from os import sys, path
from config import Config, Log

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from smaliparser.Smali import Smali
from accessmethod.name2num import NameToNumForOneFile
from accessmethod.num2name import NumToNameForOneFile



class DiffPatch():

    TARGET_OUT = os.path.join(Config.PRJ_ROOT, "target")
    OLDER_OUT  = os.path.join(Config.PRJ_ROOT, "older")
    NEWER_OUT  = os.path.join(Config.PRJ_ROOT, "newer")

    def __init__(self, target, older, newer):
        self.mTarget = target
        self.mOlder  = older
        self.mNewer  = newer
        pass

    def run(self):
        if not os.path.exists(self.mTarget) or \
           not os.path.exists(self.mOlder)  or \
           not os.path.exists(self.mNewer)  :
            return True

        # Do NOT split XML
        if fnmatch.fnmatch(self.mTarget, "*.xml"):
            return DiffPatch.__shellDiff3(self.mTarget, self.mOlder, self.mNewer)

        return self.diff3()

    def diff3(self):
        """ Incorporate changes from older to newer into target.
            Return True if no conflicts, otherwise return False.
        """

        noConflict = True

        DiffPatch.prepare()

        # Access method number to name
        targetReverse = NumToNameForOneFile(self.mTarget)
        olderReverse  = NumToNameForOneFile(self.mOlder)
        newerReverse  = NumToNameForOneFile(self.mNewer)


        # Split the target, older and newer
        targetSplitter = Splitter().split(self.mTarget, DiffPatch.TARGET_OUT)
        olderSplitter  = Splitter().split(self.mOlder,  DiffPatch.OLDER_OUT)
        newerSplitter  = Splitter().split(self.mNewer,  DiffPatch.NEWER_OUT)

        # Patch partitions one by one
        for newerPart in newerSplitter.getAllParts():
            targetPart = targetSplitter.match(newerPart)
            olderPart  = olderSplitter.match(newerPart)

            if not os.path.exists(olderPart) and \
               not os.path.exists(targetPart):
                targetSplitter.appendPart(newerPart)
                continue
 
            noConflict &= DiffPatch.__shellDiff3(targetPart, olderPart, newerPart)

        # Join the partitions
        targetSplitter.join()

        # Access method name to number
        NameToNumForOneFile(targetReverse)
        NameToNumForOneFile(olderReverse)
        NameToNumForOneFile(newerReverse)
 
        DiffPatch.clean()

        if not noConflict: Log.d("  [Conflict happened]")
        return noConflict

    @staticmethod
    def __shellDiff3(target, older, newer):
        """ Using shell diff3.
            Return True if no conflict, otherwise return False
        """

        (targetNoLine, targetPatch) = Utils.remLines(target)
        olderNoLine  = Utils.remLines(older)[0]
        newerNoLine = Utils.remLines(newer)[0]

        # Exit status is 0 if successful, 1 if conflicts, 2 if trouble
        cmd = "diff3 -E -m -L VENDOR %s -L AOSP %s -L BOSP %s" % \
                (commands.mkarg(targetNoLine), commands.mkarg(olderNoLine), commands.mkarg(newerNoLine))
        (status, output) = commands.getstatusoutput(cmd)

        if status != 2:
            # Write back the patched file
            targetFile = open(target, "wb")
            targetFile.write("%s\n" % output)
            targetFile.close()
 
        Utils.addLines(target, targetPatch)
        if fnmatch.fnmatch(target, "*.xml"):
            os.remove(targetNoLine)
            os.remove(targetPatch)
 
        return status == 0

    @staticmethod
    def prepare():
        for tmpDir in (DiffPatch.TARGET_OUT, DiffPatch.OLDER_OUT, DiffPatch.NEWER_OUT):
            if not os.path.exists(tmpDir): os.makedirs(tmpDir)

    @staticmethod
    def clean():
        for tmpDir in (DiffPatch.TARGET_OUT, DiffPatch.OLDER_OUT, DiffPatch.NEWER_OUT):
            shutil.rmtree(tmpDir)


class Splitter:
    """ Splitter of smali file
    """

    def __init__(self):
        pass

    def split(self, origSmali, output=None):
        """ Split the original smali file into partitions
        """

        if output == None: output = os.path.dirname(origSmali)

        self.mOrigSmali = origSmali
        self.mOutput    = output
        self.mPartList  = Smali(origSmali).split(self.mOutput)

        return self

    def match(self, part):
        basename = os.path.basename(part)
        return os.path.join(self.mOutput, basename)

    def getAllParts(self):
        return self.mPartList

    def appendPart(self, part):
        """ Append a part to list.
        """

        try:
            self.mPartList.index(part)
        except:
            Log.d("  [Add new part] " + part)
            self.mPartList.append(part)

    def join(self):
        """ Join all the partitions.
        """

        newSmali = open(self.mOrigSmali, "wb")

        # Write back the part by sequence
        for part in self.mPartList:
            if not os.path.exists(part):
                continue

            partHandle = open(part ,"rb")
            newSmali.write(partHandle.read())
            partHandle.close()

        newSmali.close()

        return self

class Utils:

    NOLINE_SUFFIX = ".noline"
    LINEPATCH_SUFFIX = ".linepatch"

    @staticmethod
    def remLines(origFile):
        """ Remove lines in original file
        """

        noLineFile = origFile + Utils.NOLINE_SUFFIX

        # Generate no line file
        cmd = "cat %s | sed -e '/^\s*\.line.*$/d' | sed -e 's/\/jumbo//' > %s" % \
                (commands.mkarg(origFile), commands.mkarg(noLineFile))
        commands.getstatusoutput(cmd)

        # Generate line patch
        linesPatch = origFile + Utils.LINEPATCH_SUFFIX
        cmd = "diff -B -u %s %s > %s" % \
                (commands.mkarg(noLineFile), commands.mkarg(origFile), commands.mkarg(linesPatch))
        commands.getstatusoutput(cmd)

        return noLineFile, linesPatch

    @staticmethod
    def addLines(noLineFile, linesPatch):
        """ Add the lines back to no line file
        """

        # Patch the lines to no line file
        cmd = "patch -f %s -r /dev/null < %s > /dev/null" % \
                (commands.mkarg(noLineFile), commands.mkarg(linesPatch))
        commands.getstatusoutput(cmd)

        return noLineFile


if __name__ == "__main__":
    target = "/media/source/smali/smali-4.2/devices/p6/framework.jar.out/smali/android/content/res/AssetManager.smali"
    older  = "/media/source/smali/smali-4.2/devices/p6/autopatch/aosp/framework.jar.out/smali/android/content/res/AssetManager.smali"
    newer  = "/media/source/smali/smali-4.2/devices/p6/autopatch/bosp/framework.jar.out/smali/android/content/res/AssetManager.smali"
    DiffPatch().diff3(target, older, newer)
