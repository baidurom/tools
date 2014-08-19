#!/usr/bin/python

'''
Coron
'''

__author__ = "duanqz@gmail.com"


import os, sys
from workflow import CoronStateMachine
from help import HelpFactory, HelpPresenter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from formatters.log import Paint


def coronUsage():
    helpEntry = HelpFactory.createHelp()

    print Paint.bold("Coron - an open source project for Android ROM porting.")
    print "Copyright 2014 Baidu Cloud OS <rom.baidu.com>                    "
    print "Apache License 2.0 (http://www.apache.org/licenses/LICENSE-2.0)  "
    print "                                                                 "
    print "COMMANDs are:                                                    "

    # Coron help
    print Paint.bold("* coron help [NAME]")
    print " ", helpEntry.get("help").detail.strip()
    print "                                                                 "


    # Coron action
    print Paint.bold("* coron ACTION")
    print "  Run the action separately."
    print "                                                                 "
    print Paint.bold("ACTION").rjust(20), "\t", Paint.bold("Description")

    ACTIONS = ("config", "newproject", "patchall", "autofix", "fullota", "upgrade", "clean", "cleanall")
    for action in ACTIONS:
        item = helpEntry.get(action)

        print Paint.bold(action).rjust(20), "\t", item.detail.strip()
        print "                                                             "


    # Coron fire
    print Paint.bold("* coron fire")
    print " ", helpEntry.get("fire").detail.strip()
    print "                                                                 "



if __name__ == "__main__":
    if len(sys.argv) == 1:
        coronUsage()
        sys.exit(0)

    arg = sys.argv[1]
    if   arg == "fire":
        CoronStateMachine().start()
    elif arg == "help":
        HelpPresenter.parseargs(sys.argv[1:])
    else:
        CoronStateMachine().doAction(arg)

