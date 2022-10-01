import os
import re
import socket
import sys
from _thread import *

import func

# parsed_config = readConfig()
# pprint(parsed_config)

func.bbs_init()

HOST = func.parsed_config['config']['hostname']
PORT = func.parsed_config['config']['port']
is_online = True

if len(sys.argv) > 2:
    if str(sys.argv[1]) == '-t':
        if str(sys.argv[2]).upper() == 'PCB':
            print(re.sub('#', '@', re.sub('@X([0-9A-Fa-f])([0-9A-Fa-f])', func.pcb2ansi, func.pcb_color_dump())))
            quit()

menu_path = func.parsed_config['config']['paths']['menus']
script_path = func.parsed_config['config']['paths']['scripts']

splashScreen = open(menu_path + str('palma.pcb'), 'r').read()
splashScreen = func.parse_display(splashScreen + '@X07')
print(splashScreen + "\n\n")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print('Socket initialized')

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print('Initialization failed. Error code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()

print('Socket established')

s.listen(10)
print('Socket now listening')


# clients = [] #list of clients connected

# Function for handling connections.
def client_thread(this_connection):
    global is_online

    # clients.append(this_connection)
    # Sending message to connected client
    this_connection.send(func.do_display(func.parsed_config['config']['welcomeFileOutput']) + "\n\nCommand :> ")
    is_online = True
    # infinite loop so that function do not terminate and thread do not end.
    while True:

        # Receiving from client
        data = this_connection.recv(1024)
        # command_string = data.strip('\\%').decode().strip()
        command_string = str(re.sub('[^A-Za-z0-9\\-\\+\\. ]+', '', data)).decode()
        reply = ''
        if command_string[:3].upper() == 'BYE':
            this_connection.send(func.do_display(func.parsed_config['config']['byeFileOutput']) + os.linesep)
            break
        elif command_string[:4].upper() == 'MENU':
            reply = func.do_display(func.parsed_config['boards'][func.activeBoardId]['menuFile']) + os.linesep
        elif command_string[:4].upper() == 'KILL':
            this_connection.send("I ded!" + os.linesep)
            print('Next connection will kill me.' + os.linesep)
            is_online = False
            break
        elif command_string[:6].upper() == 'RELOAD':
            func.bbs_reload()
            reply = "Reloaded the config files" + os.linesep
        else:
            reply = func.bbs_command(command_string)
        if not data:
            break

        print(command_string)
        reply += os.linesep + "Command :> "
        this_connection.send(reply)

    print('Disconnected.')
    # clients.remove(this_connection)
    this_connection.close()


while is_online:
    # wait to accept a connection - blocking call
    conn, addr = s.accept()
    print('Connected with ' + addr[0] + ':' + str(addr[1]))

    # start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the
    # function.
    start_new_thread(client_thread, (conn,))

s.close()
quit()
