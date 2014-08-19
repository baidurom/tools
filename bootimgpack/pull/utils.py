'''
Created on Jul 31, 2014

@author: tangliuxiang
'''
from mtkpull import mtkpull
from pull import pull
import os, sys
import tempfile

from command import AdbShell
from command import SuShell
from command import AndroidFile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from internal.bootimg import Bootimg

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from formatters.log import Log

LOG_TAG = "pull_boot_recovery"

class PullUtils():
    @staticmethod
    def check():
        AdbShell().waitdevices(True)
        tmpOut = tempfile.mktemp()
        SuShell().run("echo TRUE", tmpOut)
        assert os.path.isfile(tmpOut) and file(tmpOut).read().strip("\n") == "TRUE", "You must root your phone first!"
    
    @staticmethod
    def pull(outDir):
        ret = False
        Log.i("pull_boot_recovery", "Begin pull boot and recovery, make sure your phone was connected and adb devices is fine!")
        Log.i("pull_boot_recovery", "It may take a few minutes, please wait....")
        PullUtils.check()
        if mtkpull.isMtkDevice() and mtkpull.do(outDir):
            Log.d("pull_boot_recovery", "Success use mtkpull to pull images....")
            ret = True
        else:
            if pull.do(outDir):
                Log.d("pull_boot_recovery", "Success use mtkpull to pull images....")
                ret = True
        assert ret == True, "Failed to pull images....."
