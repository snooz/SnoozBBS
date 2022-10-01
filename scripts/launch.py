import os
import re
import socket
import sys
import threading
import traceback
from _thread import start_new_thread
from binascii import hexlify
from getpass import getpass
from pprint import pprint

import chardet
import paramiko
from paramiko.py3compat import u

import func

# parsed_config = readConfig()
# pprint(parsed_config)

func.bbs_init()

paramiko.util.log_to_file("../logs/server.log")

server_config = func.get_config('server')

if str(server_config['key_password']) == '--prompt--':
    key_password = getpass('Key password: ')
elif len(server_config['key_password']) > 0:
    key_password = server_config['key_password']
else:
    key_password = False

if key_password:
    host_key = paramiko.RSAKey(filename=server_config['key_private'], password=key_password)
else:
    host_key = paramiko.RSAKey(filename=server_config['key_private'])

# host_key = paramiko.DSSKey(filename='test_dss.key')

print("Read key: " + u(hexlify(host_key.get_fingerprint())))


# exit(1)


class Server(paramiko.ServerInterface):
    ssh_key_config = func.get_config('server')
    # 'data' is the output of base64.b64encode(key)
    # (using the "user_rsa_key" files)
    good_pub_key = paramiko.RSAKey(filename=ssh_key_config['key_private'])

    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == "snooz") and (password == "baka"):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if (username == "snooz") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(
            self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(
            self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def enable_auth_gssapi(self):
        return True

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(
            self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True


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


# clients = [] #list of clients connected

# Function for handling connections.
def client_thread(this_connection):
    global is_online
    global server_config
    # clients.append(this_connection)
    # Sending message to connected client
    try:
        lines = func.do_display(
                func.parsed_config['config']['welcomeFileOutput']) + os.linesep
        for line in lines.split("\n"):
            this_connection.send(line + os.linesep)
        this_connection.send(os.linesep + "Command :> ")
    except:
        print("Couldnt send the welcome file")

    is_online = True
    doDisconnect = False

    # infinite loop so that function do not terminate and thread do not end.
    while True:
        # Receiving from client
        f = this_connection.makefile("rU")
        command_string = f.readline().strip("\r\n")
        this_connection.send(command_string.upper() + os.linesep)
        print(command_string + os.linesep)

        # command_string = data.strip('\\%').decode().strip()
        # encoding = chardet.detect(data)["encoding"]
        # command_string = str(re.sub('[^A-Za-z0-9\\-\\+\\. ]+', '', data)).strip()
        # command_string = command_string.encode(encoding).decode('UTF-8')
        reply = ''
        if command_string:
            response = func.bbs_command(command_string)
            if response['display']:
                reply += response['display']
            if response['action']:
                if response['action'] == 'close':
                    doDisconnect = True
        else:
            break

        for line in reply.split("\n"):
            this_connection.send(line + os.linesep)

        this_connection.send(os.linesep + "Command :> ")

        if doDisconnect:
            break

    print('Disconnected.')
    # clients.remove(this_connection)
    this_connection.close()


DoGSSAPIKeyExchange = True

# now connect
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("Opening connection on " + str(HOST) + ':' + str(PORT))
    sock.bind((HOST, PORT))
except Exception as e:
    print("*** Bind failed: " + str(e))
    traceback.print_exc()
    sys.exit(1)

try:
    sock.listen(100)
    print("Listening for connection ...")
    client, addr = sock.accept()
except Exception as e:
    print("*** Listen/accept failed: " + str(e))
    traceback.print_exc()
    sys.exit(1)

print("Got a connection!")

try:
    t = paramiko.Transport(client, gss_kex=DoGSSAPIKeyExchange)
    t.set_gss_host(socket.getfqdn(""))
    try:
        t.load_server_moduli()
    except:
        print("(Failed to load moduli -- gex will be unsupported.)")
        raise
    t.add_server_key(host_key)
    server = Server()
    try:
        t.start_server(server=server)
    except paramiko.SSHException:
        print("*** SSH negotiation failed.")
        sys.exit(1)

    # wait for auth
    conn = t.accept(20)
    if conn is None:
        print("*** No channel.")
        sys.exit(1)
    print("Authenticated!")

    server.event.wait(10)
    if not server.event.is_set():
        print("*** Client never asked for a shell.")
        sys.exit(1)

    # while is_online:
    # wait to accept a connection - blocking call
    # start_new_thread(client_thread, (conn,))
    client_thread(conn)
    # conn.send("\r\n\r\nWelcome to my dorky little BBS!\r\n\r\n")
    # conn.send(
    #     "We are on fire all the time!  Hooray!  Candy corn for everyone!\r\n"
    # )
    # conn.send("Happy birthday to Robot Dave!\r\n\r\n")
    # conn.send("Username: ")
    # f = conn.makefile("rU")
    # username = f.readline().strip("\r\n")
    # conn.send("\r\nI don't like you, " + username + ".\r\n")
    # conn.close()

except Exception as e:
    print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass

    sys.exit(1)

sock.close()
quit()
