import websocket
import time
import ssl
from threading import Thread

BYTE = {
    'LF': '\x0A',
    'NULL': '\x00'
}

VERSIONS = '1.0,1.1'

class Stomp:
    def __init__(self, host, sockjs=False, wss=True, username=None, password=None, insecure=False, debug=False):
        """
        Initialize STOMP communication. This is the high level API that is exposed to clients.

        Args:
            host: Hostname
            sockjs: True if the STOMP server is sockjs
            wss: True if communication is over SSL
            username: Username for authentication
            password: Password for authentication
            insecure: True to accept self-signed certificates (disable SSL verification)
            debug: True to enable WebSocket debug traces
        """
        # Enable WebSocket debug traces if requested
        if debug:
            websocket.enableTrace(True)
            
        ws_host = host if sockjs is False else host + "/websocket"
        protocol = "ws://" if wss is False else "wss://"

        self.url = protocol + ws_host
        self.username = username
        self.password = password
        self.insecure = insecure

        self.dispatcher = Dispatcher(self)

        # maintain callback registry for subscriptions -> topic (str) vs callback (func)
        self.callback_registry = {}

    def connect(self):
        """
        Connect to the remote STOMP server
        """
        # set flag to false
        self.connected = False

        # attempt to connect
        self.dispatcher.connect()

        # wait until connected
        while self.connected is False:
            time.sleep(.50)

        return self.connected

    def subscribe(self, destination, callback):
        """
        Subscribe to a destination and supply a callback that should be executed when a message is received on that destination
        """
        # create entry in registry against destination
        self.callback_registry[destination] = callback
        self.dispatcher.subscribe(destination)

    def send(self, destination, message):
        """
        Send a message to a destination
        """
        self.dispatcher.send(destination, message)
        
    def disconnect(self):
        """
        Disconnect from the STOMP server
        """
        if hasattr(self, 'connected') and self.connected:
            self.dispatcher.disconnect()
            self.connected = False


class Dispatcher:
    def __init__(self, stomp):
        """
        The Dispatcher handles all network I/O and frame marshalling/unmarshalling
        """
        self.stomp = stomp

        self.ws = websocket.WebSocketApp(
            self.stomp.url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close
        )

        # Configure SSL context for insecure connections
        sslopt = None
        if self.stomp.url.startswith('wss://') and self.stomp.insecure:
            # Create SSL context that accepts self-signed certificates
            sslopt = {
                "cert_reqs": ssl.CERT_NONE,
                "check_hostname": False,
                "ssl_version": ssl.PROTOCOL_TLS
            }

        # run event loop on separate thread
        Thread(target=self.ws.run_forever, kwargs={"ping_interval": 5, "ping_timeout": 4, "sslopt": sslopt}).start()

        self.opened = False

        # wait until connected
        while self.opened is False:
            time.sleep(.50)

    def _on_message(self, ws, message):
        """
        Executed when messages is received on WS
        """
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        
        print("<<< " + message)

        command, headers, body = self._parse_message(message)

        # if connected, let Stomp know
        if command == "CONNECTED":
            self.stomp.connected = True
            print("Successfully connected to STOMP server")

        # if error received, log it
        if command == "ERROR":
            print(f"ERROR: {headers.get('message', 'Unknown error')}")
            if body:
                print(f"Details: {body}")

        # if message received, call appropriate callback
        if command == "MESSAGE":
            try:
                self.stomp.callback_registry[headers['destination']](body)
            except KeyError:
                print(f"Warning: No callback registered for destination {headers.get('destination', 'unknown')}")

    def _on_error(self, ws, error):
        """
        Executed when WS connection errors out
        """
        print(error)

    def _on_close(self, ws, close_status_code=None, close_msg=None):
        """
        Executed when WS connection is closed
        """
        print("### closed ###")

    def _on_open(self, ws):
        """
        Executed when WS connection is opened
        """
        self.opened = True

    def _transmit(self, command, headers, msg=None):
        """
        Marshalls and transmits the frame
        """
        # Contruct the frame
        lines = []
        lines.append(command + BYTE['LF'])

        # add headers
        for key in headers:
            lines.append(key + ":" + headers[key] + BYTE['LF'])

        lines.append(BYTE['LF'])

        # add message, if any
        if msg is not None:
            lines.append(msg)

        # terminate with null octet
        lines.append(BYTE['NULL'])
    
        frame = ''.join(lines)

        # transmit over ws
        print(">>>" + frame)
        try:
            self.ws.send(frame)
        except (websocket.WebSocketConnectionClosedException, ConnectionResetError) as e:
            print(f"Error sending message: {e}")
            print("Connection to remote host was lost.")
            # Attempt to reconnect could be implemented here

    def _parse_message(self, frame):
        """
        Returns:
            command
            headers
            body

        Args:
            frame: raw frame string
        """
        if isinstance(frame, bytes):
            frame = frame.decode('utf-8')
            
        lines = frame.split(BYTE['LF'])

        command = lines[0].strip()
        headers = {}

        # get all headers
        i = 1
        while i < len(lines) and lines[i] != '':
            # get key, value from raw header
            header_parts = lines[i].split(':', 1)
            if len(header_parts) == 2:
                key, value = header_parts
                headers[key] = value
            i += 1

        # set body to None if there is no body or index out of range
        body = None
        if i + 1 < len(lines):
            body = None if lines[i+1] == BYTE['NULL'] else lines[i+1]

        return command, headers, body

    def connect(self):
        """
        Transmit a CONNECT frame
        """
        headers = {}

        headers['host'] = self.stomp.url
        headers['accept-version'] = VERSIONS
        # Set heart-beat to '10000,10000' meaning:
        # - Client sends heartbeat every 10 seconds
        # - Client expects server heartbeat every 10 seconds
        headers['heart-beat'] = '10000,10000'
        
        # Add login credentials if provided
        if self.stomp.username is not None:
            headers['login'] = self.stomp.username
        if self.stomp.password is not None:
            headers['passcode'] = self.stomp.password

        self._transmit('CONNECT', headers)

    def subscribe(self, destination):
        """
        Transmit a SUBSCRIBE frame
        """
        headers = {}

        # Generate a unique ID based on timestamp
        import time
        import uuid
        sub_id = f"sub-{int(time.time())}-{str(uuid.uuid4())[:8]}"
        
        headers['id'] = sub_id
        headers['ack'] = 'client'
        headers['destination'] = destination

        self._transmit('SUBSCRIBE', headers)
        
    def send(self, destination, message):
        """
        Transmit a SEND frame
        """
        headers = {}
        headers['destination'] = destination
        headers['content-length'] = str(len(message))
        
        self._transmit('SEND', headers, msg=message)
        
    def disconnect(self):
        """
        Transmit a DISCONNECT frame
        """
        headers = {}
        self._transmit('DISCONNECT', headers)
        
    def heartbeat(self):
        """
        Send a heartbeat to the server
        
        STOMP protocol specifies that heartbeats are empty frames (no command)
        Some servers may require an EOL character (BYTE['LF'])
        """
        try:
            self.ws.send(BYTE['LF'])
        except (websocket.WebSocketConnectionClosedException, ConnectionResetError) as e:
            print(f"Error sending heartbeat: {e}")
            print("Connection to remote host was lost.")
