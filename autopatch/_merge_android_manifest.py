#!/usr/bin/python
# Filename: _merger_android_manifest.py

### File Information ###

"""
Merge the framework-res/AndroidManifest.xml automatically.

@hide

"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'

### File Information ###



### import block ###

import os
import sys

from xml.dom import minidom

### import block ###



### prologue ###

def merge(dstXML):

    srcXML = os.getcwd() + "/baidu/smali/framework-res/AndroidManifest.xml"
    # Parse out the Element tree
    srcXMLDom = minidom.parse(srcXML)
    dstXMLDom = minidom.parse(dstXML)

    # Replace the application node
    srcApplication = srcXMLDom.getElementsByTagName("application")[0]
    dstApplication = dstXMLDom.getElementsByTagName("application")[0]
    manifest = dstXMLDom.getElementsByTagName("manifest")[0]
    manifest.replaceChild(srcApplication, dstApplication)

    # Write the XML
    writexml(dstXML, dstXMLDom)

def writexml(xmlPath, xmlDom):
    f = open(xmlPath, 'w')
    xmlDom.writexml(f)
    f.close()

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "Error argv. " + sys.argv
        sys.exit(1)

    merge(sys.argv[1])

### prologue ###
