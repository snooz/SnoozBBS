import socket, sys, re, json, os

from datetime import datetime
from thread import *
from pprint import pprint
import func

#parsedConfig = readConfig()
#pprint(parsedConfig)

func.bbsInit()

HOST = func.parsedConfig['config']['hostname']
PORT = func.parsedConfig['config']['port']
ISONLINE = True

if len(sys.argv) > 2:
    if str(sys.argv[1]) == '-t':
        if (str(sys.argv[2]).upper() == 'PCB'):
            print re.sub('#','@',re.sub('@X([0-9A-Fa-f])([0-9A-Fa-f])',func.pcbToAnsi,func.pcbColorDump()))
            quit()

PATHMENU   = func.parsedConfig['config']['paths']['menus']
PATHSCRIPT = func.parsedConfig['config']['paths']['scripts']

splashScreen = open(PATHMENU + str('palma.pcb'),'r').read()
splashScreen = func.parseDisplay(splashScreen+'@X07')
print splashScreen + "\n\n"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
print 'Socket initialized'

try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print 'Initialization failed. Error code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

print 'Socket established'

s.listen(10)
print 'Socket now listening'

#clients = [] #list of clients connected

#Function for handling connections.
def clientthread(conn):
    global ISONLINE

    #clients.append(conn)
    #Sending message to connected client
    conn.send(func.doDisplay(func.parsedConfig['config']['welcomeFileOutput']) + "\n\nCommand :> ")
    isOnline = True
    #infinite loop so that function do not terminate and thread do not end.
    while True:
         
        #Receiving from client
        data = conn.recv(1024)
        #commandString = data.strip('\\%').decode().strip()
        commandString = str(re.sub('[^A-Za-z0-9\-\+\. ]+','',data)).decode()
        reply = ''
        if commandString[:3].upper() == 'BYE':
            conn.send(func.doDisplay(func.parsedConfig['config']['byeFileOutput']) + "\n")
            break
        elif commandString[:4].upper() == 'MENU':
            reply = func.doDisplay(func.parsedConfig['boards'][func.activeBoardId]['menuFile']) + "\n"
        elif commandString[:4].upper() == 'KILL':
            conn.send("I ded!\n")
            print 'Next connection will kill me.\n'
            ISONLINE = False
            break
        elif commandString[:6].upper() == 'RELOAD':
            func.bbsReload()
            reply = "Reloaded the config files\n"
        else:
            reply = func.bbsCommand(commandString)
        if not data: 
            break
     
        print(commandString)
        reply += "\nCommand :> "
        conn.send(reply)
     
    print 'Disconnected.'
    #clients.remove(conn)
    conn.close()
 
while ISONLINE == True:
    #wait to accept a connection - blocking call
    conn, addr = s.accept()
    print 'Connected with ' + addr[0] + ':' + str(addr[1])
     
    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    start_new_thread(clientthread ,(conn,))

s.close()
quit()