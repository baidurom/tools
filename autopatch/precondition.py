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


class Prepare:

    FRAMEWORK_JARS = ("framework.jar", "services.jar", "telephony-common.jar", "android.policy.jar", "pm.jar",
                      "secondary-framework.jar", "secondary_framework.jar",
                      "framework-ext.jar", "framework_ext.jar",
                      "framework2.jar",
                      "mediatek-framework.jar")

    PARTITIONS     = ("secondary_framework.jar.out", "secondary-framework.jar.out",
                      "framework-ext.jar.out", "framework_ext.jar.out",
                      "framework2.jar.out")


    DEVICE_BASE_TOOL = os.path.join(os.path.dirname(__file__), "device_base.sh")


    @staticmethod
    def setup(base):
        Prepare.DEVICE_BASE = Prepare.getBasePath(base)


    @staticmethod
    def getBasePath(base):
        try:
            devices = os.path.join(os.environ["PORT_ROOT"], "devices")
            return os.path.join(devices, base)
        except KeyError:
            Log.e(TAG, "device %s not found" % base)
            sys.exit(155)


    @staticmethod
    def patchall():
        """ Prepare precondition of patchall
        """

        # Phase 1: prepare AOSP
        Prepare.aosp(Config.AOSP_ROOT)

        print "  "

        # Phase 2: prepare BOSP
        Prepare.bosp(Config.BOSP_ROOT)

        # Phase 3: make out the change list
        hasChange = ChangeList(Config.AOSP_ROOT, Config.BOSP_ROOT, Config.PATCHALL_XML).make(force=False)

        # Phase 4: record last head
        Utils.recordLastHead()

        if not hasChange:
            print " "
            print Paint.green(" No changes between %s and %s, nothing to patch." % (Config.AOSP_ROOT, Config.BOSP_ROOT))
            sys.exit(0)


    @staticmethod
    def upgrade():
        """ Prepare precondition of upgrade
        """

        lastBaiduZip  = os.path.join(Config.PRJ_ROOT, "baidu/last_baidu.zip")
        baiduZip      = os.path.join(Config.PRJ_ROOT, "baidu/baidu.zip")

        baseAutopatch = os.path.join(Prepare.DEVICE_BASE, "autopatch")

        if os.path.exists(lastBaiduZip) and os.path.exists(baiduZip):

            # Phase 1: prepare LAST_BOSP from last_baidu.zip
            Utils.decode(lastBaiduZip, Config.LAST_BOSP_ROOT)

            print "  "

            # Phase 2: prepare BOSP from baidu.zip
            Utils.decode(baiduZip, Config.BOSP_ROOT)

        elif os.path.exists(baseAutopatch):
            prjAutopatch = os.path.join(Config.PRJ_ROOT, "autopatch")
            if os.path.exists(prjAutopatch):
                shutil.rmtree(prjAutopatch)

            Log.i(TAG, "Generating %s from %s" % (prjAutopatch, baseAutopatch))
            shutil.copytree(baseAutopatch, prjAutopatch)

        else:

            # Phase 1: prepare LAST_BOSP from devices/base
            Utils.setToLastHead()
            Prepare.bosp(Config.LAST_BOSP_ROOT)

            print "  "

            # Phase 2: prepare BOSP from devices/base
            Utils.setToOrigHead()
            Prepare.bosp(Config.BOSP_ROOT)

        # Phase 3: make out the change list
        hasChange = ChangeList(Config.LAST_BOSP_ROOT, Config.BOSP_ROOT, Config.UPGRADE_XML).make(force=True)

        if not hasChange:
            print " "
            print Paint.green(" Already the newest.")
            sys.exit(0)


    @staticmethod
    def porting(argv):
        """ arg_0: device
            arg_1: commit1 if present
            arg_2: commit2 if present 
        """

        base = commit1 = commit2 = None
        argc = len(argv)
        if argc > 0 : base  = argv[0]
        if argc > 1 : commit1 = argv[1]
        if argc > 2 : commit2 = argv[2]

        if base == None:
            print "                                         "
            print "Usage: porting device [commit1] [commit2]"
            print "       - device should be presented      "
            print "                                         "

            sys.exit(1)

        (olderRoot, newerRoot) = Porting(base).prepare(commit1, commit2)

        hasChange = ChangeList(olderRoot, newerRoot, Config.PORTING_XML).make(force=True)

        if not hasChange:
            print " "
            print Paint.green(" No changes between %s and %s, nothing to porting." % (olderRoot, newerRoot))
            sys.exit(0)

        return (olderRoot, newerRoot)


    @staticmethod
    def aosp(aospDst):

        aospSrc = os.path.join(Prepare.DEVICE_BASE, "vendor/aosp")
        if not os.path.exists(aospSrc):
            os.makedirs(aospSrc)
            vendorRoot = os.path.join(Prepare.DEVICE_BASE, "vendor")
            Utils.decodeAPKandJAR(vendorRoot, aospSrc)

        if not os.path.exists(aospDst):
            Log.i(TAG, "Generating %s from %s" % (aospDst, Prepare.DEVICE_BASE))
            shutil.copytree(aospSrc, aospDst)

        Utils.combineFrameworkPartitions(aospDst)


    @staticmethod
    def bosp(bospDst, force=True):
        """ Prepare BOSP, set force to be False to not generate again if exists.
        """

        if force:
            subp = Utils.run(["rm", "-rf", bospDst], stdout=subprocess.PIPE)
            subp.communicate()

        if not os.path.exists(bospDst):
            os.makedirs(bospDst)

        Log.i(TAG, "Generating %s from %s" %(bospDst, Prepare.DEVICE_BASE))

        src = os.path.join(Prepare.DEVICE_BASE, "framework-res")
        subp = Utils.run(["cp", "-r", src, bospDst], stdout=subprocess.PIPE)
        subp.communicate()

        for jarname in Prepare.FRAMEWORK_JARS:
            jarname += ".out"
            src = os.path.join(Prepare.DEVICE_BASE, jarname)
            if os.path.exists(src):
                subp = Utils.run(["cp", "-r", src, bospDst], stdout=subprocess.PIPE)
                subp.communicate()

        Utils.combineFrameworkPartitions(bospDst)



class Porting:

    def __init__(self, device):
        self.devicePath = Porting.getDevicePath(device)
        self.portingDevice = PortingDevice(self.devicePath)


    @staticmethod
    def getDevicePath(device):
        device = os.path.join(os.path.dirname(Prepare.DEVICE_BASE), device)
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
        if not os.path.exists(dstDir):
            os.makedirs(dstDir)

        Log.i(TAG, "Prepare %s from %s" % (dstDir, self.devicePath))
        # Copy changed items from source
        for item in filesChanged:
            src = os.path.join(self.devicePath, item)
            dst = os.path.join(dstDir, item)
            if os.path.exists(src):
                dirname = os.path.dirname(dst)
                if not os.path.exists(dirname): os.makedirs(dirname)
                Utils.run(["cp", "-u", src, dst], stdout=subprocess.PIPE).communicate()

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
        subp.communicate()

        Utils.decodeAPKandJAR(temp, out)

        shutil.rmtree(temp)

        # Phase 3: combine framework partitions
        Utils.combineFrameworkPartitions(out)


    @staticmethod
    def decodeAPKandJAR(root, out):
        # Format path
        if os.path.exists(os.path.join(root, "SYSTEM")):
            shutil.move(os.path.join(root, "SYSTEM"), os.path.join(root, "system"))

        dirname = os.path.join(root, "system/framework")

        Log.i(TAG, "decoding framework-res.apk")
        jarpath = os.path.join(dirname, "framework-res.apk")
        jarout  = os.path.join(out, "framework-res")
        subp = Utils.run(["apktool", "d", "-f", jarpath, jarout], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)

        for jarname in Prepare.FRAMEWORK_JARS:
            jarpath = os.path.join(dirname, jarname)
            if os.path.exists(jarpath):
                Log.i(TAG, "decoding %s" % jarname)
                jarout = os.path.join(out, jarname + ".out")
                subp = Utils.run(["apktool", "d", "-f", jarpath, jarout], stdout=subprocess.PIPE)
                Utils.printSubprocessOut(subp)


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

        for partition in Prepare.PARTITIONS:
            if partition == "framework.jar.out": continue

            partitionPath = os.path.join(frameworkDir, partition)
            if os.path.exists(partitionPath):
                Log.i(TAG, "Combine %s into framework.jar.out" % partition)
                src = os.path.join(partitionPath, "smali")
                dst = os.path.join(frameworkDir, "framework.jar.out")
                subp = Utils.run(["cp", "-r",  src, dst], stdout=subprocess.PIPE)
                subp.communicate()
                shutil.rmtree(partitionPath)


    @staticmethod
    def recordLastHead():
        subp = Utils.run([Prepare.DEVICE_BASE_TOOL, "--recd", Prepare.DEVICE_BASE], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)


    @staticmethod
    def setToLastHead():
        subp = Utils.run([Prepare.DEVICE_BASE_TOOL, "--last", Prepare.DEVICE_BASE], stdout=subprocess.PIPE)
        Utils.printSubprocessOut(subp)


    @staticmethod
    def setToOrigHead():
        subp = Utils.run([Prepare.DEVICE_BASE_TOOL, "--orig", Prepare.DEVICE_BASE], stdout=subprocess.PIPE)
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

    if argc > 2: base = sys.argv[2]
    else:        base = "base"

    Prepare.setup(base)

    arg1 = sys.argv[1]
    if   arg1 in ("--patchall,-p"): Prepare.patchall()
    elif arg1 in ("--upgrade, -u"): Prepare.upgrade()
    elif arg1 in ("--porting, -t"): Prepare.porting(sys.argv[2:])

