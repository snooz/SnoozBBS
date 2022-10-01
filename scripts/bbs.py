from func import *


def bbs_command(strInput):
    m = re.search('([a-zA-Z]+)\\s?([0-9]+)?', strInput)
    if m is not None:
        if str(m.group(1)).upper() == 'CHANGE':
            if int(m.group(2)) >= 0:
                return bbs_change_menu(m.group(2))
    else:
        return 'Invalid command.'


def bbs_change_menu(boardId):
    return 'menu changed to ' + parsed_config['boards'][boardId]['name']
