#!/usr/bin/python
# Filename: config.py

### File Information ###
"""
Configuration
"""

__author__ = 'duanqz@gmail.com'



import os.path


class Config:
    """ Configuration.
    """

    # Whether in debug mode or not
    DEBUG = False

    # Whether to revise OPTION feature, default to be True
    REVISE_OPTION = True


### Root directory   
    # Root directory of current project
    PRJ_ROOT = os.curdir

    # Root directory of reject files
    REJ_ROOT = os.path.join(PRJ_ROOT, "out/reject/")

### DIFF-PATCH Directory
    # We need to hold three directory because diff_patch.sh
    # incorporate changes from newer to older into target.

    AUTOPATCH_DIR = os.path.join(PRJ_ROOT, "autopatch/")

    # Older directory
    OLDER_DIR = os.path.join(AUTOPATCH_DIR, "aosp/")

    # Newer directory
    NEWER_DIR = os.path.join(AUTOPATCH_DIR, "bosp/")

### Upgrade Directory
    # Upgrade directory contains all the upgrade patches.

    UPGRADE_DIR = os.path.join(AUTOPATCH_DIR, "upgrade/")

    UPGRADE_LAST_BAIDU_DIR = os.path.join(UPGRADE_DIR, "last_baidu/")

    UPGRADE_BAIDU_DIR  = os.path.join(UPGRADE_DIR, "baidu/")

### Patches directory
    # Default patchall.xml to be parsed
    PATCH_XML = os.path.join(AUTOPATCH_DIR, "changelist/patchall.xml")

    PATCH_XML_DIR = os.path.dirname(PATCH_XML)



    @staticmethod
    def setup(argv):
        """ Setup the configuration.
            arguments list is (PATCH_XML, OLDER_DIR, NEWER_DIR)
        """

        argc = len(argv)
        if argc > 0: Config.setPatchXML(argv[0])
        if argc > 1: Config.setReviseOption(argv[1])

        Config.toString()

    @staticmethod
    def setPatchXML(patchXML):
        Config.PATCH_XML = patchXML
        Config.PATCH_XML_DIR = os.path.dirname(Config.PATCH_XML)

    @staticmethod
    def setDiffDir(olderDir, newerDir):
        Config.OLDER_DIR = olderDir
        Config.NEWER_DIR = newerDir

    @staticmethod
    def setReviseOption(option):
        option = option.lower()
        if option == "true":
            Config.REVISE_OPTION = True
        elif option == "false" :
            Config.REVISE_OPTION = False

    @staticmethod
    def createReject(target):
        relTarget = os.path.relpath(target, Config.PRJ_ROOT)
        rejFilename = os.path.join(Config.REJ_ROOT, relTarget + ".reject")
        dirname = os.path.dirname(rejFilename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        return rejFilename

    @staticmethod
    def toString():
        Log.d("-----------------------------------------------------------")
        Log.d("PRJ_ROOT:\t" + Config.PRJ_ROOT)
        Log.d("OLDER_DIR:\t" + Config.OLDER_DIR)
        Log.d("NEWER_DIR:\t" + Config.NEWER_DIR)
        Log.d("---")
        Log.d("PATCH_XML:\t" + Config.PATCH_XML)
        Log.d("REVISE_OPTION:\t" + str(Config.REVISE_OPTION))
        Log.d("-----------------------------------------------------------")

# End of class Config

class Log:

    FAILED_LIST = []

    REJECT_LIST = []

    @staticmethod
    def d(message):
        if Config.DEBUG: print message

    @staticmethod
    def i(message):
        print message

    @staticmethod
    def w(message):
        print " Waring: ", message

    @staticmethod
    def e(message):
        print " Error: ", message

    @staticmethod
    def fail(message):
        Log.FAILED_LIST.append(message)

    @staticmethod
    def reject(target):
        Log.REJECT_LIST.append(target)

    @staticmethod
    def conclude():
        Log.i("\n")

        Log.i("  +--------------- Auto Patch Results ")

        if len(Log.FAILED_LIST) > 0:
            Log.i("  |                                                                  ")
            Log.i("  |  >> Failed to auto patch the following files, please check out:  ")
            Log.i("  |                                                                  ")
            for failed in Log.FAILED_LIST: Log.i("  |     " + failed)

        if len(Log.REJECT_LIST) > 0:
            Log.i("  |                                                                  ")
            Log.i("  |  >> -_-!!!  Conflicts happen in the following files:             ")
            Log.i("  |                                                                  ")
            for reject in Log.REJECT_LIST: Log.i("  |     " + reject)
            Log.i("  |                                                                  ")
            Log.i("  |                                                                  ")
            Log.i("  |     Advice:                                                      ")
            Log.i("  |      1. Conflicts are marked out in `out/reject/`, you'd better  ")
            Log.i("  |         resolve them before going on with the following work.    ")
            Log.i("  |                                                                  ")
            Log.i("  |      2. To resolve conflict, use tools to compare AOSP and BOSP, ")
            Log.i("  |         also VENDOR and BOSP. Beyond-Compare is recommended.     ")
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

if __name__ == "__main__":
    Config.toString()