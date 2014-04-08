'''
Created on Feb 26, 2014

@author: tangliuxiang
'''

import os
import SmaliEntryFactory
import Smali
import re
import utils
import sys

sys.path.append('%s/autopatch' %os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import Log


from Content import Content
from SmaliLine import SmaliLine

SMALI_POST_SUFFIX = r'\.smali'
PART_SMALI_POST_SUFFIX = r'\.smali\.part'
SMALI_POST_SUFFIX_LEN = 6
DEBUG = False

class SmaliParser(object):
    '''
    classdocs
    '''
    STATE_NULL = 0
    STATE_WAIT_START = 1
    STATE_WAIT_END = 2

    def __init__(self, smaliFilePath, parseNow = True):
        '''
        Constructor
        '''
        self.mSmaliFilePath = smaliFilePath
        self.mParsed = False
        self.state = SmaliParser.STATE_NULL
        self.mEntryList = []
        
        if parseNow:
            self.parse()
            
    def parse(self):
        clsName = getClassFromPath(self.mSmaliFilePath)
        state = SmaliParser.STATE_WAIT_START;
        curEntryType = None
        curEntryContent = Content()
        curPreContent = Content()
        entryList = []
        
        if not os.path.isfile(self.mSmaliFilePath):
            Log.d("Warning: %s doesn't exist!" %(self.mSmaliFilePath))
            self.mParsed = True
            return
        
        sFile = file(self.mSmaliFilePath)
        fileLinesList = sFile.readlines()
        sFile.close()
        idx = 0
        while idx < len(fileLinesList):
            if fileLinesList[idx][-1] == "\n":
                sLine = SmaliLine(fileLinesList[idx][0:-1])
            else:
                sLine = SmaliLine(fileLinesList[idx])
            
            if sLine.getType() is SmaliLine.TYPE_DOT_LINE:
                if sLine.isDotEnd():
                    assert state == SmaliParser.STATE_WAIT_END, "wrong end in line: (%s:%s)" % (self.mSmaliFilePath, idx)
                    curEntryContent.append(sLine.getLine())
                    entryList.append(SmaliEntryFactory.newSmaliEntry(curEntryType, curEntryContent, clsName, curPreContent))
                    
                    curPreContent = Content()
                    curEntryContent = Content()
                    state = SmaliParser.STATE_WAIT_START
                else:
                    if state is SmaliParser.STATE_WAIT_START:
                        curEntryType = sLine.getDotType() 
                        assert curEntryType is not None, "Life is hard...."
                    
                        curEntryContent.setContentStr(sLine.getLine())
                        state = SmaliParser.STATE_WAIT_END
                    else:
                        assert state is SmaliParser.STATE_WAIT_END, "wrong state, Life is hard...."
                        assert not curEntryContent.isMultiLine(), "wrong entry start, expect .end %s (%s:%s)" % (curEntryType, self.mSmaliFilePath, idx)

                        postStr = curEntryContent.getPostContent().getContentStr()
                        curEntryContent.setContentStr(curEntryContent.getContentStr().split('\n')[0])
                        entryList.append(SmaliEntryFactory.newSmaliEntry(curEntryType, curEntryContent, clsName, curPreContent))
                        
                        curEntryType = sLine.getDotType()
                        assert curEntryType is not None, "Life is hard...."
                        
                        curPreContent = Content(postStr)
                        curEntryContent = Content(sLine.getLine())

            else:
                if state is SmaliParser.STATE_WAIT_START:
                    curPreContent.append(sLine.getLine())
                else:
                    assert state is SmaliParser.STATE_WAIT_END,  "wrong state, Life is hard...."
                    curEntryContent.append(sLine.getLine())
            idx = idx + 1
            
        if state is SmaliParser.STATE_WAIT_END \
            and curEntryType is not None \
            and curEntryContent.getContentStr() is not None:
            curEntryContent.setContentStr(curEntryContent.getContentStr().split('\n')[0])
            entryList.append(SmaliEntryFactory.newSmaliEntry(curEntryType, curEntryContent, clsName, curPreContent))
        
        self.mEntryList = entryList
        self.mParsed = True
    
    def getEntryList(self):
        if self.mParsed is False:
            self.parse()
        return self.mEntryList;
    
    def removeEntry(self, entry):
        if self.mParsed is False:
            self.parse()
            
        if entry is None:
            return False
        
        idx = 0
        while idx < len(self.mEntryList):
            if self.mEntryList[idx] == entry:
                del self.mEntryList[idx]
                return True
            idx = idx + 1
        return False
    
    def addEntry(self, entry):
        if self.mParsed is False:
            self.parse()
        
        if entry is None:
            return False
        
        self.mEntryList.append(entry)
        return True

    def replaceEntry(self, entry):
        if self.mParsed is False:
            self.parse()

        if entry is None:
            return False

        idx = 0
        while idx < len(self.mEntryList):
            if self.mEntryList[idx].equals(entry):
                self.mEntryList[idx] = entry
                return True
            idx = idx + 1

        self.addEntry(entry)
        return True


smaliFileRe = re.compile(r'(?:^.*%s$)|(?:^.*%s$)' % (SMALI_POST_SUFFIX, PART_SMALI_POST_SUFFIX))
partSmaliFileRe = re.compile(r'(?:^.*%s$)' %(PART_SMALI_POST_SUFFIX))
def isSmaliFile(smaliPath):
    return bool(smaliFileRe.match(smaliPath))

def isPartSmaliFile(smaliPath):
    return bool(partSmaliFileRe.match(smaliPath))

def getSmaliPathList(source):
    filelist = []
    
    source = os.path.abspath(source)
    if os.path.isfile(source):
        if isSmaliFile(source):
            filelist.append(source)
        return filelist
    
    for root, dirs, files in os.walk(source):
        for fn in files:
            if isSmaliFile(fn):
                filelist.append("%s/%s" % (root, fn))

    return filelist

def getPackageFromClass(className):
    try:
        idx = className.rindex(r'/')
    except:
        print "Error: wrong className: %s" %className
        return None
    return className[1:idx]

def __shouldFilter(filterOutDirList, sPath):
    if filterOutDirList is None:
        return False
    for dir in filterOutDirList:
        try:
            if sPath.index(dir) == 0:
                if DEBUG:
                    print ">>> filter path: %s" %sPath
                return True
        except:
            pass
    return False

def getSmaliDict(smaliDir, filterOutDirList = None):
    sFileList = getSmaliPathList(smaliDir)
    smaliDict = {}
    
    for sPath in sFileList:
        if not __shouldFilter(filterOutDirList, sPath):
            smali = Smali.Smali(sPath)
            sClass = getClassFromPath(sPath)
            smaliDict[sClass] = smali
       
    return smaliDict

def getJarNameFromPath(smaliPath):
    assert isSmaliFile(smaliPath), "This file is not smali file: %s" % smaliPath

    absSmaliPath = os.path.abspath(smaliPath)
    splitArray = absSmaliPath.split("/smali/")

    assert len(splitArray) >= 2, "This smali is not decode by apktool, doesn't hava /smali/ directory"
    return os.path.basename(splitArray[len(splitArray) - 2])

def getClassBaseNameFromPath(smaliPath):
    assert isSmaliFile(smaliPath), "This file is not smali file: %s" % smaliPath
    sBaseName = os.path.basename(smaliPath)
    return sBaseName[:sBaseName.rindex('.smali')]
        
def getClassFromPath(smaliPath):
    assert isSmaliFile(smaliPath), "This file is not smali file: %s" % smaliPath
    
    absSmaliPath = os.path.abspath(smaliPath)
    splitArray = absSmaliPath.split("/smali/")
    
    assert len(splitArray) >= 2, "This smali is not decode by apktool, doesn't hava /smali/ directory"
    clsNameWithPost = splitArray[len(splitArray) - 1]
    return 'L%s;' % clsNameWithPost[:clsNameWithPost.rindex('.smali')]



