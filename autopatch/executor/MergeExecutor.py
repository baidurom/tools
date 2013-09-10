#!/usr/bin/python
# Filename: MergeExecutor.py

### File Information ###

"""
Merge the changed defined in XML into destination file.
"""

__author__ = 'duanqizhi01@baidu.com (duanqz)'

### File Information ###



### import block ###

import sys
import re

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

    def getItemAttrib(self, item, key):
        try:
            return item.attrib[key]
        except KeyError:
            return None

    def getNearbyPos(self, item):
        """
        Get the nearby position. If not found the nearby, 0 will be returned.
        """

        nearbyPos = 0
        nearby = self.getItemAttrib(item, 'nearby')
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
        matchType = self.getItemAttrib(item, 'match')

        if anchor == "EOF":
            anchorStart = len(self.dstFileBuf)
            anchorEnd = anchorStart
            content = item.text

        elif matchType == "REGEX":
            anchorRegex = re.compile(anchor)
            match = anchorRegex.search(self.dstFileBuf[nearbyPos:])
            if match == None:
                return None
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
            return None

        return { "anchorStart" : anchorStart,
                 "anchorEnd"   : anchorEnd,
                 "content"     : content  }

    def applyMerge(self, item, anchorStart, anchorEnd, content):
        """
        Merge the content to anchor position. 
        """

        action = item.attrib['action']
        position = self.getItemAttrib(item, 'position')

        if action == "ADD":
            if position == "OVER":
                self.dstFileBuf = self.dstFileBuf[:anchorStart] + content + "\n" + self.dstFileBuf[anchorStart:]
            elif position == "BELOW":
                self.dstFileBuf = self.dstFileBuf[:anchorEnd] + "\n" + content + self.dstFileBuf[anchorEnd:]

        elif action == "REPLACE":
            self.dstFileBuf = self.dstFileBuf[:anchorStart]  + content.strip() + self.dstFileBuf[anchorEnd:]

        elif action == "DEL":
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

# End of class MergerXML


if __name__ == "__main__":
    Main()

### prologue ###



