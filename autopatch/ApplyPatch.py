#!/usr/bin/python
# Filename: _merger_single_file.py

### File Information ###

"""
Merge the modifications defined in XML into target file.

@hide

This routine takes over two parameters.
parameter 1 : file path of target smali to be merged
parameter 2 : file path of XML defined modification  
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'

### File Information ###



### import block ###

import sys
import re
import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

### import block ###



### prologue ###

class ApplyPatch():
    """
    Entry of the script
    """

    def __init__(self):
        if len(sys.argv) < 3:
            print "Usage ApplyPatch.py TARGET PATCH"
            print "   - TARGET : the target file path to be patched"
            print "   - PATCH  : the patch file path"
            sys.exit(1)

        targetPath = sys.argv[1]
        patchPath = sys.argv[2]

        MergeExecutor(targetPath, patchPath).run()

# End of class Main


class MergeExecutor:
    """
    Execute the merge action
    """

    def __init__(self, targetPath, patchPath):

        self.mTargetPath = targetPath
        self.mPatchPath = patchPath

        # Hold all the exceptions
        self.exceptions = []
        # Handle reject files while merging
        self.rejectHandler = RejectHandler()

    def run(self):
        # Open the target file
        self.openTarget()

        # Open and parse the source PatchXML file
        patchXML = PatchXML().parse(self.mPatchPath)
        for item in patchXML.getItems():
            self.mergeItem(item)

        # Close the target file
        self.closeTarget()

        # Raise exceptions if happened
        self.raiseExceptions()

    def mergeItem(self, item):
        """
        Merge each item according to the item configuration.
        """

        # Find the nearby place if provided
        nearbyPos = self.getNearbyPos(item)

        # Find the anchor place
        resultMap = self.getAnchorPosAndContent(item, nearbyPos)
        if resultMap == None:
            return

        # Apply the modification
        self.applyMerge(item, resultMap['anchorStart'], resultMap['anchorEnd'], resultMap['content'])

    def getNearbyPos(self, item):
        """
        Get the nearby position. If not found the nearby, 0 will be returned.
        """

        nearbyPos = 0
        nearby = PatchXML.getItemAttrib(item, 'nearby')
        if nearby != None:
            nearbyPos = self.mTargetContent.find(nearby)

        if nearbyPos < 0:
            print "Can not find nearby " + nearby
            nearbyPos = 0

        return nearbyPos

    def getAnchorPosAndContent(self, item, nearbyPos):
        """
        Get the anchor position from the nearby position,
        as well as the content to be merged
        """

        anchor = item.attrib['anchor']
        matchType = PatchXML.getItemAttrib(item, 'match')

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
            self.exceptions.append("Can not find anchor " + anchor + " in " + self.mTargetPath)
            self.rejectHandler.reject(self.mTargetPath, item)
            return None

        return { "anchorStart" : anchorStart,
                 "anchorEnd"   : anchorEnd,
                 "content"     : content  }

    def applyMerge(self, item, anchorStart, anchorEnd, content):
        """
        Merge the content to anchor position. 
        """

        action = item.attrib['action']
        position = PatchXML.getItemAttrib(item, 'position')

        if action == "ADD":
            if position == "OVER":
                self.mTargetContent = self.mTargetContent[:anchorStart] + content + "\n" + self.mTargetContent[anchorStart:]
            elif position == "BELOW":
                self.mTargetContent = self.mTargetContent[:anchorEnd] + "\n" + content + self.mTargetContent[anchorEnd:]

        elif action == "REPLACE":
            self.mTargetContent = self.mTargetContent[:anchorStart]  + content.strip() + self.mTargetContent[anchorEnd:]

        elif action == "DEL":
            # TODO add Delete action
            pass

    def openTarget(self):
        """
        Open the destination file in read and write mode
        Read the file content and create a buffer
        """

        self.mTargetFile = open(self.mTargetPath, 'r+')
        self.mTargetContent = self.mTargetFile.read()

    def closeTarget(self):
        """
        Update the file content , and flush the destination file to disk
        """

        self.mTargetFile.truncate(0)
        self.mTargetFile.seek(0)
        self.mTargetFile.write(self.mTargetContent)
        self.mTargetFile.flush()
        self.mTargetFile.close()

    def raiseExceptions(self):
        """
        Raise the exceptions if exists. 
        """

        if len(self.exceptions) > 0:
            raise KeyError(self.exceptions)

# End of class MergeExecutor


class PatchXML:
    """
    Represents the XML file declare the content to be merged.
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
# End of class PatchXML


class RejectHandler:
    """
    Handle rejected files while merging.
    """

    REJECT_DIR = os.getcwd() + "/out/reject/"

    def __init__(self):
        if os.path.exists(RejectHandler.REJECT_DIR) == False:
            os.makedirs(RejectHandler.REJECT_DIR)
            pass

    def getRejectFilePath(self, originFilePath):
        return RejectHandler.REJECT_DIR + os.path.basename(originFilePath) + ".reject"

    def reject(self, originFilePath, item):
        # Open the the reject file with append mode
        self.rejectFileHandle = open(self.getRejectFilePath(originFilePath), "a")

        # Write the reject content
        action = PatchXML.getItemAttrib(item, 'action')
        nearby = PatchXML.getItemAttrib(item, 'nearby')
        anchor = PatchXML.getItemAttrib(item, 'anchor')
        position = PatchXML.getItemAttrib(item, 'position')
        matchType = PatchXML.getItemAttrib(item, 'match')
        content = item.text

        # Compose the reject text
        buf = ""
        if nearby != None:
            buf += "\n# [IN METHOD] : " + nearby

        buf += "\n# [ ANCHOR  ] : " + anchor

        if matchType != None and matchType == "REGEX":
            buf += "\n# [ATTENTION] : SHOULD USE REGEX TO MATCH THE ANCHOR IN " + os.path.basename(originFilePath)

        buf += "\n# [ ACTION  ] : " + action
        if position != None:
            buf += " THE FOLLOWING CODE " + position + " ANCHOR \n"

        buf += content
        buf += "\n# -----------------------------------------------------------\n"
        self.rejectFileHandle.write(buf)

        # Close
        self.rejectFileHandle.close()
        pass

# End of class RejectHandler

if __name__ == "__main__":
    ApplyPatch()

### prologue ###



