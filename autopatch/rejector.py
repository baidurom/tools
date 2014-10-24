#!/usr/bin/python

### File Information ###
"""
Rejector
"""

__author__ = 'duanqz@gmail.com'


import os
import fnmatch
from config import Config



class Rejector:
    """ Rejector:
        1. Check whether conflicts happen.
        2. Resolve conflicts automatically.
    """

    CONFILCT_START = "<<<<<<<"
    CONFLICT_MID   = "======="
    CONFILCT_END   = ">>>>>>>"

    def __init__(self, target):
        self.mTarget = target
        self.mConflictNum = 0

    def getConflictNum(self):
        if   fnmatch.fnmatch(self.mTarget, "*.xml"):
            self.resolveConflict()
        elif fnmatch.fnmatch(self.mTarget, "*.smali"):
            self.collectConflict()

        return self.mConflictNum

    def collectConflict(self):
        """ Check whether conflict happen or not in the target
        """

        self.mConflictNum = 0

        top = 0
        size = 0

        # delLinesNumbers record the lines of conflicts
        delLineNumbers = []
        needToDel = False

        targetFile = open(self.mTarget, "r+")

        lineNum = 0
        lines = targetFile.readlines()

        for line in lines:
            size = self.mConflictNum
            if line.startswith(Rejector.CONFILCT_START):

                top += 1

                # Modify the conflict in the original
                lines[lineNum] = "%s #Conflict %d\n" % (line.rstrip(), size)
                self.mConflictNum += 1

                #conflicts.append("#Conflict %d , start at line %d\n" % (size, lineNum))
                #conflicts[size] += line

                delLineNumbers.append(lineNum)

            elif line.startswith(Rejector.CONFILCT_END):

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

                    if line.startswith(Rejector.CONFLICT_MID):
                        # Modify the conflict in the original
                        lines[lineNum] = "%s #Conflict %d\n" % (line.rstrip(), size-top)
                        needToDel = True

                    if needToDel:
                        delLineNumbers.append(lineNum)

            lineNum += 1


        # Create a reject file if conflict happen
        if self.mConflictNum > 0:
            rejFilename = Rejector.createReject(self.mTarget)
            rejFile = open(rejFilename, "wb")
            rejFile.writelines(lines)
            rejFile.close()


        # Remove conflict blocks, and write back target.
        for lineNum in delLineNumbers[::-1]:
            del lines[lineNum]

        targetFile.seek(0)
        targetFile.truncate()
        targetFile.writelines(lines)
        targetFile.close()

        return self

    @staticmethod
    def createReject(target):
        relTarget = os.path.relpath(target, Config.PRJ_ROOT)
        rejFilename = os.path.join(Config.REJ_ROOT, relTarget)
        dirname = os.path.dirname(rejFilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return rejFilename


    def resolveConflict(self):

        rejFileHandle = open(self.mTarget, "r+")

        top = 0
        lineNum = 0

        delLineNumbers = []
        needToDel = True

        lines = rejFileHandle.readlines()
        for line in lines:
            if line.startswith(Rejector.CONFILCT_START):
                top += 1
                delLineNumbers.append(lineNum)

            elif line.startswith(Rejector.CONFILCT_END):
                top -= 1
                delLineNumbers.append(lineNum)
                needToDel = True

                if top < 0: break;
            else:
                if top > 0:
                    if needToDel:
                        delLineNumbers.append(lineNum)

                    if line.startswith(Rejector.CONFLICT_MID):
                        needToDel = False

            lineNum += 1

        for lineNum in delLineNumbers[::-1]:
            del lines[lineNum]

        rejFileHandle.seek(0)
        rejFileHandle.truncate()
        rejFileHandle.writelines(lines)
        rejFileHandle.close()
