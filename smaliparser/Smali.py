'''
Created on Feb 26, 2014

@author: tangliuxiang
'''

import os
import re
import SmaliEntry
import hashlib
import SmaliParser

from Content import Content

KEY_INTERFACE = "interface"

KEY_PUBLIC = "public"
KEY_PRIVATE = "private"
KEY_PROTECTED = "protected"
KEY_STATIC = "static"
KEY_FINAL = "final"
KEY_SYNTHETIC = "synthetic"

# only use in methods
KEY_ABSTRACT = "abstract"
KEY_CONSTRUCTOR = "constructor"
KEY_BRIDGE = "bridge"
KEY_DECLARED_SYNCHRONIZED = "declared-synchronized"
KEY_NATIVE = "native"
KEY_SYNCHRONIZED = "synchronized"
KEY_VARARGS = "varargs"

# only use in field
KEY_ENUM = "enum"
KEY_TRANSIENT = "transient"
KEY_VOLATILE = "volatile"

MAX_INVOKE_LEN = 5
DEBUG = True

DEFAULT_SUPER = r'Ljava/lang/Object;'

class Smali(object):
    '''
    classdocs
    '''

    def __init__(self, smaliFilePath):
        '''
        Constructor
        '''
        self.mPath = smaliFilePath
        self.mParser = SmaliParser.SmaliParser(smaliFilePath, False)
        self.mInvokeMethods = None
        self.mAllMethods = None
        self.mImplementsClassList = None
        self.mChildrenClsNameList = []
        self.__mWasInvokedList = {}
        self.mClassName = None
        self.mSuperClassName = None
        self.mSourceName = None
        self.mPackageName = None
        self.mUsedOutsideFields = None
        self.mUsedFields = None
        self.mIsPartSmali = SmaliParser.isPartSmaliFile(smaliFilePath)
 
    def useField(self, name):
        pass
    
    def wasInvoke(self, invokeItem, check = False):
        if check and not self.checkInvokeType(invokeItem.method, invokeItem.type):
            print ">>> Error: wrong invoke in class %s, method: %s, invoke method: %s, invoke type: %s" %(invokeItem.cls, invokeItem.belongMethod, invokeItem.method, invokeItem.type)
            return False
        
        if not self.__mWasInvokedList.has_key(invokeItem.method):
            self.__mWasInvokedList[invokeItem.method] = []
        if len(self.__mWasInvokedList[invokeItem.method]) < MAX_INVOKE_LEN:
                self.__mWasInvokedList[invokeItem.method].append(invokeItem)

    def getWasInvokeList(self):
        return self.__mWasInvokedList
    
    def checkInvokeType(self, methodName, invokeType):
        if invokeType is None:
            return True
        else:
            # need write function to check invoke type
            return True

    def addChild(self, childClsName):
        self.mChildrenClsNameList.append(childClsName)
    
    def getChildren(self):
        return self.mChildrenClsNameList
    
    def hasChild(self, child):
        for ch in self.mChildrenClsNameList:
            if ch == child:
                return True
        return False
        
    def getEntryList(self, type = None, filterInList = None, filterOutList = None, maxSize=0):
        entryList = self.mParser.getEntryList()
        if type is None:
            return entryList
        
        outEntryList = []
        for entry in entryList:
            if entry.getType() == type:
                if filterInList is not None and not entry.hasKeyList(filterInList):
                    continue
                
                if filterOutList is not None and entry.hasKeyList(filterOutList):
                    continue
                    
                outEntryList.append(entry)
                if maxSize > 0 and len(outEntryList) >= maxSize:
                    break;

        return outEntryList
    
    def getEntry(self, type, name, filterInList = None, filterOutList = None):
        for entry in self.getEntryList(type, filterInList, filterOutList):
            if entry.getName() == name:
                return entry
        return None
    
    def hasEntry(self, type, name, filterInList = None, filterOutList = None):
        return self.getEntry(type, name, filterInList, filterInList) is not None;
    
    def hasMethod(self, name, filterInList = None, filterOutList = None):
        return self.hasEntry(SmaliEntry.METHOD, name, filterInList, filterOutList)
    
    def hasField(self, name, filterInList = None, filterOutList = None):
        return self.hasEntry(SmaliEntry.FIELD, name, filterInList, filterOutList)

    def getEntryNameList(self, type = None, filterInList = None, filterOutList = None):
        outEntryList = []
        for entry in self.getEntryList(type, filterInList, filterOutList):
            outEntryList.append(entry.getName())
        return outEntryList
    
    def getMethodsNameList(self, filterInList = None, filterOutList = None):
        return self.getEntryNameList(SmaliEntry.METHOD, filterInList, filterOutList)
    
    def getAbstractMethodsNameList(self):
        return self.getMethodsNameList([KEY_ABSTRACT])
    
    def isAbstractClass(self):
        entryList = self.getEntryList(SmaliEntry.CLASS, [KEY_ABSTRACT])
        assert len(entryList) <= 1, "Error: should has only one class define"
        return len(entryList) == 1
    
    def isInterface(self):
        entryList = self.getEntryList(SmaliEntry.CLASS, [KEY_INTERFACE])
        assert len(entryList) <= 1, "Error: should has only one class define"
        return len(entryList) == 1
    
    def getSuperClassName(self):
        if self.mSuperClassName is None:
            entryList = self.getEntryList(SmaliEntry.SUPER, None, None, 1)
        
            if len(entryList) == 1:
                self.mSuperClassName = entryList[0].getName()
            else:
                # java/lang/Object doesn't have super
                if SmaliParser.getClassFromPath(self.mPath) != DEFAULT_SUPER:
                    if not self.mIsPartSmali:
                        print "Wrong smali, should define the super! (%s)" % (self.mPath)
                    self.mSuperClassName = DEFAULT_SUPER
                else:
                    self.mSuperClassName = None
        return self.mSuperClassName
        
    def getImplementClassList(self):
        if self.mImplementsClassList is None:
            self.mImplementsClassList = []
            for entry in self.getEntryList(SmaliEntry.IMPLEMENTS):
                self.mImplementsClassList.append(entry.getName())
        
        return self.mImplementsClassList

    def getSuperAndImplementsClassName(self):
        clsNameList = []
        superClsName = self.getSuperClassName()
        
        if superClsName is not None:
            clsNameList.append(superClsName)
            
        implementsEntryList = self.getEntryList(SmaliEntry.IMPLEMENTS)
        for entry in implementsEntryList:
            clsNameList.append(entry.getName())
        
        return clsNameList
        
    def getPath(self):
        return self.mPath
    
    def removeEntryByName(self, type, name):
        entry = self.getEntry(type, name)
        return self.mParser.removeEntry(entry)
    
    def removeEntry(self, entry):
        return self.mParser.removeEntry(entry)
    
    def addEntry(self, entry):
        return self.mParser.addEntry(entry)

    def getClassName(self):
        if self.mClassName is None:
            entryList = self.getEntryList(SmaliEntry.CLASS, None, None, 1)
        
            if len(entryList) != 1:
                if not self.mIsPartSmali:
                    print "Warning: should has only one class define! (%s)" %(self.mPath)
                self.mClassName = SmaliParser.getClassFromPath(self.getPath())
            else:
                self.mClassName = entryList[0].getName()
        return self.mClassName
    
    def getClassBaseName(self):
        return SmaliParser.getClassBaseNameFromPath(self.getPath())
    
    def getSourceName(self):
        if self.mSourceName is None:
            entryList = self.getEntryList(SmaliEntry.SOURCE, None, None, 1)
        
            assert len(entryList) == 1
            self.mSourceName = entryList[0].getName()
        return self.mSourceName
    
    def getJarName(self):
        return SmaliParser.getJarNameFromPath(self.getPath())
    
    def getPackageName(self):
        if self.mPackageName is None:
            self.mPackageName = SmaliParser.getPackageFromClass(self.getClassName())
            
        return self.mPackageName;
    
    def __getInvokeMethods__(self):
        invokeMethodsList = []
        for entry in self.getEntryList(SmaliEntry.METHOD):
            invokeMethodsList.extend(entry.getInvokeMethods())
        return list(set(invokeMethodsList))
    
    def getInvokeMethods(self, filterInList = None):
        if self.mInvokeMethods is None:
            self.mInvokeMethods = self.__getInvokeMethods__()
        
        if filterInList is None:
            return self.mInvokeMethods
        
        outInvokeMethodsList = []
        for invokeItem in self.mInvokeMethods:
            for k in filterInList:
                if k == invokeItem.type:
                    outInvokeMethodsList.append(invokeItem)
                    break;
        
        return outInvokeMethodsList
    
    def __getUsedFields__(self):
        usedFieldsList = []
        for entry in self.getEntryList(SmaliEntry.METHOD):
            usedFieldsList.extend(entry.getUsedFields())
        return usedFieldsList
    
    def getUsedFields(self, filterInList = None):
        if self.mUsedFields is None:
            self.mUsedFields = self.__getUsedFields__()
            
        if filterInList is None:
            return self.mUsedFields
        
        outUsedMethodsList = []
        for usedFieldItem in self.mUsedFields:
            for k in filterInList:
                if k == usedFieldItem.type:
                    outUsedMethodsList.append(usedFieldItem)
                    break;
        
        return outUsedMethodsList
    
    def getUsedOutsideFields(self):
        if self.mUsedOutsideFields is None:
            usedFileds = self.getUsedFields()
            usedOutsideFields = []
            for usedFieldItem in usedFileds:
                if not usedFieldItem.cls == self.getClassName() or not self.hasField(usedFieldItem.field):
                    usedOutsideFields.append(usedFieldItem)
            self.mUsedOutsideFields = usedOutsideFields
        return self.mUsedOutsideFields
    
    def getAllMethods(self):
        return self.mAllMethods;

    def setAllMethods(self, allMethods):
        self.mAllMethods = allMethods

    def toString(self, entryList=None):
        if entryList is None:
            entryList = self.getEntryList()
        
        outContent = Content()
        for entry in self.getEntryList(): 
            outContent.append(entry.toString())
        if outContent.getContentStr() is not None:
            outContent.append("")
        return outContent.getContentStr()
    
    def toStringByType(self, type):
        return self.toString(self.getEntryList(type))
    
    # not finish
    def split(self, outdir):
        """ Return the sorted partition list.
        """

        sName = os.path.basename(self.mPath)[:-6]

        if False: print ">>> begin split file: %s to %s" %(self.mPath, outdir)

        partList = []

        sHeadFile = file('%s/%s.head' % (outdir, sName), 'w+')
        partList.append(sHeadFile.name)

        for entry in self.getEntryList():
            entryStr = entry.toString()
            if entryStr is None:
                continue

            if entry.getType() == SmaliEntry.METHOD:
                methodFilePath = getHashMethodPath(sName, entry, outdir)
                partList.append(methodFilePath)

                sMethodFile = file(methodFilePath, 'w+')
                sMethodFile.write("%s\n" %entryStr)
                sMethodFile.close()
            else:
                sHeadFile.write("%s\n" %entryStr)
        sHeadFile.close()

        return partList

    def format(self, formatMap):
        modified = False
        for entry in self.getEntryList():
            if entry.format(formatMap):
                modified = True
        return modified

    def out(self, outPath = None):
        if outPath is None:
            outPath = self.getPath()
        sFile = file(outPath, "w+")
        sFile.write(self.toString())
        sFile.close()

DEFAULT_HASH_LEN = 6
def getHashCode(name, len = DEFAULT_HASH_LEN):
    return hashlib.md5(name).hexdigest()[:len]

def getHashMethodPath(sName, entry, outdir):
    eName = entry.getName()
    mName = eName.split(r'(')[0]
    sMethodPath = '%s/%s.%s.%s' %(outdir, sName, mName, getHashCode(eName))
    idx=1
    while os.path.isfile(sMethodPath):
        sMethodPath = '%s/%s.%s.%s.%s' %(outdir, sName, mName, getHashCode(eName), idx)
        idx = idx + 1
    return sMethodPath