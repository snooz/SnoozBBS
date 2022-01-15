import socket, sys, re, os
from datetime import datetime
from listener import *
from func import *

def bbsCommand(strInput):
  m = re.search('([a-zA-Z]+)\s?([0-9]+)?',strInput)
  if m != None:
    if str(m.group(1)).upper() == 'CHANGE':
      if (int(m.group(2)) >= 0):
        return bbs_changeMenu(m.group(2))
  else:
    return 'Invalid command.'

def bbs_changeMenu(boardId):
  return 'menu changed to ' + parsedConfig['boards'][boardId]['name']