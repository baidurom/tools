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
from config import Config
from log import Log

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from smaliparser.Smali import Smali
from format import Format



class DiffPatch():

    TARGET_OUT = os.path.join(Config.PRJ_ROOT, "target")
    OLDER_OUT  = os.path.join(Config.PRJ_ROOT, "older")
    NEWER_OUT  = os.path.join(Config.PRJ_ROOT, "newer")

    def __init__(self, target, older, newer):
        self.mTarget = target
        self.mOlder  = older
        self.mNewer  = newer

    def run(self):
        if not os.path.exists(self.mTarget) or \
           not os.path.exists(self.mOlder)  or \
           not os.path.exists(self.mNewer)  :
            return True

        # Do NOT split XML
        if fnmatch.fnmatch(self.mTarget, "*.xml"):
            DiffPatch.__shellDiff3(self.mTarget, self.mOlder, self.mNewer)
            return self.checkConflict()

        return self.diff3()

    def diff3(self):
        """ Incorporate changes from older to newer into target.
            Return True if no conflicts, otherwise return False.
        """

        self.prepare()

        # Split the target, older and newer
        targetSplitter = Splitter().split(self.mTarget, DiffPatch.TARGET_OUT)
        olderSplitter  = Splitter().split(self.mOlder,  DiffPatch.OLDER_OUT)
        newerSplitter  = Splitter().split(self.mNewer,  DiffPatch.NEWER_OUT)

        # Patch partitions one by one
        for newerPart in newerSplitter.getAllParts():
            targetPart = targetSplitter.match(newerPart)
            olderPart  = olderSplitter.match(newerPart)

            if not os.path.exists(olderPart):
                if not os.path.exists(targetPart):
                    # newer not exist in target
                    targetSplitter.appendPart(newerPart)
                else:
                    # newer already exist in target
                    pass

                continue
            elif not os.path.exists(targetPart):
                # Target might be removed by vendor
                continue

            DiffPatch.__shellDiff3(targetPart, olderPart, newerPart)

        # Join the partitions
        targetSplitter.join()

        self.clean()

        return self.checkConflict()

    @staticmethod
    def __shellDiff3(target, older, newer):
        """ Using shell diff3.
        """

        # Exit status is 0 if successful, 1 if conflicts, 2 if trouble
        cmd = "diff3 -E -m -L VENDOR %s -L AOSP %s -L BOSP %s" % \
                (commands.mkarg(target), commands.mkarg(older), commands.mkarg(newer))
        (status, output) = commands.getstatusoutput(cmd)

        # Append "\n" to output for shell invoking result will miss it
        output += "\n"
 
        if status != 2:
            # Write back the patched file
            targetFile = open(target, "wb")
            targetFile.write(output)
            targetFile.close()

        return status == 0

    def prepare(self):
        for tmpDir in (DiffPatch.TARGET_OUT, DiffPatch.OLDER_OUT, DiffPatch.NEWER_OUT):
            if not os.path.exists(tmpDir): os.makedirs(tmpDir)

        action = Format.REMOVE_LINE | Format.ACCESS_TO_NAME | Format.RESID_TO_NAME
        self.mFormatTarget = Format(Config.PRJ_ROOT, self.mTarget).do(action)
        self.mFormatOlder  = Format(Config.OLDER_DIR, self.mOlder).do(action)
        self.mFormatNewer  = Format(Config.NEWER_DIR, self.mNewer).do(action)

    def clean(self):
        self.mFormatTarget.undo()
        self.mFormatOlder.undo()
        self.mFormatNewer.undo()

        for tmpDir in (DiffPatch.TARGET_OUT, DiffPatch.OLDER_OUT, DiffPatch.NEWER_OUT):
            shutil.rmtree(tmpDir)

    def checkConflict(self):
        """ Check whether conflict happen or not in output
            Return True if no conflict happen. otherwise return False
        """

        CONFILCT_START = "<<<<<<<"
        CONFLICT_MID   = "======="
        CONFILCT_END   = ">>>>>>>"

        top = 0
        size = 0
        conflictCnt = 0
        delLineNumbers = []

        needToDel = False

        targetFile = open(self.mTarget, "r+")

        lineNum = 0
        lines = targetFile.readlines()

        for line in lines:
            size = conflictCnt
            if line.startswith(CONFILCT_START):

                top += 1

                # Modify the conflict in the original
                lines[lineNum] = "%s #Conflict %d\n" % (line.rstrip(),size)
                conflictCnt += 1

                #conflicts.append("#Conflict %d , start at line %d\n" % (size, lineNum))
                #conflicts[size] += line

                delLineNumbers.append(lineNum)

            elif line.startswith(CONFILCT_END):

                # Modify the conflict in the original
                lines[lineNum] = "%s #Conflict %d\n" % (line.rstrip(), size-top)

                #conflicts[size-top] += line
                #conflicts[size-top] += "#Conflict %d , end at line %d\n\n" % (size-top, lineNum)

                delLineNumbers.append(lineNum)
                needToDel = False

                if top == 0: break;
                top -= 1

            else:
                if top > 0:
                    #conflicts[size-top] += line

                    if line.startswith(CONFLICT_MID):
                        # Modify the conflict in the original
                        lines[lineNum] = "%s #Conflict %d\n" % (line.rstrip(), size-top)
                        needToDel = True

                    if needToDel:
                        delLineNumbers.append(lineNum)

            lineNum += 1


        # Create a reject file if conflict happen
        if conflictCnt > 0:
            Log.d("  [Conflict happened. Total %d ]" %conflictCnt)
            rejFilename = Config.createReject(self.mTarget)
            rejFile = open(rejFilename, "wb")
            rejFile.writelines(lines)
            rejFile.close()

        # Write back target
        for lineNum in delLineNumbers[::-1]:
            del lines[lineNum]

        targetFile.seek(0)
        targetFile.truncate()
        targetFile.writelines(lines)
        targetFile.close()

        return conflictCnt == 0

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
            Log.d("  [Add new part %s ] " % part)
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


if __name__ == "__main__":
    target = "/media/source/smali/smali-4.2/devices/p6/framework-res/AndroidManifest.xml"
    older  = "/media/source/smali/smali-4.2/devices/p6/autopatch/aosp/framework-res/AndroidManifest.xml"
    newer  = "/media/source/smali/smali-4.2/devices/p6/autopatch/bosp/framework-res/AndroidManifest.xml"
    DiffPatch(target, older, newer).run()
