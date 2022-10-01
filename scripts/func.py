import json
import os
import re
from datetime import datetime
from os import path
from cffi.backend_ctypes import unicode

active_board = 1
parsed_config = {}


def byte_convert(in_data):
    if isinstance(in_data, dict):
        return {byte_convert(key): byte_convert(value)
                for key, value in in_data.items()}
    elif isinstance(in_data, list):
        return [byte_convert(element) for element in in_data]
    elif isinstance(in_data, unicode):
        return in_data.encode('utf-8')
    else:
        return in_data


def pcb_color_dump():
    return_var = ''
    for i in range(0, 16):
        for j in range(0, 16):
            return_var += '@X' + str(hex(i)[2:]).upper() + str(hex(j)[2:]).upper() + '#X' + str(
                hex(i)[2:]).upper() + str(hex(j)[2:]).upper() + ' '
        return_var += '@X07\n'
    return return_var + '@X07\n\n'


def pcb2ansi(m):
    color1 = int(m.group(1), 16)
    color2 = int(m.group(2), 16)
    if color1 > 7:
        color1 = color1 - 8
        color1 = color1 + 100
    else:
        color1 = color1 + 40
    if color2 > 7:
        color2 = color2 - 8
        color2 = color2 + 90
    else:
        color2 = color2 + 30
    if str(m.group(1)) + str(m.group(2)) == '07':
        return '\x1b[0m'
    else:
        return '\x1b[0;' + str(color1) + ';' + str(color2) + 'm'


def pcb_codes(m):
    code = m.group(1)
    if code == 'SYSTIME':
        return datetime.now().strftime("%H:%M")
    elif code == 'SYSDATE':
        return datetime.now().strftime("%Y-%m-%d")


def parse_display(inp):
    # PCBoard color codes @X0F
    inp = re.sub('@X([0-9A-Fa-f])([0-9A-Fa-f])', pcb2ansi, inp)

    # Wildcat color codes @0F@
    inp = re.sub('@([0-9A-Fa-f])([0-9A-Fa-f])@', pcb2ansi, inp)

    inp = inp.replace("\\n", '')
    out = ''
    for line in inp.split("\n"):
        out += line + "\n"

    return out


def do_display(inp):
    # PCBoard display variables
    inp = re.sub('@([A-Z0-9:]+)@', pcb_codes, inp)

    return inp


def config_parser(config_data):
    global board_list
    global parsed_config
    board_list = ''
    parsed_data = {}
    for (config_slug, config_content) in config_data.items():
        if config_slug == 'boards':
            parsed_data['boards'] = {}
            for (board_slug, board_val) in config_content.items():
                parsed_data['boards'][int(board_slug)] = parse_boards(board_val,
                                                                      config_data['config']['paths']['menus'])
                board_list += str(board_slug).rjust(5) + ': ' + str(board_val['name']) + os.linesep
        elif config_slug == 'config':
            parsed_data['config'] = {}
            for (config_slug_sub, config_val_sub) in config_content.items():
                if str(config_slug_sub)[-4:] == 'File':
                    if path.exists(menu_path + str(config_val_sub)):
                        temp_var = open(menu_path + str(config_val_sub), encoding="utf-8").read()
                        temp_var = parse_display(temp_var)
                        parsed_data['config'][str(config_slug_sub) + 'Output'] = temp_var
                        temp_var = None
                    else:
                        print("Config path doesn't exist: " + menu_path + str(config_val_sub) + os.linesep)
                elif str(config_slug_sub) == 'paths':
                    parsed_data['config'][str(config_slug_sub)] = {}
                    for (pathSlug, pathVal) in config_val_sub.items():
                        parsed_data['config'][str(config_slug_sub)][str(pathSlug)] = str(pathVal)
                else:
                    parsed_data['config'][str(config_slug_sub)] = int(config_val_sub) if str(
                        config_val_sub).isdigit() else str(config_val_sub)
        else:
            parsed_data[str(config_slug)] = {}
            for (config_slug_sub, config_val_sub) in config_content.items():
                parsed_data[str(config_slug)][str(config_slug_sub)] = int(config_val_sub) if str(
                    config_val_sub).isdigit() else str(config_val_sub)
    parsed_config = parsed_data


def parse_boards(board_data, menu_path):
    boards = {}
    for (configKey, configVal) in board_data.items():
        if str(configKey)[-4:] == 'File':
            temp_var = open(menu_path + str(configVal), 'r').read()
            temp_var = parse_display(temp_var)
            boards['menuFile'] = temp_var
        elif str(configKey) == 'commands':
            boards['commands'] = {}
            for (commandKey, commandVal) in configVal.items():
                boards['commands'][str(commandKey)] = str(commandVal)
        else:
            boards[str(configKey)] = str(configVal)
    return boards


def read_config():
    global menu_path
    global script_path
    file_config = {}
    with open('../config/bbs.json', encoding="utf-8") as json_data_file:
        file_config = json.load(json_data_file)

    print(file_config)
    menu_path = file_config['config']['paths']['menus']
    script_path = file_config['config']['paths']['scripts']

    config_parser(file_config)


def get_active_board():
    global active_board
    return active_board


def set_active_board(board=1):
    global active_board
    active_board = board
    return True


# BBS Functions
def bbs_command(str_input):
    return_command = {'display': '', 'action': ''}
    m = re.search('([a-zA-Z]+)\\s?([0-9]+)?', str_input)
    if m is None:
        return_command['display'] = 'Invalid command.'
    elif m is not None:
        first_command = str(m.group(1)).upper()
        if first_command == 'CHANGE':
            if str(m.group(2)).isdigit() and int(m.group(2)) >= 0:
                return_command['display'] = bbs_change_menu(int(m.group(2)))
            else:
                return_command['display'] = 'You must supply a board number, use the LIST command to show available ' \
                                            'boards.'
        elif first_command == 'LIST':
            return_command['display'] = bbs_list_boards()
        elif first_command == 'QUIT' or first_command == 'EXIT' or first_command == 'BYE':
            bye_config = get_config('config')
            return_command['display'] = do_display(bye_config['byeFileOutput'])
            return_command['action'] = 'close'
        elif first_command == 'MENU':
            all_boards = get_config('boards')
            return_command['display'] = do_display(all_boards[get_active_board()]['menuFile'])
        elif first_command == 'RELOAD':
            bbs_reload()
            return_command['display'] = "Reloaded the config files"
        else:
            return_command['display'] = 'Invalid command.'
    else:
        return_command['display'] = 'Invalid command.'
    return return_command

def bbs_change_menu(current_board_id):
    set_active_board(current_board_id)
    return 'Board changed to ' + parsed_config['boards'][current_board_id]['name'] + '\n'


def bbs_list_boards():
    return str(board_list)


def bbs_init():
    read_config()
    base_config = get_config('config')
    set_active_board(int(base_config['initialBoard']))


def bbs_reload():
    print('Reload was called.')
    read_config()


def get_config(key, default=False):
    global parsed_config
    if parsed_config[key]:
        return parsed_config[key]
    elif default:
        return default
    else:
        return False
