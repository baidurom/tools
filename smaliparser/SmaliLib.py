'''
Created on Feb 28, 2014

@author: tangliuxiang
'''

import Smali
import SmaliEntry
import SmaliMethod
import string
import SmaliParser

DEBUG = False
class SmaliLib(object):
    '''
    classdocs
    '''

    def __init__(self, libPath):
        '''
        Constructor
        '''
        self.mSDict = SmaliParser.getSmaliDict(libPath)
        self.mCalledMethods = None
        self.mSmaliRoot = None
        self.mAlreadyParsedInvoke = False
        self.mPath = libPath
    
    def getPath(self):
        return self.mPath
        
    def getSmali(self, className):
        if self.mSDict.has_key(className):
            return self.mSDict[className]
        
        return None
    
    def getSuperSmali(self, child):
        return self.getSmali(child.getSuperClassName())
    
    def generateSmaliTree(self):
        if self.mSmaliRoot is None:
            self.mSmaliRoot = self.getSmali("Ljava/lang/Object;")
            for clsName in self.mSDict.keys():
                smali = self.getSmali(clsName)
                superClsName = smali.getSuperClassName()
                superSmali = self.getSmali(superClsName)
                if superSmali is not None:
                    superSmali.addChild(smali.getClassName())
    
    def getInheritMethods(self, child, filterInList = None, filterOutList = None):
        methodsList = []
        
        for clsName in child.getSuperAndImplementsClassName():
            superSmali = self.getSmali(clsName)
            if superSmali is None:
                if DEBUG:
                    print "Warning: can not get %s's super class: %s" %(child.getClassName(), clsName)
                continue
            
            methodsList.extend(self.getInheritMethods(superSmali, filterInList, filterOutList))
            methodsList.extend(superSmali.getEntryList(SmaliEntry.METHOD, filterInList, filterOutList))
        
        return methodsList
    
    def getAllMethods(self, smali):
        superFilterOutList = [Smali.KEY_PRIVATE]
        if not smali.isInterface() and not smali.isAbstractClass():
            superFilterOutList.append(Smali.KEY_ABSTRACT)
        methodsList = self.getInheritMethods(smali, None, superFilterOutList)
        methodsList.extend(smali.getEntryList(SmaliEntry.METHOD))
        
        return methodsList
    
    def getAllFields(self, smali):
        fieldsList = smali.getEntryList(SmaliEntry.FIELD)
        for clsName in self.getAllFathers(smali):
            cSmali = self.getSmali(clsName)
            if cSmali is not None and not cSmali.isInterface():
                fieldsList.extend(cSmali.getEntryList(SmaliEntry.FIELD, None, [Smali.KEY_PRIVATE]))
        return fieldsList
    
    def getNeedOverrideMethods(self, smali):
        overrideMethodsList = []
        
        superClsNameList = smali.getEntryNameList(SmaliEntry.IMPLEMENTS)
        superClsName = smali.getSuperClassName()
        
        if superClsName is not None:
            superClsNameList.append(superClsName)
        
        for clsName in superClsNameList:
            superSmali = self.getSmali(clsName)
            assert superSmali is not None, "Error: can not find class: %s" %(clsName)
            
            overrideMethodsList.extend(self.getNeedOverrideMethods(superSmali))
            overrideMethodsList.extend(superSmali.getAbstractMethodsNameList())
            
        return overrideMethodsList

    def __parseAllInvoke(self):
        if self.mAlreadyParsedInvoke:
            return

        self.generateSmaliTree()
        for clsName in self.mSDict.keys():
            smali = self.mSDict[clsName]
            for invokeItem in smali.getInvokeMethods():
                cSmali = self.getSmali(invokeItem.cls)
                if cSmali is not None:
                    cSmali.wasInvoke(invokeItem)
        self.mAlreadyParsedInvoke = True
    
    def getCalledMethod(self, smali):
        self.__parseAllInvoke()
        cSmali = self.getSmali(smali.getClassName())
        if cSmali is not None:
            return cSmali.getWasInvokeList()
        else:
            print "Warning: can not get class %s from smali lib" %(smali.getClassName())
            return []
        
    def getAllFathers(self, smali):
        if smali is None:
            return []
        allFathersList = []
        for clsName in smali.getSuperAndImplementsClassName():
            cSmali = self.getSmali(clsName)
            if cSmali is not None:
                allFathersList.extend(self.getAllFathers(cSmali))
                allFathersList.append(clsName)
        return list(set(allFathersList))
        
    def getAbstractMethodsNameList(self, smali):
        absMethodsNameList = smali.getAbstractMethodsNameList()
        for clsName in self.getAllFathers(smali):
            cSmali = self.getSmali(clsName)
            absMethodsNameList.append(cSmali.getAbstractMethodsNameList())
        return list(set(absMethodsNameList))
    
    def __getSuperCalledMethods__new(self, smali):
        superCalledMethods = {}
        for clsName in self.getAllFathers(smali):
            cSmali = self.getSmali(clsName)
            if cSmali.isInterface():
                if superCalledMethods.has_key(clsName):
                    superCalledMethods[clsName] = dict(superCalledMethods[clsName], **self.getCalledMethod(cSmali))
                else:
                    superCalledMethods[clsName] = self.getCalledMethod(cSmali)
            elif cSmali.isAbstractClass():
                absMethodsNameList = cSmali.getAbstractMethodsNameList()
                sCalledMethods = self.getCalledMethod(cSmali)
                
                for method in sCalledMethods.keys():
                    for absMethodName in absMethodsNameList:
                        if method == absMethodName:
                            if not superCalledMethods.has_key(cSmali):
                                superCalledMethods[cSmali] = {}
                            superCalledMethods[cSmali][method] = sCalledMethods[method]
                            break
        return superCalledMethods
        
    def __getSuperCalledMethods__(self, smali):
        superCalledMethods = {}
        
        superClsName = smali.getSuperClassName()
        if superClsName is not None and self.getSmali(superClsName) is not None:
            superSmali = self.getSmali(superClsName)
            sCalledMethods = self.getCalledMethod(superSmali)
            absMethodsNameList = superSmali.getAbstractMethodsNameList()
            superCalledMethods = self.__getSuperCalledMethods__(superSmali)
            
            for method in sCalledMethods.keys():
                for absMethodName in absMethodsNameList:
                    if method == absMethodName:
                        if not superCalledMethods.has_key(superClsName):
                            superCalledMethods[superClsName] = {}
                        superCalledMethods[superClsName][method] = sCalledMethods[method]
                        break
        
        for clsName in smali.getImplementClassList():
            superSmali = self.getSmali(clsName)
            if superSmali is not None:
                assert superSmali.isAbstractClass() and superSmali.isInterface(), "Error: class %s was implement by %s, it should be interface!" %(clsName, smali.getClassName())
                if superCalledMethods.has_key(clsName):
                    superCalledMethods[clsName] = dict(superCalledMethods[clsName], **self.getCalledMethod(superSmali))
                else:
                    superCalledMethods[clsName] = self.getCalledMethod(superSmali)
        return superCalledMethods
    
    def __dict(self, dict1, dict2):
        newDict = dict1.copy()
        for key in dict2.keys():
            if newDict.has_key(key):
                newDict[key].extend(dict2[key])
            else:
                newDict[key] = dict2[key]
        return newDict
    
    def __getSelfAndSuperCalledMethods__(self, smali):
        allCalledMethods = {}
        allCalledMethods[smali.getClassName()] = self.getCalledMethod(smali)
        if not smali.isInterface() and not smali.isAbstractClass():
            allCalledMethods = self.__dict(allCalledMethods, self.__getSuperCalledMethods__new(smali))
        return allCalledMethods
    
    def __getUnImplementMethods__(self, smali, selfMethods):
        usedMethodsList = {}
        allCalledMethodDict = self.__getSelfAndSuperCalledMethods__(smali)
        
        for clsName in allCalledMethodDict.keys():
            for method in allCalledMethodDict[clsName]:
                hasMethod = False
                for sMethod in selfMethods:
                    if method == sMethod.getName():
                        hasMethod = True
                        break;
                if hasMethod is False:
                    if not usedMethodsList.has_key(method):
                        usedMethodsList[method] = []
                    usedMethodsList[method].extend(allCalledMethodDict[clsName][method])

        return usedMethodsList
    
    def getUsedMethods(self, smali, selfMethods = None):
        if selfMethods is None:
            selfMethods = self.getAllMethods(smali)
        usedMethodsList = {}
        allCalledMethodDict = self.__getSelfAndSuperCalledMethods__(smali)
        for method in selfMethods:
            for clsName in allCalledMethodDict.keys():
                for methodName in allCalledMethodDict[clsName]:
                    if methodName == method.getName():
                        if not usedMethodsList.has_key(methodName):
                            usedMethodsList[methodName] = []
                        usedMethodsList[methodName].extend(allCalledMethodDict[clsName][methodName])
                        break
                    
                if usedMethodsList.has_key(method.getName()) and \
                len(usedMethodsList[method.getName()]) >= Smali.MAX_INVOKE_LEN:
                    break

        return usedMethodsList
    
    def checkMethods(self, smali):
#        if smali.isAbstractClass() or smali.isInterface():
#            return
        
        allCalledMethods = self.getCalledMethod(smali)
        if not smali.isInterface() and not smali.isAbstractClass():
            mergedDict = self.__dict(allCalledMethods, self.__getSuperCalledMethods__(smali))
            allCalledMethods = mergedDict
        
        for key in allCalledMethods.keys():
            splitArray = key.split(':')
            assert len(splitArray) == 2, "Life is hard...."
            type = splitArray[0]
            method = splitArray[1]
            
            hasMethod = False
            for sMethod in self.getAllMethods(smali):
                if method == sMethod.getName():
                    hasMethod = True
                    break;
            if hasMethod is False:
                print "Error: %s doesn't has method %s, was called by: %s" %(smali.getClassName(), method, string.join(allCalledMethods[key]))
                
                
def __getSplitItem__(string, sep, idx = 0):
    splitArray = string.split(sep)
    assert len(splitArray) > idx, "Life is hard...."
    return splitArray[idx]
        
