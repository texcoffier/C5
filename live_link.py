"""
Shared worker for all tabs and windows.
It is only a multiplexer

<id>   is the line number in the journal
<port> is the index of CLIENTS array «port.my_index»

Action       Network             JournalLink
open       → <port> <session>  → Ologin IP
JJournal   ← <port> JJournal   ←
<id> <msg> → <port> <id> <msg> → <msg>
<id> <msg> ← <port> <id> <msg> ← (If write OK: for each connected client on session)
<id> <msg> ← <port> <id> <msg> ← (Else: resend skipped content to the sender only)

close      → -<port>           →  C

M<log>     ← Display message on console
R          ← Connection lost: reinitialize tab

<msg> content :
   JJournal  : (not a line in journal) full journal content.
   Ologin IP : login and IP of the tab opened.
   C         : (only in journal) tab closed.
   Istr      : Insert 'str' text
For other messages see common.py Journal class

"""

window = {}

CLIENTS = []

class Server:
    """All communications between browser and server"""
    ticket = None
    socket = None
    wait_socket_open = False
    queue = []
    start_time = None
    def open(self):
        """Returns True if the socket is ready"""
        self.print('socket=' + self.socket + '/' + self.wait_socket_open + ' ' + self.ticket)
        if self.socket:
            self.print('Yet opened')
            return not self.wait_socket_open

        self.wait_socket_open = True

        socket = eval('new WebSocket("/live_link/session' + self.ticket + '")') # pylint: disable=eval-used
        self.print('socket=' + socket + '/' + self.wait_socket_open)
        SELF = self # pylint: disable=invalid-name
        def onopen():
            """The connection opened"""
            SELF.print("Server answered to open")
            SELF.socket = socket
            SELF.wait_socket_open = False
            for message in self.queue:
                SELF.socket.send(message)
        def onerror(event):
            """Tell clients that an error occured"""
            SELF.socket = None
            SELF.print('socket_error')
            SELF.print(event.target.readyState)
            SELF.reload()
        def onclose():
            """Tell clients that server connection is closed"""
            SELF.socket = None
            SELF.print('socket_close')
            SELF.reload()
        def onmessage(event):
            """Dispatch server message to the good client in the browser"""
            SELF.print("Receive from server:" + event.data)
            port = event.data.split(' ')[0]
            message = event.data.replace(RegExp('[0-9]* '), '')
            #SELF.print("port=" + event.data + ', message=' + message + ', client=' + CLIENTS[port])
            client = CLIENTS[port]
            if client:
                client.postMessage(message)

        socket.onopen = onopen
        socket.onerror = onerror
        socket.onclose = onclose
        socket.onmessage = onmessage
    def send(self, message):
        """Send or queue a message"""
        if self.open():
            self.print('REALLY SEND')
            self.socket.send(message)
        else:
            self.queue.append(message)
    def reload(self):
        """Tell all client tab to restart (connection lost)"""
        for client in CLIENTS:
            if client:
                CLIENTS[client.my_index] = None
                client.my_index = None
                client.postMessage('R')
                client.close()
    def print(self, message):
        """Tell all client to print a message in their console"""
        for client in CLIENTS:
            if client:
                client.postMessage('M' + self.start_time + ' ' + message)

SERVER = Server()

def my_onconnect(event):
    """A new browser tab connects to the live link shared worker"""
    def onmessage(event):
        """
        The tab just send a message to be send to the server
        To send message to server
        """
        SERVER.print(JSON.stringify(event.data))
        if event.data[0] == 'TICKET':
            if '=' not in event.data[2]:
                return # Not a session name
            port.session = event.data[2]
            SERVER.ticket = event.data[1]
            SERVER.send(port.my_index + ' ' + port.session + ' ' + event.data[3])
            return
        if event.data[0] == 'CLOSE':
            if port.my_index is not None: # Not closed by server
                SERVER.send(port.my_index + ' -')
                CLIENTS[port.my_index] = None
            return
        SERVER.send(port.my_index + ' ' + event.data)
    port = event.ports[0]
    port.onmessage = onmessage
    port.my_index = len(CLIENTS)
    CLIENTS.append(port)
    port.postMessage('M======== YOUR PORT IS : ' + port.my_index + " ========")

onconnect = my_onconnect
SERVER.start_time = millisecs()
