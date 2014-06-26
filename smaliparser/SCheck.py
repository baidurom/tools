'''
Created on Mar 12, 2014

@author: tangliuxiang
'''
import SmaliLib
import SmaliEntry
import Smali
import string
import SmaliMethod
import sys
import os
import getopt
import SAutoCom
import SmaliFileReplace
import tobosp
import utils
import Replace

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from format import Format

from SmaliLib import SmaliLib

class Options(object): pass
OPTIONS = Options()
OPTIONS.autoComplete = False

OPTIONS.formatSmali = False
OPTIONS.libraryPath = None
OPTIONS.filterOutDir = []

OPTIONS.replaceMethod = False
OPTIONS.replaceSmali = False
OPTIONS.tobosp = False

OPTIONS.replaceWithCheck = False
OPTIONS.methodToBosp = False

OPTIONS.smaliToBosp = False

def formatSmali(smaliLib, smaliFileList = None):
    utils.SLog.i("    begin format smali files, please wait....")
    if smaliFileList is not None:
        idx = 0
        while idx < len(smaliFileList):
            clsName = utils.getClassFromPath(smaliFileList[idx])
            cSmali = smaliLib.getSmali(clsName)
            smaliLib.format(cSmali)
            idx = idx + 1
    else:
        for clsName in smaliLib.mSDict.keys():
            cSmali = smaliLib.getSmali(clsName)
            smaliLib.format(cSmali)
    utils.SLog.i("    format done")

def usage():
    pass

def main(argv):
    options,args = getopt.getopt(argv[1:], "hafl:s:t:rpbm:", [ "help", "autocomplete", "formatsmali", "library", "smali", "filter", "replacemethod", "replacesmali", "methodtobosp", "smalitobosp"])
    for name,value in options:
        if name in ("-h", "--help"):
            usage()
        elif name in ("-a", "--autocomplete"):
            OPTIONS.autoComplete = True
        elif name in ("-f", "--formatsmali"):
            OPTIONS.formatSmali = True
        elif name in ("-l", "--library"):
            OPTIONS.libraryPath = value
        elif name in ("-t", "--filter"):
            OPTIONS.filterOutDir.append(os.path.abspath(value))
        elif name in ("-r", "--replacemethod"):
            OPTIONS.replaceMethod = True
        elif name in ("-m", "--methodtobosp"):
            OPTIONS.replaceWithCheck = False
            OPTIONS.methodToBosp = True
        elif name in ("--smalitobosp"):
            OPTIONS.smaliToBosp = True
        else:
            utils.SLog.w("Wrong parameters, see the usage....")
            usage()
            exit(1)

    if OPTIONS.autoComplete:
        if len(args) >= 6:
            SAutoCom.SAutoCom.autocom(args[0], args[1], args[2], args[3], args[4], args[5:])
        else:
            usage()
            exit(1)
    elif OPTIONS.formatSmali:
        if OPTIONS.libraryPath is None:
            if len(args) > 0:
                OPTIONS.libraryPath = args[0]
                args = args[1:]
            else:
                usage()
                exit(1)
        if len(args) > 0:
            formatSmali(SmaliLib.getSmaliLib(OPTIONS.libraryPath), args)
        else:
            formatSmali(SmaliLib.getSmaliLib(OPTIONS.libraryPath), None)
    elif OPTIONS.replaceMethod:
        if len(args) >= 3:
            Replace.replaceMethod(args[0], args[1], args[2])
    elif OPTIONS.methodToBosp:
        if len(args) >= 2:
            Replace.methodtobosp(args[0], args[1], OPTIONS.replaceWithCheck)
    elif OPTIONS.smaliToBosp:
        if len(args) >= 1:
            SmaliFileReplace.smalitobosp(args, False)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv)
    else:
        usage()
