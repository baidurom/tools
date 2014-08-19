#!/usr/bin/python

"""
Usage: $shell precondition.py [OPTIONS]
              OPTIONS:
                --patchall, -p : preparation for patchall
                --upgrade,  -u : preparation for upgrade
                --porting,  -t : preparation for porting
"""

__author__ = 'duanqz@gmail.com'



import shutil
import subprocess
import os, sys
import tempfile
from config import Config
from changelist import ChangeList
from formatters.log import Log, Paint



TAG="precondition"

try:
    DEVICE_BASE = os.path.join(os.environ["PORT_ROOT"], "devices/base")
except KeyError:
    DEVICE_BASE = os.curdir

FRAMEWORK_JARS = ("framework.jar", "services.jar", "telephony-common.jar",
                  "secondary-framework.jar", "secondary_framework.jar", "framework2.jar",
                  "mediatek-framework.jar", "framework-ext.jar",
                  "android.policy.jar",
                  "pm.jar")


def checkDeviceBaseExists():
    if not os.path.exists(DEVICE_BASE):
        # Not found devices/base
        Log.e(TAG, "%s not found" % DEVICE_BASE)
        sys.exit(155)


def preparePatchall():
    """ Prepare precondition of patchall
    """

    checkDeviceBaseExists()

    # Phase 1: prepare AOSP
    prepareAOSP(Config.AOSP_ROOT)

    print "  "

    # Phase 2: prepare BOSP
    prepareBOSP(Config.BOSP_ROOT)


    # Phase 3: make out the change list
    ChangeList(Config.AOSP_ROOT, Config.BOSP_ROOT, Config.PATCHALL_XML).make(force=False)


def prepareUpgrade():
    """ Prepare precondition of upgrade
    """

    checkDeviceBaseExists()

    lastBaiduZip = os.path.join(Config.PRJ_ROOT, "baidu/last_baidu.zip")
    baiduZip     = os.path.join(Config.PRJ_ROOT, "baidu/baidu.zip")

    if os.path.exists(lastBaiduZip) and os.path.exists(baiduZip):

        # Phase 1: prepare LAST_BOSP from last_baidu.zip
        Utils.decode(lastBaiduZip, Config.LAST_BOSP_ROOT)

        print "  "

        # Phase 2: prepare BOSP from baidu.zip
        Utils.decode(baiduZip, Config.BOSP_ROOT)

    else:

        # Phase 1: prepare LAST_BOSP from devices/base
        Utils.setToLastHead()
        prepareBOSP(Config.LAST_BOSP_ROOT)

        print "  "

        # Phase 2: prepare BOSP from devices/base
        Utils.setToOrigHead()
        prepareBOSP(Config.BOSP_ROOT)

    # Phase 3: make out the change list
    ChangeList(Config.LAST_BOSP_ROOT, Config.BOSP_ROOT, Config.UPGRADE_XML).make(force=True)


def preparePorting(argv):
    """ arg_0: device
        arg_1: commit1 if present
        arg_2: commit2 if present 
    """

    device = commit1 = commit2 = None
    argc = len(argv)
    if argc > 0 : device  = argv[0]
    if argc > 1 : commit1 = argv[1]
    if argc > 2 : commit2 = argv[2]

    if device == None:
        print "                                         "
        print "Usage: porting device [commit1] [commit2]"
        print "       - device should be presented      "
        print "                                         "

        sys.exit(1)

    (olderRoot, newerRoot) = Porting(device).prepare(commit1, commit2)

    ChangeList(olderRoot, newerRoot, Config.PORTING_XML).make(force=True)

    return (olderRoot, newerRoot)

def prepareAOSP(aospDst):

    aospSrc = os.path.join(DEVICE_BASE, "vendor/aosp")
    if os.path.exists(aospSrc) and not os.path.exists(aospDst):
        Log.i(TAG, "Generating %s from %s" %(aospDst, DEVICE_BASE))
        shutil.copytree(aospSrc, aospDst)

    Utils.combineFrameworkPartitions(aospDst)


def prepareBOSP(bospDst, force=True):
    """ Prepare BOSP, set force to be False to not generate again if exists.
    """

    if not os.path.exists(bospDst):
        os.makedirs(bospDst)

    Log.i(TAG, "Generating %s from %s" %(bospDst, DEVICE_BASE))

    src = os.path.join(DEVICE_BASE, "framework-res")
    dst = os.path.join(bospDst,     "framework-res")
    if force or not os.path.exists(dst):
        subp = Utils.run(["cp", "-r", "-u", src, bospDst], stdout=subprocess.PIPE)
        subp.wait()

    for jarname in FRAMEWORK_JARS:
        jarname += ".out"
        src = os.path.join(DEVICE_BASE, jarname)
        dst = os.path.join(bospDst,     jarname)
        if os.path.exists(src):
            if force or not os.path.exists(dst):
                subp = Utils.run(["cp", "-r", "-u", src, bospDst], stdout=subprocess.PIPE)
                subp.wait()

    Utils.combineFrameworkPartitions(bospDst)



class Porting:

    def __init__(self, device):
        self.devicePath = Porting.getDevicePath(device)
        self.portingDevice = PortingDevice(self.devicePath)


    @staticmethod
    def getDevicePath(device):
        device = os.path.join(os.path.dirname(DEVICE_BASE), device)
        return device


    def prepare(self, commit1=None, commit2=None):
        """ Porting changes from commit1 to commit2
        """

        (lowerCommit, upperCommit) = self.portingDevice.getCommitRange(commit1, commit2)

        # Get the patch files between two commits
        filesChanged = self.portingDevice.getChanges(lowerCommit, upperCommit)

        newer = self.generatePatchFiles(upperCommit, filesChanged, suffix="newer")
        older = self.generatePatchFiles(lowerCommit, filesChanged, suffix="older")
        self.portingDevice.restore()

        return (older, newer)

    def generatePatchFiles(self, commit, filesChanged, suffix):
        """ Generate patch files for porting
        """

        # Reset to the commit
        self.portingDevice.reset(commit)

        dirname = "%s_%s_%s" % (os.path.basename(self.devicePath), suffix, commit)
        dstDir = os.path.join(Config.AUTOPATCH, dirname)

        Log.i(TAG, "Prepare %s from %s" % (dstDir, self.devicePath))
        # Copy changed items from source
        for item in filesChanged:
            src = os.path.join(self.devicePath, item)
            dst = os.path.join(dstDir, item)
            if os.path.exists(src):
                dirname = os.path.dirname(dst)
                if not os.path.exists(dirname): os.makedirs(dirname)
                Utils.run(["cp", "-u", src, dst], stdout=subprocess.PIPE).wait()

        return dstDir


class PortingDevice:
    """ The Commits Model of a device
    """

    def __init__(self, devicePath):
        """ Initialize the commits model from a device path.
        """

        self.originPath = os.path.abspath(Config.PRJ_ROOT)
        self.devicePath = devicePath

        self.commitIDs = []
        self.comments  = []

        self.initAllCommits()


    def initAllCommits(self):
        """ Initialize all the commits information of device
        """

        os.chdir(self.devicePath)

        subp = Utils.run(["git", "log", "--oneline"], stdout=subprocess.PIPE)
        while True:
            buff = subp.stdout.readline().strip('\n')
            if buff == '' and subp.poll() != None:
                break

            buff = buff.strip()
            # The first 7 bits is commit ID
            self.commitIDs.append(buff[0:7])
            self.comments.append(buff[7:])

        os.chdir(self.originPath)


    def getChanges(self, lowerCommit, upperCommit):
        """ Get changes from lower to upper commit
        """

        os.chdir(self.devicePath)

        changes = []
        subp = Utils.run(["git", "diff", "--name-only", lowerCommit, upperCommit], stdout=subprocess.PIPE)
        while True:
            buff = subp.stdout.readline().strip('\n')
            if buff == '' and subp.poll() != None:
                break

            changes.append(buff.strip())

        os.chdir(self.originPath)

        return changes


    def restore(self):
        self.reset(self.commitIDs[0])


    def reset(self, commit):
        """ Reset to commit
        """

        os.chdir(self.devicePath)

        subp = Utils.run(["git", "reset", "--hard", commit], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)

        os.chdir(self.originPath)

    def showUserInputHint(self):
        """ Show user input hint
        """

        for i in range(0, len(self.commitIDs)):
            commitID = self.commitIDs[i]
            comment  = self.comments[i]
            print "  %s %s" % (Paint.bold(commitID), comment)

        deviceName = os.path.basename(self.devicePath)
        oneCommit  = Paint.bold(self.commitIDs[0])
        twoCommits = "%s %s" % (Paint.bold(self.commitIDs[-1]), Paint.bold(self.commitIDs[0]))
        print "  ________________________________________________________________________________________"
        print "                                                                                          "
        print "  Each 7 bits SHA1 code identify a commit on %s," % Paint.blue(deviceName),
        print "  You could input:                                                                        "
        print "  - Only one single commit, like: %s" % oneCommit
        print "    will porting changes between the selected and the latest from %s to your device" % Paint.blue(deviceName) 
        print "  - Two commits as a range, like: %s" % twoCommits
        print "    will porting changes between the two selected from %s to your device" % Paint.blue(deviceName)
        print "  ________________________________________________________________________________________"
        print "                                                                                          "


    def readUserInput(self):
        """ Read user input
        """

        self.showUserInputHint()

        userInput = raw_input(Paint.bold(">>> Input the 7 bits SHA1 commit ID (q to exit):  "))
        if userInput in ("q", "Q"): sys.exit()

        commits = userInput.split()
        size = len(commits)
        commit1 = commit2 = None
        if size > 0 : commit1 = commits[0]
        if size > 1 : commit2 = commits[1]

        return (commit1, commit2)


    def computeLowerAndUpper(self, commit1, commit2=None):
        """ Retrieve the lower and upper commit ID
        """

        if commit2 == None: commit2 = commit1

        try:    index1 = self.commitIDs.index(commit1)
        except: index1 = 0

        try:    index2 = self.commitIDs.index(commit2)
        except: index2 = 0

        if  index1 == index2:
            upper = 0
            lower = index1
        elif index1 < index2:
            upper = index1
            lower = index2
        else:
            upper = index2
            lower = index1

        lowerCommit = self.commitIDs[lower]
        upperCommit = self.commitIDs[upper]

        return (lowerCommit, upperCommit)


    def getCommitRange(self, commit1, commit2):
        """ Get the range of commit1 and commit2
        """

        # If no commit present, ask for user input
        if commit1 == None and commit2 == None:
            (commit1, commit2) = self.readUserInput()

        return self.computeLowerAndUpper(commit1, commit2)


# End of class PortingDevice



class Utils:
    """ Utilities
    """

    DEVICE_BASE_TOOL = os.path.join(os.path.dirname(__file__), "device_base.sh")

    PARTITIONS=("secondary_framework.jar.out", "secondary-framework.jar.out",
                "framework2.jar.out", "framework-ext.jar.out")

    @staticmethod
    def decode(baiduZip, out):
        """ Decode FRAMEWORK_JARS in baidu.zip into out directory.
        """

        Log.i(TAG, "Generating %s from %s" %(out, baiduZip))

        # Phase 1: deodex
        deodexZip = Utils.deodex(baiduZip)
        if deodexZip == None:
            return

        # Phase 2: decode framework jars
        temp = tempfile.mkdtemp()
        Log.i(TAG, "unzip %s to %s" % (deodexZip, temp))
        subp = Utils.run(["unzip", "-q", "-o", deodexZip, "-d", temp], stdout=subprocess.PIPE)
        subp.wait()

        # Format path
        if os.path.join(os.path.join(temp, "SYSTEM")):
            shutil.move(os.path.join(temp, "SYSTEM"), os.path.join(temp, "system"))

        dirname = os.path.join(temp, "system/framework")
        for jarname in FRAMEWORK_JARS:
            jarpath = os.path.join(dirname, jarname)
            if os.path.exists(jarpath):
                Log.i(TAG, "decoding %s" % jarname)
                jarout = os.path.join(out, jarname + ".out")
                subp = Utils.run(["apktool", "d", "-f", jarpath, jarout], stdout=subprocess.PIPE)
                Utils.printSubprocessOut(subp)

        shutil.rmtree(temp)

        # Phase 3: combine framework partitions
        Utils.combineFrameworkPartitions(out)


    @staticmethod
    def deodex(baiduZip):
        """ Deodex the baidu.zip. The deodexed with suffix "deodex.zip" is returned if succeed.
        """

        if not os.path.exists(baiduZip):
            Log.e(TAG, "deodex() % not exists" % baiduZip)
            return None

        deodexZip = baiduZip + ".deodex.zip"
        if os.path.exists(deodexZip):
            Log.d(TAG, "deodex() %s already exists" % deodexZip)
            return deodexZip

        DEODEX_THREAD_NUM="4"
        Log.i(TAG, "Deodex %s" % baiduZip)
        subp = Utils.run(["deodex", "-framework", baiduZip, DEODEX_THREAD_NUM], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)

        if not os.path.exists(deodexZip):
            Log.e(TAG, "deodex() deodex %s failed!" % baiduZip)
            return None

        return deodexZip


    @staticmethod
    def combineFrameworkPartitions(frameworkDir):
        """ Combine framework partitions into framework.jar.out.
        """

        for partition in Utils.PARTITIONS:
            if partition == "framework.jar.out": continue

            partitionPath = os.path.join(frameworkDir, partition)
            if os.path.exists(partitionPath):
                Log.i(TAG, "Combine %s into framework.jar.out" % partition)
                src = os.path.join(partitionPath, "smali")
                dst = os.path.join(frameworkDir, "framework.jar.out")
                subp = Utils.run(["cp", "-r",  src, dst], stdout=subprocess.PIPE)
                subp.wait()
                shutil.rmtree(partitionPath)


    @staticmethod
    def setToLastHead():
        subp = Utils.run([Utils.DEVICE_BASE_TOOL, "--last"], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)

    @staticmethod
    def setToOrigHead():
        subp = Utils.run([Utils.DEVICE_BASE_TOOL, "--orig"], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)

    @staticmethod
    def run(args, **kwargs):
        """Create and return a subprocess.Popen object, printing the command
           line on the terminal
        """

        return subprocess.Popen(args, **kwargs)


    @staticmethod
    def printSubprocessOut(subp):
        while True:
            buff = subp.stdout.readline().strip('\n')
            if buff == '' and subp.poll() != None:
                break
    
            Log.i(TAG, buff)

# End of class Utils




if __name__ == "__main__":
    argc = len(sys.argv)
    if argc < 2:
        print __doc__
        sys.exit(0)

    arg1 = sys.argv[1]
    if   arg1 in ("--patchall,-p"): preparePatchall()
    elif arg1 in ("--upgrade, -u"): prepareUpgrade()
    elif arg1 in ("--porting, -t"): preparePorting(sys.argv[2:])

    elif arg1 in ("--decode,  -d"):
        if argc > 2: otaZip = sys.argv[2]
        if argc > 3: out    = sys.argv[3]
        Utils.decode(otaZip, out)
