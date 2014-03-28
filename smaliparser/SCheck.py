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
import SmaliParser
import os
import getopt

class Options(object): pass
OPTIONS = Options()
OPTIONS.autoComplete = False

OPTIONS.formatSmali = False
OPTIONS.libraryPath = None
OPTIONS.filterOutDir = []

MAX_CHECK_INVOKE_DEEP = 50
class SCheck(object):
    '''
    classdocs
    '''


    def __init__(self, vendorDir, aospDir, bospDir, mergedDir):
        '''
        Constructor
        '''
        self.mVSLib = SmaliLib.SmaliLib(vendorDir)
        self.mASLib = SmaliLib.SmaliLib(aospDir)
        self.mBSLib = SmaliLib.SmaliLib(bospDir)
        self.mMSLib = SmaliLib.SmaliLib(mergedDir)
    
    def autoComplete(self, smali):
        unImplementMethods = self.getUnImplementMethods(smali)
        canReplaceMethods = []
        if unImplementMethods is not None and len(unImplementMethods) > 0:
            vSmali = self.mVSLib.getSmali(smali.getClassName())
            assert vSmali is not None, "Error: Can't get smali %s from vendor: %s"  %(smali.getClassName(), string.join(unImplementMethods))
            
            unImplMethodEntryList = getEntryListByNameList(vSmali, SmaliEntry.METHOD, unImplementMethods)
            canReplaceMethods = getCanReplaceMethods(self.mMSLib, self.mVSLib, smali.getClassName(), unImplMethodEntryList)
        
            for method in canReplaceMethods:
                print "Can Replace: class: %s, method: %s" %(method.getClassName(), method.getName())
        return canReplaceMethods
        
    def getUnImplementMethods(self, smali):
        return getUnImplementMethods(self.mASLib, self.mMSLib, smali)
        
    def getCanReplaceToBaiduMethods(self, smali, methodEntryList):
        return getCanReplaceMethods(self.mMSLib, self.mBSLib, smali.getClassName(), methodEntryList)
    
def getEntryListByNameList(smali, type, nameList):
    outList = []
    for entry in smali.getEntryList(type):
        for name in nameList:
            if name == entry.getName():
                outList.append(entry)
                break
    return outList
    
def isMethodUsed(asLib, sLib, smali, methodName, deep = 0):
    sMethodEntry = smali.getEntry(SmaliEntry.METHOD, methodName)
    if sMethodEntry is not None:
        aSmali = asLib.getSmali(smali.getClassName())
        if aSmali is not None and aSmali.getEntry(SmaliEntry.METHOD, methodName) is not None:
            return True
            
        usedMethodsList = sLib.getUsedMethods(smali, [sMethodEntry])
            
        if not usedMethodsList.has_key(methodName):
            for childClsName in smali.getChildren():
                cSmali = sLib.getSmali(childClsName)
                if cSmali is not None and isMethodUsed(asLib, sLib, cSmali, methodName):
                    return True
        else:
            if len(usedMethodsList) < Smali.MAX_INVOKE_LEN and deep < MAX_CHECK_INVOKE_DEEP:
                isUsed = False
                for invokeItem in usedMethodsList[methodName]:
                    cSmali = sLib.getSmali(invokeItem.belongCls)
                    if cSmali is not None and isMethodUsed(asLib, sLib, cSmali, invokeItem.belongMethod, deep + 1):
                        isUsed = True
                        break
                return isUsed
            else:
                return True
    return False

def getUnImplementMethods(asLib, sLib, smali):
    unImplementMethods = []
    methodsList = sLib.__getUnImplementMethods__(smali, sLib.getAllMethods(smali))
    for key in methodsList.keys():
        if len(methodsList[key]) >= Smali.MAX_INVOKE_LEN:
            unImplementMethods.append(key)
            continue

        for invokeItem in methodsList[key]:
            cSmali = sLib.getSmali(invokeItem.belongCls)
            if cSmali is None:
                continue
                
            if isMethodUsed(asLib, sLib, cSmali, invokeItem.belongMethod):
                unImplementMethods.append(key)
                break
    return unImplementMethods

def getMissedMethods(sLib, invokeMethods):
    missedMethods = []
    for invokeItem in invokeMethods:
        cSmali = sLib.getSmali(invokeItem.cls)
        assert cSmali is not None, "Error: doesn't have class: %s" % invokeItem.cls
            
        hasMethod = False
        for mEntry in sLib.getAllMethods(cSmali):
            if invokeItem.method == mEntry.getName():
                hasMethod = True
                break
        if not hasMethod:
            print "Warning: class: %s doesn't have method: %s" % (invokeItem.cls, invokeItem.method)
            missedMethods.append(invokeItem)
    return missedMethods

def getMissedFields(sLib, usedFields):
    missedFields = []
    for usedFieldItem in usedFields:
        cSmali = sLib.getSmali(usedFieldItem.cls)
        assert cSmali is not None, "Error: doesn't have class: %s" % usedFieldItem.cls

        hasField = False
        for mEntry in sLib.getAllFields(cSmali):
            if usedFieldItem.field == mEntry.getName():
                hasField = True
                break
        if not hasField:
            print "Warning: class: %s doesn't have field: %s" % (usedFieldItem.cls, usedFieldItem.field)
            missedFields.append(usedFieldItem)
    return missedFields

# targetLib is which you already merged 
# sourceLib is which you want get the replace method
def getCanReplaceMethods(targetLib, sourceLib, clsName, methodEntryList):
    outEntryList = []
    for mEntry in methodEntryList:
        methodName = mEntry.getName()
        print "Check if can replace method: %s in class: %s" %(methodName, clsName)

        if mEntry is None:
            print ">>>> Warning: Baidu doesn't have this Method: %s" %clsName
            continue
        
        try:
            missedFields = getMissedFields(targetLib, mEntry.getUsedFields())
            hasGetField = False
            outMissedFieldsList = []
            for usedField in missedFields:
                if not SmaliMethod.isPutUseField(usedField):
                    hasGetField = True
                    break
                else:
                    cSmali = sourceLib.getSmali(usedField.cls)
                    assert cSmali is not None,  "Error: doesn't have class: %s" % usedField.cls
                    fieldEntry = cSmali.getEntry(SmaliEntry.FIELD, usedField.field)
                    assert fieldEntry is not None,  "Error: doesn't have field: %s in class: %s" % (usedField.field, usedField.cls)
                    outMissedFieldsList.append(fieldEntry)
            if hasGetField:
                print "Warning: can not replace method: %s in class: %s" %(methodName, clsName)
                continue
            outEntryList.extend(outMissedFieldsList)
        except:
            print "Warning: can not replace method: %s in class: %s" %(methodName, clsName)
            continue
        
        try:
            missedMethods = getMissedMethods(targetLib, mEntry.getInvokeMethods())
            missedMethodDict = {}
            for invokeItem in missedMethods:
                if not missedMethodDict.has_key(invokeItem.cls):
                    missedMethodDict[invokeItem.cls] = []
                missedMethodDict[invokeItem.cls].append(invokeItem.method)
            for cls in missedMethodDict.keys():
                cSmali = sourceLib.getSmali(cls)
                assert cSmali is not None, "Error: doesn't have class: %s" % cls
                entryList = getEntryListByNameList(cSmali, SmaliEntry.METHOD, missedMethodDict[cls])
                outEntryList.extend(getCanReplaceMethods(targetLib, sourceLib, cls, entryList))
            outEntryList.append(mEntry)
            missedMethodDict.clear()
        except:
            print "Warning: can not replace method: %s in class: %s" %(methodName, clsName)
            continue

    return list(set(outEntryList))

def autoComplete(vendorDir, aospDir, bospDir, mergedDir, outdir, comModuleList):
    sCheck = SCheck(vendorDir, aospDir, bospDir, mergedDir)
    
    for module in comModuleList:
        needComleteDir = '%s/%s' %(mergedDir, module)
        sDict = SmaliParser.getSmaliDict(needComleteDir)
        for clsName in sDict.keys():
            mSmali = sCheck.mMSLib.getSmali(clsName)
            assert mSmali is not None, "Error: can not get class: %s" %clsName
            canReplaceEntryList = sCheck.autoComplete(mSmali)
            for entry in canReplaceEntryList:
                outStr = "%s\n" %entry.toString()
                assert outStr is not None, "Error: Life is hard...."
                
                cls = entry.getClassName()
                cSmali = sCheck.mVSLib.getSmali(cls)
                assert cSmali is not None, "Error: can not get class %s from: %s" %(cls, sCheck.mVSLib.getPath())
                jarName = cSmali.getJarName()
                pkgName = cSmali.getPackageName()
                
                outFilePath = r'%s/%s/smali/%s/%s.smali.part' %(outdir, jarName, pkgName, cSmali.getClassBaseName())
                
                print ">>> begin auto compelete class:%s %s:%s to %s" %(cls, entry.getType(), entry.getName(), outFilePath)
                
                dirName = os.path.dirname(outFilePath)
                if not os.path.isdir(dirName):
                    os.makedirs(os.path.dirname(outFilePath))
                
                outFile = None
                if os.path.isfile(outFilePath):
                    oldSmali = Smali.Smali(outFilePath)
                    if oldSmali.removeEntryByName(entry.getType(), entry.getName()):
                        outFile = file(outFilePath, 'w+')
                        oldSmali.addEntry(entry)
                        outStr = oldSmali.toString()
                
                if outFile is None:
                    outFile = file(outFilePath, 'a+')
                
                outFile.write(outStr)
                outFile.close()

def formatSmali(smaliLib, smaliFileList = None):

    print ">>> begin format smali files, please wait...."
    if smaliFileList is not None:
        idx = 0
        while idx < len(smaliFileList):
            clsName = SmaliParser.getClassFromPath(smaliFileList[idx])
            cSmali = smaliLib.getSmali(clsName)
            smaliLib.format(cSmali)
            idx = idx + 1
    else:
        for clsName in smaliLib.mSDict.keys():
            cSmali = smaliLib.getSmali(clsName)
            smaliLib.format(cSmali)
    print ">>> format done"

def usage():
    pass

def main(argv):
    options,args = getopt.getopt(argv[1:], "hafl:s:t:", [ "help", "autocomplete", "formatsmali", "library", "smali", "filter"])
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
        else:
            print "Wrong parameters, see the usage...."
            usage()
            exit(1)

    if OPTIONS.autoComplete:
        if len(args) >= 6:
            autoComplete(args[0], args[1], args[2], args[3], args[4], args[5:])
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
            formatSmali(OPTIONS.libraryPath, args, OPTIONS.filterOutDir)
        else:
            formatSmali(OPTIONS.libraryPath, None, OPTIONS.filterOutDir)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv)
    else:
        usage()