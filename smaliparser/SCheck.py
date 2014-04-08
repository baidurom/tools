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
import SAutoCom

sys.path.append('%s/autopatch' %os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import Log

class Options(object): pass
OPTIONS = Options()
OPTIONS.autoComplete = False

OPTIONS.formatSmali = False
OPTIONS.libraryPath = None
OPTIONS.filterOutDir = []

OPTIONS.replaceMethod = False

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
        canReplaceEntryList = []
        canNotReplaceEntryList = []
        if unImplementMethods is not None and len(unImplementMethods) > 0:
            vSmali = self.mVSLib.getSmali(smali.getClassName())
            if vSmali is None:
                Log.e("Can't get smali %s from vendor: %s"  %(smali.getClassName(), string.join(unImplementMethods)))
                return canReplaceEntryList
            
            unImplMethodEntryList = getEntryListByNameList(vSmali, SmaliEntry.METHOD, unImplementMethods)
            (canReplaceEntryList, canNotReplaceEntryList) = getCanReplaceMethods(self.mMSLib, self.mVSLib, smali.getClassName(), unImplMethodEntryList)
        
            for entry in canReplaceEntryList:
                Log.d("   Can Replace: %s" %(entry.getSimpleString()))

            for entry in canNotReplaceEntryList:
                Log.d("   Can not Replace: %s" %(entry.getSimpleString()))

        return (canReplaceEntryList, canNotReplaceEntryList)
        
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
            Log.d("class: %s doesn't have method: %s" % (invokeItem.cls, invokeItem.method))
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
            Log.d("class: %s doesn't have field: %s" % (usedFieldItem.cls, usedFieldItem.field))
            missedFields.append(usedFieldItem)
    return missedFields

# targetLib is which you already merged 
# sourceLib is which you want get the replace method
def getCanReplaceMethods(targetLib, sourceLib, clsName, methodEntryList):
    canReplaceEntryList = []
    canNotReplaceEntryList = []
    for mEntry in methodEntryList:
        methodName = mEntry.getName()
        Log.d("Check if can replace method: %s in class: %s" %(methodName, clsName))

        if mEntry is None:
            Log.e("Baidu doesn't have this Method: %s" %clsName)
            continue
        
        try:
            missedFields = getMissedFields(targetLib, mEntry.getUsedFields())
            canIgnore = True
            outMissedFieldsList = []
            for usedField in missedFields:
                if not SmaliMethod.isPutUseField(usedField):
                    canIgnore = False
                    break
                else:
                    cSmali = sourceLib.getSmali(usedField.cls)
                    if cSmali is None:
                        canIgnore = False
                        break

                    fieldEntry = cSmali.getEntry(SmaliEntry.FIELD, usedField.field)
                    if fieldEntry is None:
                        canIgnore = False
                        break

                    outMissedFieldsList.append(fieldEntry)
            if canIgnore:
                canReplaceEntryList.extend(outMissedFieldsList)
            else:
                canNotReplaceEntryList.append(mEntry)
                continue
        except Exception as e:
            Log.d(e)
            canNotReplaceEntryList.append(mEntry)
            Log.d("can not replace method: %s in class: %s" %(methodName, clsName))
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
                if cSmali is None:
                    canNotReplaceEntryList.append(mEntry)
                    break

                entryList = getEntryListByNameList(cSmali, SmaliEntry.METHOD, missedMethodDict[cls])
                (cEntryList, nEntryList) = getCanReplaceMethods(targetLib, sourceLib, cls, entryList)
                canReplaceEntryList.extend(cEntryList)
                canNotReplaceEntryList.extend(nEntryList)
            canReplaceEntryList.append(mEntry)
            missedMethodDict.clear()
        except Exception as e:
            Log.d(e)
            canNotReplaceEntryList.append(mEntry)
            Log.d("Warning: can not replace method: %s in class: %s" %(methodName, clsName))
            continue

    return list(set(canReplaceEntryList)), list(set(canNotReplaceEntryList))

def formatSmali(smaliLib, smaliFileList = None):
    Log.i("    begin format smali files, please wait....")
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
    Log.i("    format done")

def replace(src, dst, type, name):
    srcSmali = Smali.Smali(src)
    dstSmali = Smali.Smali(dst)

    if srcSmali is None:
        Log.e("%s doesn't exist or is not smali file!" %src)
        return False

    if dstSmali is None:
        Log.e("%s doesn't exist or is not smali file!" %dst)
        return False

    name = name.split()[-1]
    srcEntry = srcSmali.getEntry(type, name)
    if srcEntry is not None:
        Log.i("Replace %s %s from %s to %s" %(type, name, src, dst))
        dstSmali.replaceEntry(srcEntry)
        dstSmali.out()
        return True
    else:
        Log.e("Can not get %s:%s from %s" %(type, name, src))
        return False

def replaceMethod(src, dst, methodName):
    replace(src, dst, SmaliEntry.METHOD, methodName)

def usage():
    pass

def main(argv):
    options,args = getopt.getopt(argv[1:], "hafl:s:t:r", [ "help", "autocomplete", "formatsmali", "library", "smali", "filter", "replacemethod"])
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
        else:
            Log.w("Wrong parameters, see the usage....")
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
            formatSmali(SmaliLib.SmaliLib(OPTIONS.libraryPath), args)
        else:
            formatSmali(SmaliLib.SmaliLib(OPTIONS.libraryPath), None)
    elif OPTIONS.replaceMethod:
        if len(args) >= 3:
            replaceMethod(args[0], args[1], args[2])

if __name__ == "__main__":
    if len(sys.argv) > 2:
        main(sys.argv)
    else:
        usage()
