#!/usr/bin/python

'''
Type `help name' to find out more about the `name'.

   e.g.  help "config"
   e.g.  help "newproject"
   e.g.  help "patchall"

'''


import os, sys
import types
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from formatters.log import Paint

class Item:
    """ Help Item Model
    """

    name = None
    code = None
    detail = None
    solution = None

    def __init__(self, code, name):
        self.code = code
        self.name = name

# End of class Item


class Help:
    """ Help Model
    """

    XML = os.path.join(os.path.dirname(os.path.realpath(__file__)), "help/help.xml")

    CODE_TO_NAME = {}
    NAME_TO_CODE = {}
    ITEM_TAGS = {}

    def __init__(self):
        XMLDom = ET.parse(Help.XML)

        for tag in XMLDom.findall('item'):
            name = tag.get('name')
            code = int(tag.get('code'))

            self.CODE_TO_NAME[code] = name
            self.NAME_TO_CODE[name] = code
            self.ITEM_TAGS[code] = tag

    def getName(self, code):
        return self.CODE_TO_NAME.get(code)

    def getCode(self, name):
        return int(self.NAME_TO_CODE.get(name))

    def get(self, key):
        """ Get the help item by either code or name.
            See the Help Item Model @Item
        """

        if key == None:
            return None
        elif type(key) is types.IntType:
            code = key
            name = self.CODE_TO_NAME.get(code)
        elif key.isdigit():
            code = int(key)
            name = self.CODE_TO_NAME.get(code)
        else:
            name = key
            code = self.NAME_TO_CODE.get(name)

        tag = self.ITEM_TAGS.get(code)
        if tag == None:
            return None

        item = Item(code, name)
        for child in tag.getchildren():
            if   child.tag == "solution":
                item.solution = child.text
            elif child.tag == "detail":
                item.detail = child.text

        return item


    @staticmethod
    def show(item, attrib=None):
        """ Show the help item.
        """

        if item == None:
            return

        if attrib == "solution":
            if item.solution != None: print item.solution.replace("\t", "")
        elif attrib == "detail":
            if item.detail != None: print item.detail.replace("\t", "")
        else:
            print Paint.bold("%s\t%s\n" % (item.code, item.name))
            Help.showDetail(item)
            print " "


    @staticmethod
    def showDetail(item):
        if item == None:
            return

        if item.detail != None:
            if item.code == 0:
                print Paint.green(item.detail.replace("\t", ""))
            else:
                print Paint.red(item.detail.replace("\t", ""))

        if item.solution != None:
            print Paint.green(item.solution.replace("\t", ""))


# End of class Help


class HelpOverride(Help):
    """ Derived class of Help.
        Override items if defined in Help
    """

    def __init__(self, xml):
        Help.__init__(self)

        XMLDom = ET.parse(xml)

        for tag in XMLDom.findall('item'):
            name = tag.get('name')
            code = int(tag.get('code'))

            self.CODE_TO_NAME[code] = name
            self.NAME_TO_CODE[name] = code
            self.ITEM_TAGS[code] = tag

# End of class HelpOverride



class HelpFactory:
    """ Factory to create Help Model
    """

    @staticmethod
    def createHelp(category=None):
        helpXML = HelpFactory.getHelpXML(category)
        if helpXML != None:
            return HelpOverride(helpXML)
        else:
            return Help()

    @staticmethod
    def getHelpXML(category):
        helpXML = os.path.join(os.path.dirname(Help.XML), "help_%s.xml" % category)
        if os.path.exists(helpXML):
            return helpXML
        else:
            return None

# End of class HelpFactory



class HelpPresenter:


    @staticmethod
    def get(key, category):
        helpEntry = HelpFactory.createHelp(category)
        item = helpEntry.get(key)
        if item == None and category == None:
            helpXMLs = os.listdir(os.path.dirname(Help.XML))
            for helpXML in helpXMLs:
                if helpXML.startswith("help_") and helpXML.endswith(".xml"):
                    category = helpXML[5:-4]
                    helpEntry = HelpFactory.createHelp(category)
                    item = helpEntry.get(key)

        return item  


    @staticmethod
    def showall():
        helpEntry = HelpFactory.createHelp()
        for code in sorted(helpEntry.CODE_TO_NAME.keys()):
            if code == 255: continue;
            item = helpEntry.get(code)
            if item.detail != None:
                print "%s(%d)\n%s" % (Paint.bold(item.name), item.code, item.detail.replace("\t", "").strip())
                print " "

    @staticmethod
    def show(key, category=None):
        item = HelpPresenter.get(key, category)
        Help.show(item)


    @staticmethod
    def showdetail(key, category=None):
        item = HelpPresenter.get(key, category)
        Help.showDetail(item)

    @staticmethod
    def parseargs(argv):
        key = None
        category = None
        size = len(argv)
        if size == 1:  HelpPresenter.showall()
        if size >  1:  key = argv[1]
        if size >  2:  category = argv[2]

        HelpPresenter.show(key, category)



if __name__ == "__main__":
    HelpPresenter.parseargs(sys.argv)


