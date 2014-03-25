#!/usr/bin/python


### File Information ###
"""
Rejector to collect reject files
"""

__author__ = 'duanqz@gmail.com'



import os.path
from config import Config, Log


class Rejector:
    """ Entity to collect information of reject files. 
    """

    CONFILCT_START = "<<<<<<<"
    CONFLICT_MID   = "======="
    CONFILCT_END   = ">>>>>>>"

    REJ_LIST = []

    @staticmethod
    def collect(target):
        """ Collect the reject file if exists
        """

        # Append target to reject list
        relTarget = os.path.relpath(target, Config.PRJ_ROOT)
        Rejector.REJ_LIST.append(relTarget)

        # Split the target to reject part
        parts = Rejector.splitToParts(target)

        # Combine parts again to generate the reject file
        rejFilename = os.path.join(Config.REJ_ROOT, relTarget + ".reject")
        dirname = os.path.dirname(rejFilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        Rejector.combimeFromParts(parts, rejFilename)

    @staticmethod
    def splitToParts(rejFilename):
        """ Split the reject file to parts.
            Use combine from parts to rebuild the reject file.
        """

        parts = []
        top = 0

        rejFile = open(rejFilename, "r+")
        lineNum = 0
        lines = rejFile.readlines()
        for line in lines:
            size = len(parts)
            if line.startswith(Rejector.CONFILCT_START):
                top += 1

                # Modify the conflict in the original
                lines[lineNum] = line.rstrip() + "  " + Rejector.extraConflict(size)

                # Append the conflict part
                line = line.rstrip() + Rejector.extraLineNum(lineNum)
                parts.append(Rejector.extraConflict(size))
                parts[size] += line


            elif line.startswith(Rejector.CONFILCT_END):
                # Modify the conflict in the original
                lines[lineNum] = line.rstrip() + "    " + Rejector.extraConflict(size-top)
                # Append the conflict part
                line = line.rstrip() + Rejector.extraLineNum(lineNum)
                parts[size-top] += line

                if top == 0: break;
                top -= 1

            else:
                if top > 0:
                    if line.startswith(Rejector.CONFLICT_MID):
                        # Modify the conflict in the original
                        lines[lineNum] = line.rstrip() + "  " + Rejector.extraConflict(size-top)
                        # Append the conflict part
                        line = line.rstrip() + Rejector.extraLineNum(lineNum)
 
                    parts[size-top] += line

            lineNum += 1

        rejFile.seek(0)
        rejFile.truncate()
        rejFile.writelines(lines)
        rejFile.close()

        return parts

    @staticmethod
    def extraConflict(top):
        return "# Conflict " + str(top) + "\n"

    @staticmethod
    def extraLineNum(lineNum):
        return "\t@line " + str(lineNum) + "\n"

    @staticmethod
    def combimeFromParts(parts, rejFilename):
        if len(parts) > 0:
            rejFile = open(rejFilename, "w")
            for part in parts:
                rejFile.write(part)
                rejFile.write("\n")

            rejFile.close()

    @staticmethod
    def check():
        Log.i("\n")

        Log.i("  +--------------- Auto Patch Results ")

        if len(Log.BUFF) > 0:
            Log.i("  |                                                                  ")
            Log.i("  |  >> Failed to auto patch the following files, please check out:  ")
            Log.i("  |                                                                  ")
            for message in Log.BUFF:
                Log.i("  |     " + message)

        if len(Rejector.REJ_LIST) > 0:
            Log.i("  |                                                                  ")
            Log.i("  |  >> -_-!!!  Conflicts happen in the following files:             ")
            Log.i("  |     (You could also find all the reject files in `out/reject/`)  ")
            Log.i("  |                                                                  ")
            for item in Rejector.REJ_LIST:
                Log.i("  |     " + item)
            Log.i("  |                                                                  ")
            Log.i("  |                                                                  ")
            Log.i("  |     Advice:                                                      ")
            Log.i("  |      1. Conflicts are marked out, you should resolve them        ")
            Log.i("  |         manually before you go on the following work.            ")
            Log.i("  |                                                                  ")
            Log.i("  |      2. As a reference to resolve conflict, use tools to         ")
            Log.i("  |         compare AOSP and BOSP.                                   ")
            Log.i("  |                                                                  ")
            Log.i("  |      3. Delete the reject file after resolving it.               ")
            Log.i("  |                                                                  ")
        else:
            Log.i("  |                                                                  ")
            Log.i("  |  >> ^_^.   No conflicts. Congratulations!                        ")
            Log.i("  |                                                                  ")
            Log.i("  |     Advice:                                                      ")
            Log.i("  |      1. Although no conflict, mistakes still come out sometimes, ")
            Log.i("  |         it depends on your device, VENDOR may change AOSP a lot. ")
            Log.i("  |                                                                  ")
            Log.i("  |      2. You could go on to `make` out a ROM, flash it into       ")
            Log.i("  |         your device, and then fix bugs depends on real-time logs.")
            Log.i("  |                                                                  ")

        Log.i("  +---------------")
        Log.i("\n")
