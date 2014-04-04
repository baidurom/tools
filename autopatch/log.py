#!/usr/bin/python
# Filename: config.py

### File Information ###
"""
Log
"""

__author__ = 'duanqz@gmail.com'



class Log:

    DEBUG = False

    FAILED_LIST = []

    REJECT_LIST = []

    @staticmethod
    def d(message):
        if Log.DEBUG: print message

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
            for failed in set(Log.FAILED_LIST): Log.i("  |     " + failed)

        if len(Log.REJECT_LIST) > 0:
            Log.i("  |                                                                  ")
            Log.i("  |  >> -_-!!!  Conflicts happen in the following files:             ")
            Log.i("  |                                                                  ")
            for reject in set(Log.REJECT_LIST): Log.i("  |     " + reject)
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
    Log.conclude()