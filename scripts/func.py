import socket, sys, re, json, os
from datetime import datetime
from pprint import pprint

def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

def pcbColorDump():
    returnVar = ''
    for i in range(0,16):
        for j in range(0,16):
            returnVar += '@X'+str(hex(i)[2:]).upper()+str(hex(j)[2:]).upper()+'#X'+str(hex(i)[2:]).upper()+str(hex(j)[2:]).upper()+' '
        returnVar += '@X07\n'
    return returnVar + '@X07\n\n'

def pcbToAnsi(m):
    color1 = int(m.group(1),16)
    color2 = int(m.group(2),16)
    if (color1 > 7):
        color1 = color1 - 8
        color1 = color1 + 100
    else:
        color1 = color1 + 40
    if (color2 > 7):
        color2 = color2 - 8
        color2 = color2 + 90
    else:
        color2 = color2 + 30
    if str(m.group(1))+str(m.group(2)) == '07':
        return '\x1b[0m'
    else:
        return '\x1b[0;'+str(color1)+';'+str(color2)+'m'

def pcbCodes(m):
    code = m.group(1)
    if (code == 'SYSTIME'):
        return datetime.now().strftime("%H:%M")
    elif (code == 'SYSDATE'):
        return datetime.now().strftime("%Y-%m-%d")

def parseDisplay(inp):
    # PCBoard color codes @X0F
    inp = re.sub('@X([0-9A-Fa-f])([0-9A-Fa-f])',pcbToAnsi,inp)

    # Wildcat color codes @0F@
    inp = re.sub('@([0-9A-Fa-f])([0-9A-Fa-f])@',pcbToAnsi,inp)

    return inp

def doDisplay(inp):
    # PCBoard display variables
    inp = re.sub('@([A-Z0-9:]+)@',pcbCodes,inp)

    return inp

def parseConfig(configData):
    global boardList
    boardList = ''
    parsedData = {}
    for (configSlug,configContent) in configData.items():
        if configSlug == 'boards':
            parsedData['boards'] = {}
            for (boardSlug,boardVal) in configContent.items():
                parsedData['boards'][int(boardSlug)] = parseBoards(boardVal,configData['config']['paths']['menus'])
                boardList += str(boardSlug).rjust(5)+': '+str(boardVal['name'])+"\n"
        elif configSlug == 'config':
            parsedData['config'] = {}
            for (configSubSlug,configSubVal) in configContent.items():
                if str(configSubSlug)[-4:] == 'File':
                    tempVar = open(PATHMENU + str(configSubVal),'r').read()
                    tempVar = parseDisplay(tempVar)
                    parsedData['config'][str(configSubSlug)+'Output'] = tempVar
                    tempVar = None
                elif str(configSubSlug) == 'paths':
                    parsedData['config'][str(configSubSlug)] = {}
                    for (pathSlug,pathVal) in configSubVal.items():
                        parsedData['config'][str(configSubSlug)][str(pathSlug)] = str(pathVal)
                else:
                    parsedData['config'][str(configSubSlug)] = int(configSubVal) if str(configSubVal).isdigit() else str(configSubVal)
    return parsedData

def parseBoards(boardData,PATHMENU):
    boards = {}
    for (configKey,configVal) in boardData.items():
        if str(configKey)[-4:] == 'File':
            tempVar = open(PATHMENU + str(configVal),'r').read()
            tempVar = parseDisplay(tempVar)
            boards['menuFile'] = tempVar
        elif str(configKey) == 'commands':
            boards['commands'] = {}
            for (commandKey,commandVal) in configVal.items():
                boards['commands'][str(commandKey)] = str(commandVal)
        else:
            boards[str(configKey)] = str(configVal)
    return boards

def readConfig():
    global PATHMENU
    global PATHSCRIPT
    fileConfig = {}
    with open('../config/bbs.json') as json_data_file:
        fileConfig = byteify(json.load(json_data_file))

    #print(fileConfig)
    PATHMENU   = fileConfig['config']['paths']['menus']
    PATHSCRIPT = fileConfig['config']['paths']['scripts']

    parsedConfig = parseConfig(fileConfig)
    return parsedConfig

# BBS Functions
def bbsCommand(strInput):
    m = re.search('([a-zA-Z]+)\s?([0-9]+)?',strInput)
    if m == None:
        return 'Invalid command.'
    elif m != None:
        if str(m.group(1)).upper() == 'CHANGE':
            if str(m.group(2)).isdigit() and int(m.group(2)) >= 0:
                return bbs_changeMenu(int(m.group(2)))
            else:
                return 'You must supply a board number, use the LIST command to show available boards.'
        elif str(m.group(1)).upper() == 'LIST':
            return bbs_listBoards()
        else:
            return 'Invalid command.'
    else:
        return 'Invalid command.'

def bbs_changeMenu(boardId):
    global activeBoardId
    activeBoardId = boardId
    return 'Board changed to ' + parsedConfig['boards'][boardId]['name'] + '\n'

def bbs_listBoards():
    return str(boardList)

def bbsInit():
    global parsedConfig
    global activeBoardId
    parsedConfig = readConfig()
    activeBoardId = int(parsedConfig['config']['initialBoard'])

def bbsReload():
    global parsedConfig
    print 'Reload was called.'
    parsedConfig = readConfig()
