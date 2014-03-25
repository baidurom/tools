#!/usr/bin/python
# Filename: xml_patch.py

### File Information ###

"""
Merge the modifications defined in XML into target file.

@hide

This routine takes over two parameters.
  parameter 1 : file path of target smali to be merged
  parameter 2 : file path of XML defined modification  
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'


import sys
import re
import os

from config import Config, Log

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


### prologue ###

class XMLPatch():
    """ Entry of the script
    """

    def __init__(self):
        if len(sys.argv) < 3:
            print "Usage xml_patch.py TARGET PATCH"
            print "   - TARGET : the target file path to be patched"
            print "   - PATCH  : the patch file path"
            sys.exit(1)

        targetPath = sys.argv[1]
        patchPath  = sys.argv[2]

        Patcher(targetPath, patchPath).run()

# End of class XMLPatch


class Patcher:
    """ Execute the patch action
    """

    def __init__(self, targetPath, patchPath):

        self.mTargetPath = targetPath
        self.mPatchPath  = patchPath

        # Hold all the exceptions
        self.exceptions = []

    def run(self):
        """ Return True patched successfully. Otherwise return False
        """

        # Open the target file
        self.openTarget()

        # Open and parse the source ReviseXML file
        reviseXML = ReviseXML().parse(self.mPatchPath)
        for item in reviseXML.getItems():
            self.mergeItem(item)

        # Close the target file
        self.closeTarget()

        # Raise exceptions if happened
        Log.d(self.exceptions)
        return len(self.exceptions) == 0

    def mergeItem(self, item):
        """ Merge each item according to the item configuration.
        """

        # Find the nearby place if provided
        nearbyPos = self.getNearbyPos(item)

        # Find the anchor place
        resultMap = self.getAnchorPosAndContent(item, nearbyPos)
        if resultMap == None: return

        # Apply the modification
        self.applyMerge(item, resultMap['anchorStart'], resultMap['anchorEnd'], resultMap['content'])

    def getNearbyPos(self, item):
        """ Get the nearby position. If not found the nearby, 0 will be returned.
        """

        nearbyPos = 0
        nearby = ReviseXML.getItemAttrib(item, 'nearby')
        if nearby != None:
            nearbyPos = self.mTargetContent.find(nearby)

        if nearbyPos < 0:
            print "Can not find nearby " + nearby
            nearbyPos = 0

        return nearbyPos

    def getAnchorPosAndContent(self, item, nearbyPos):
        """ Get the anchor position from the nearby position,
            as well as the content to be merged.
        """

        anchor = item.attrib['anchor']
        matchType = ReviseXML.getItemAttrib(item, 'match')

        if anchor == "EOF":
            anchorStart = len(self.mTargetContent)
            anchorEnd = anchorStart
            content = item.text

        elif matchType == "REGEX":
            anchorRegex = re.compile(anchor)
            match = anchorRegex.search(self.mTargetContent[nearbyPos:])
            if match == None:
                anchorStart = -1
            else:
                anchorStart = nearbyPos + match.start()
                anchorEnd = nearbyPos + match.end()
                # Format the content text with match result
                content = item.text % match.groups()

        else:
            anchorStart = self.mTargetContent.find(anchor, nearbyPos)
            anchorEnd = anchorStart + len(anchor)
            content = item.text

        if anchorStart < 0:
            self.reject(item)
            return None

        return { "anchorStart" : anchorStart,
                 "anchorEnd"   : anchorEnd,
                 "content"     : content  }

    def applyMerge(self, item, anchorStart, anchorEnd, content):
        """ Merge the content to anchor position. 
        """

        action = item.attrib['action']
        position = ReviseXML.getItemAttrib(item, 'position')

        if self.isContentMerged(anchorStart, anchorEnd, content) == True :
            return

        if action == "ADD":
            if position == "OVER":
                self.mTargetContent = self.mTargetContent[:anchorStart] + content.rstrip() + "\n\n" + self.mTargetContent[anchorStart:]
            elif position == "BELOW":
                self.mTargetContent = self.mTargetContent[:anchorEnd] + "\n" + content.rstrip() + "\n" + self.mTargetContent[anchorEnd:]

        elif action == "REPLACE":
            self.mTargetContent = self.mTargetContent[:anchorStart]  + content.strip() + self.mTargetContent[anchorEnd:]

        elif action == "DEL":
            # TODO add Delete action
            pass

    def isContentMerged(self, anchorStart, anchorEnd, content):
        """ Check whether content is merged
        """

        # Compute the range to search content
        contentLen = len(content)
        totalLen = len(self.mTargetContent)

        rangeStart = anchorStart - contentLen
        if rangeStart < 0 : rangeStart = 0

        rangeEnd = anchorEnd + contentLen
        if rangeEnd > totalLen : rangeEnd = totalLen


        # Content already exist in the specific range, means already merged
        if self.mTargetContent[rangeStart:rangeEnd].find(content.strip()) >= 0:
            return True

        return False

    def openTarget(self):
        """ Open the destination file in read and write mode
            Read the file content and create a buffer
        """

        self.mTargetFile = open(self.mTargetPath, 'r+')
        self.mTargetContent = self.mTargetFile.read()

    def closeTarget(self):
        """ Update the file content , and flush the destination file to disk
        """

        self.mTargetFile.truncate(0)
        self.mTargetFile.seek(0)
        self.mTargetFile.write(self.mTargetContent)
        self.mTargetFile.flush()
        self.mTargetFile.close()

    def raiseExceptions(self):
        """ Raise the exceptions if exists. 
        """

        if len(self.exceptions) > 0:
            raise KeyError(self.exceptions)

    def reject(self, item):
        """ Reject the item. Write the reject information into reject file.
        """

        # Open the the reject file with append mode
        relTarget = os.path.relpath(self.mTargetPath, Config.PRJ_ROOT)
        rejFilename = os.path.join(Config.REJ_ROOT, relTarget + ".reject")
        dirname = os.path.dirname(rejFilename)
        if not os.path.exists(dirname): os.makedirs(dirname)
        rejFileHandle = open(rejFilename, "a")

        # Write the reject content
        action = ReviseXML.getItemAttrib(item, 'action')
        nearby = ReviseXML.getItemAttrib(item, 'nearby')
        anchor = ReviseXML.getItemAttrib(item, 'anchor')
        position = ReviseXML.getItemAttrib(item, 'position')
        matchType = ReviseXML.getItemAttrib(item, 'match')
        content = item.text

        # Compose the reject text
        buf = ""
        if nearby != None:
            buf += "\n# [IN METHOD] : " + nearby

        buf += "\n# [ ANCHOR  ] : " + anchor

        if matchType != None and matchType == "REGEX":
            buf += "\n# [ATTENTION] : SHOULD USE REGEX TO MATCH THE ANCHOR IN " + os.path.basename(relTarget)

        buf += "\n# [ ACTION  ] : " + action
        if position != None:
            buf += " THE FOLLOWING CODE " + position + " ANCHOR \n"
        elif action == "REPLACE":
            buf += " ANCHOR WITH THE FOLLOWING CODE \n"

        buf += content
        buf += "\n# -----------------------------------------------------------\n"

        # Close the the reject file
        rejFileHandle.write(buf)
        rejFileHandle.close()

        # Append the exception
        self.exceptions.append("Can not find anchor " + anchor + " in " + self.mTargetPath)

# End of class Patcher


class ReviseXML:
    """ Represents the XML model declared the content to be merged.
    """

    def __init__(self):
        pass

    def parse(self, xmlFile):
        self.tree = ET.parse(xmlFile)
        return self

    def getItems(self):
        return self.tree.findall('item')

    @staticmethod
    def getItemAttrib(item, key):
        try:
            return item.attrib[key]
        except KeyError:
            return None
# End of class ReviseXML


# End of class Rejecter

if __name__ == "__main__":
    XMLPatch()

### prologue ###



