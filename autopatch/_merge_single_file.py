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

class Main():
    """
    Entry of the script
    """

    def __init__(self):
        if len(sys.argv) < 3:
            print "Error arguments. " + " ".join(sys.argv)
            sys.exit(1)

        dstFilePath = sys.argv[1]
        srcFilePath = sys.argv[2]

        MergeExecutor(dstFilePath, srcFilePath).run()
        pass

# End of class Main


class MergeExecutor:
    """
    Execute the merge action
    """

    def __init__(self, dstFilePath, srcFilePath):

        self.mDstFilePath = dstFilePath
        self.mSrcFilePath = srcFilePath

        # Hold all the exceptions
        self.exceptions = []
        # Handle reject files while merging
        self.rejectHandler = RejectHandler()

    def run(self):
        # Open the destination file
        self.openDstFile()

        # Open and parse the source MergerXML file
        mergerXML = MergerXML().parse(self.mSrcFilePath)
        for item in mergerXML.getItems():
            self.mergeItem(item)

        # Close the destination file
        self.closeDstFiles()

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
        nearby = MergerXML.getItemAttrib(item, 'nearby')
        if nearby != None:
            nearbyPos = self.dstFileBuf.find(nearby)

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
        matchType = MergerXML.getItemAttrib(item, 'match')

        if anchor == "EOF":
            anchorStart = len(self.dstFileBuf)
            anchorEnd = anchorStart
            content = item.text

        elif matchType == "REGEX":
            anchorRegex = re.compile(anchor)
            match = anchorRegex.search(self.dstFileBuf[nearbyPos:])
            if match == None:
                anchorStart = -1
            else:
                anchorStart = nearbyPos + match.start()
                anchorEnd = nearbyPos + match.end()
                # Format the content text with match result
                content = item.text % match.groups()

        else:
            anchorStart = self.dstFileBuf.find(anchor, nearbyPos)
            anchorEnd = anchorStart + len(anchor)
            content = item.text

        if anchorStart < 0:
            self.exceptions.append("Can not find anchor " + anchor + " in " + self.mDstFilePath)
            self.rejectHandler.reject(self.mDstFilePath, item)
            return None

        return { "anchorStart" : anchorStart,
                 "anchorEnd"   : anchorEnd,
                 "content"     : content  }

    def applyMerge(self, item, anchorStart, anchorEnd, content):
        """
        Merge the content to anchor position. 
        """

        action = item.attrib['action']
        position = MergerXML.getItemAttrib(item, 'position')

        if action == "ADD":
            if position == "OVER":
                self.dstFileBuf = self.dstFileBuf[:anchorStart] + content + "\n" + self.dstFileBuf[anchorStart:]
            elif position == "BELOW":
                self.dstFileBuf = self.dstFileBuf[:anchorEnd] + "\n" + content + self.dstFileBuf[anchorEnd:]

        elif action == "REPLACE":
            self.dstFileBuf = self.dstFileBuf[:anchorStart]  + content.strip() + self.dstFileBuf[anchorEnd:]

        elif action == "DEL":
            # TODO add Delete action
            pass

    def openDstFile(self):
        """
        Open the destination file in read and write mode
        Read the file content and create a buffer
        """

        self.dstFileHandle = open(self.mDstFilePath, 'r+')
        self.dstFileBuf = self.dstFileHandle.read()

    def closeDstFiles(self):
        """
        Update the file content , and flush the destination file to disk
        """

        self.dstFileHandle.truncate(0)
        self.dstFileHandle.seek(0)
        self.dstFileHandle.write(self.dstFileBuf)
        self.dstFileHandle.flush()
        self.dstFileHandle.close()

    def raiseExceptions(self):
        """
        Raise the exceptions if exists. 
        """

        if len(self.exceptions) > 0:
            raise KeyError(self.exceptions)

# End of class MergeExecutor


class MergerXML:
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
# End of class MergerXML


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
        action = MergerXML.getItemAttrib(item, 'action')
        nearby = MergerXML.getItemAttrib(item, 'nearby')
        anchor = MergerXML.getItemAttrib(item, 'anchor')
        position = MergerXML.getItemAttrib(item, 'position')
        matchType = MergerXML.getItemAttrib(item, 'match')
        content = item.text

        # Compose the reject text
        if nearby != None:
            buf = "\n# [IN METHOD] : " + nearby

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
    Main()

### prologue ###



