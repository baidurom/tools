'''
Created on Apr 4, 2014

@author: tangliuxiang
'''
import SCheck
import os
import sys
import Smali
import SmaliParser
import SmaliEntry
import SmaliMethod
import SmaliEntryFactory
import Content
import re

sys.path.append('%s/autopatch' %os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from log import Log
from xml.dom import minidom

class SAutoCom(object):
    '''
    classdocs
    '''
    AUTCOMPLETE_XML = r'%s/autocomplete.xml' %(os.path.dirname(os.path.abspath(__file__)))
    BLANK_ENTRY = None
        
    @staticmethod
    def autocom(vendorDir, aospDir, bospDir, mergedDir, outdir, comModuleList):
        #SAutoCom.parseAutoComXml()
        sCheck = SCheck.SCheck(vendorDir, aospDir, bospDir, mergedDir)
    
        for module in comModuleList:
            needComleteDir = '%s/%s' %(mergedDir, module)
            sDict = SmaliParser.getSmaliDict(needComleteDir)
            for clsName in sDict.keys():
                mSmali = sCheck.mMSLib.getSmali(clsName)
                if mSmali is None:
                    Log.e("can not get class: %s" %clsName)
                    continue
            
                (canReplaceEntryList, canNotReplaceEntryList) = sCheck.autoComplete(mSmali)
            
                for entry in canReplaceEntryList:
                    SAutoCom.replaceEntry(sCheck, entry, SAutoCom.getAutocomPartPath(sCheck, entry, outdir))
                
                for entry in canNotReplaceEntryList:
                    SAutoCom.appendBlankEntry(entry, SAutoCom.getAutocomPartPath(sCheck, entry, outdir))
    
    @staticmethod
    def getAutocomPartPath(sCheck, entry, outdir):
        cls = entry.getClassName()
        cSmali = sCheck.mVSLib.getSmali(cls)
                
        if cSmali is None:
            Log.e("can not get class %s from: %s" % (cls, sCheck.mVSLib.getPath()))
            return
    
        jarName = cSmali.getJarName()
        pkgName = cSmali.getPackageName()
        
        return r'%s/%s/smali/%s/%s.smali.part' % (outdir, jarName, pkgName, cSmali.getClassBaseName()) 
    
    @staticmethod
    def replaceEntry(sCheck, entry, outFilePath):
        Log.i(" ADD %s" % (entry.getSimpleString()))

        dirName = os.path.dirname(outFilePath)
        if not os.path.isdir(dirName):
            os.makedirs(os.path.dirname(outFilePath))

        partSmali = Smali.Smali(outFilePath)
        partSmali.replaceEntry(entry)
        partSmali.out()
    
    @staticmethod
    def parseAutoComXml():
        assert os.path.isfile(SAutoCom.AUTCOMPLETE_XML), "%s doesn't exist! Are you remove it?" %(SAutoCom.AUTCOMPLETE_XML)
        root = minidom.parse(SAutoCom.AUTCOMPLETE_XML).documentElement
        
        SAutoCom.BLANK_ENTRY = {}

        for item in root.childNodes:
            if item.nodeType == minidom.Node.ELEMENT_NODE:
                if not SAutoCom.BLANK_ENTRY.has_key(item.nodeName):
                    SAutoCom.BLANK_ENTRY[item.nodeName] = {}
                
                if item.nodeName == SmaliEntry.METHOD:
                    returnType = item.getAttribute("return")
                    contentStr = item.getAttribute("content")
                    outStr = re.sub(r'^ ', '', contentStr, 0, re.M)
                    SAutoCom.BLANK_ENTRY[item.nodeName][returnType] = outStr
                else:
                    Log.w("Doesn't support %s in %s" %(item.nodeName, SAutoCom.AUTCOMPLETE_XML))
    
    @staticmethod    
    def __getBlankContentStr__(entry):
        returnType = entry.getReturnType()
        if SAutoCom.BLANK_ENTRY[entry.getType()].has_key(returnType):
            return SAutoCom.BLANK_ENTRY[entry.getType()][returnType]
        else:
            for key in SAutoCom.BLANK_ENTRY[entry.getType()].keys():
                if re.match(key, returnType) is not None:
                    return SAutoCom.BLANK_ENTRY[entry.getType()][key]
        return None

    @staticmethod
    def getBlankContent(entry):
        content = Content.Content()
        if entry.getType() == SmaliEntry.METHOD:
            contentStr = SAutoCom.__getBlankContentStr__(entry)

            if contentStr is not None:
                content.append(entry.getFirstLine())
                content.append(contentStr)

        return content

    @staticmethod
    def appendBlankEntry(entry, outFilePath):
        Log.i(" ADD BLANK %s" % (entry.getSimpleString()))
        
        if SAutoCom.BLANK_ENTRY is None:
            SAutoCom.parseAutoComXml()
        
        if not SAutoCom.BLANK_ENTRY.has_key(entry.getType()) or entry.getType() != SmaliEntry.METHOD:
            Log.e("Doesn't support add blank %s in autocomplete")
            return

        dirName = os.path.dirname(outFilePath)
        if not os.path.isdir(dirName):
            os.makedirs(os.path.dirname(outFilePath))

        partSmali = Smali.Smali(outFilePath)
        nEntry = SmaliEntryFactory.newSmaliEntry(entry.getType(), SAutoCom.getBlankContent(entry), entry.getClassName(), entry.getPreContent())
        partSmali.replaceEntry(nEntry)
        partSmali.out()
