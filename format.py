#!/usr/bin/python

### File Information ###
"""
Incorporate changes from older to newer into target.
"""

__author__ = 'duanqz@gmail.com'



import commands
import shutil
import os

from os import sys, path

sys.path.append(path.dirname(path.abspath(__file__)))
from accessmethod.name2num import NameToNumForOneFile
from accessmethod.num2name import NumToNameForOneFile
from idtoname import idtoname
from nametoid import nametoid
#from smaliparser import SmaliLib, SCheck


class Format():

    DEBUG = False

    RELATIVE_PUBLIC_XML = "framework-res/res/values/public.xml"

    REMOVE_LINE    = 0x00000001
    RESID_TO_NAME  = 0x00000010
    ACCESS_TO_NAME = 0x00000100
    UNIFY_INVOKE   = 0x00001000
    XX             = 0x00010000
    XXX            = 0x00100000
    XXXX           = 0x01000000
    XXXXX          = 0x10000000

    def __init__(self, root, smaliFile):
        self.mRoot = root
        self.mSmaliFile = smaliFile

        #self.mSmaliLib = SmaliLib.SmaliLib(self.mRoot)
        self.mPublicXML = os.path.join(self.mRoot, Format.RELATIVE_PUBLIC_XML)

    def setPublicXML(self, publicXML):
        self.mPublicXML = publicXML
        return self

    def do(self, action):
        self.mAction = action

        Format.log("DO")

        # REMOVE_LINE ->  ACCESS_TO_NAME -> RESID_TO_NAME
        if self.mAction & Format.REMOVE_LINE:
            Format.log("  REMOVE_LINE")
            self.mLinePatch = Format.remLines(self.mSmaliFile)

        if self.mAction & Format.ACCESS_TO_NAME:
            Format.log("  ACCESS_TO_NAME")
            self.mAccessData = NumToNameForOneFile(self.mSmaliFile)

        if self.mAction & Format.RESID_TO_NAME:
            Format.log("  RESID_TO_NAME")
            if os.path.exists(self.mPublicXML):
                idtoname(self.mPublicXML, self.mSmaliFile).idtoname()
            else:
                Format.log("  No such file or directory: %s" % self.mPublicXML)

        if self.mAction & Format.UNIFY_INVOKE:
            Format.log("  UNIFY_INVOKE")
            # TODO
            #SCheck.formatSmali(self.mSmaliLib, [self.mSmaliFile])

        return self

    def undo(self):

        Format.log("UNDO")

        # RESID_TO_NAME ->  ACCESS_TO_NAME -> REMOVE_LINE 
        if self.mAction & Format.RESID_TO_NAME:
            Format.log("  RESID_TO_NAME")
            if os.path.exists(self.mPublicXML):
                nametoid(self.mPublicXML, self.mSmaliFile).nametoid()
            else:
                Format.log("  No such file or directory: %s" % self.mPublicXML)

        if self.mAction & Format.ACCESS_TO_NAME:
            Format.log("  ACCESS_TO_NAME")
            NameToNumForOneFile(self.mAccessData)

        if self.mAction & Format.REMOVE_LINE:
            Format.log("  REMOVE_LINE")
            Format.addLines(self.mSmaliFile, self.mLinePatch)

        return self

    @staticmethod
    def remLines(origFile):
        """ Remove lines in original file
        """

        noLineFile = origFile + ".noline"

        # Generate no line file
        cmd = "cat %s | sed -e '/^\s*\.line.*$/d' | sed -e 's/\/jumbo//' > %s" % \
                (commands.mkarg(origFile), commands.mkarg(noLineFile))
        commands.getstatusoutput(cmd)

        # Generate line patch
        linesPatch = origFile + ".linepatch"
        cmd = "diff -B -u %s %s > %s" % \
                (commands.mkarg(noLineFile), commands.mkarg(origFile), commands.mkarg(linesPatch))
        commands.getstatusoutput(cmd)

        shutil.move(noLineFile, origFile)

        return linesPatch

    @staticmethod
    def addLines(smaliFile, linesPatch):
        """ Add the lines back to no line file
        """

        # Patch the lines to no line file
        cmd = "patch -f %s -r /dev/null < %s > /dev/null" % \
                (commands.mkarg(smaliFile), commands.mkarg(linesPatch))
        commands.getstatusoutput(cmd)

        os.remove(linesPatch)
        origFile = smaliFile + ".orig"
        if os.path.exists(origFile): os.remove(origFile)

        return smaliFile

    @staticmethod
    def log(message):
        if Format.DEBUG: print message

if __name__ == "__main__":
    root = "/media/source/smali/smali-4.2/devices/demo/autopatch/vendor"
    smaliFile = "/media/source/smali/smali-4.2/devices/demo/framework.jar.out/smali/android/widget/TextView.smali"
    publicXML = "/media/source/smali/smali-4.2/devices/demo/framework-res/res/values/public.xml"

    action = Format.REMOVE_LINE | Format.ACCESS_TO_NAME | Format.RESID_TO_NAME | Format.UNIFY_INVOKE
    Format(root, smaliFile).setPublicXML(publicXML).do(action).undo()
