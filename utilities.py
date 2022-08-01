#!/usr/bin/python3
"""
Script to put C5 in production on a remote host
And some utilities
"""

import os
import sys
import re
import json
import socket
import ssl
import time
import urllib.request
import aiohttp
from aiohttp import web

def local_ip():
    """Get the local IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'

def get_certificate(server=True):
    """Returns None if no certificate needed"""
    if C5_CERT == 'SS': # Encryption is done by NGINX
        if server:
            cert = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        else:
            cert = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        cert.load_cert_chain(certfile="SSL/localhost.crt", keyfile="SSL/localhost.key")
        return cert
    return None

class CourseConfig: # pylint: disable=too-many-instance-attributes
    """A course session"""
    configs = {}
    def __init__(self, course):
        self.course = course
        self.filename = course + '.cf'
        self.time = 0
        self.load()
        self.update()
        self.configs[course] = self

    def load(self):
        """Load course configuration file"""
        self.config = {'start': "2000-01-01 00:00:00",
                       'stop': "2100-01-01 00:00:00",
                       'tt': '',
                       'teachers': 'nobody',
                       'copy_paste': '0',
                      }
        self.time = time.time()
        try:
            with open(self.filename, 'r') as file:
                self.config.update(eval(file.read())) # pylint: disable=eval-used
        except IOError:
            if os.path.exists(self.filename.replace('.cf', '.js')):
                self.record()
                self.time = time.time()

    def update(self):
        """Compute some values"""
        self.start = self.config['start']
        self.start_timestamp = time.mktime(time.strptime(self.start, '%Y-%m-%d %H:%M:%S'))
        self.stop = self.config['stop']
        self.stop_timestamp = time.mktime(time.strptime(self.stop, '%Y-%m-%d %H:%M:%S'))
        self.stop_tt_timestamp = self.start_timestamp + (
            self.stop_timestamp - self.start_timestamp) * 4 / 3
        self.stop_tt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.stop_tt_timestamp))
        self.tt_list = set(re.split('[ \n\r\t]+', self.config['tt']))
        self.tt_list.add('')
        self.teachers = set(re.split('[ \n\r\t]+', self.config['teachers']))
    def record(self):
        """Record option on disk"""
        with open(self.course + '.cf', 'w') as file:
            file.write(repr(self.config))
        self.time = time.time()
    def set_parameter(self, parameter, value):
        """Set one of the parameters"""
        self.config[parameter] = value
        self.update()
        self.record()
    def get_stop(self, login):
        """Get stop date, taking login into account"""
        if login in self.tt_list:
            return self.stop_tt_timestamp
        return self.stop_timestamp
    def status(self, login):
        """Status of the course"""
        if os.path.getmtime(self.filename) > self.time:
            self.load()
            self.update()
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        if now < self.start:
            return 'pending'
        if now < self.stop:
            return 'running'
        if login in self.tt_list and now < self.stop_tt:
            return 'running_tt'
        return 'done'
    def running(self, login):
        """If the session running for the user"""
        return self.status(login).startswith('running')

    @classmethod
    def get(cls, course):
        """Get a config from cache"""
        config = cls.configs.get(course, None)
        if config:
            return config
        return CourseConfig(course)

class Config:
    """C5 configuration"""
    masters = []
    ticket_ttl = 86400
    def __init__(self):
        self.config = {
            'masters': self.masters,
            'ticket_ttl': self.ticket_ttl,
        }
        self.load()
    def load(self):
        """Load configuration from file"""
        if os.path.exists('c5.cf'):
            with open('c5.cf', 'r') as file:
                self.config.update(json.loads(file.read()))
        self.update()
    def update(self):
        """Update configuration attributes"""
        self.masters = self.config['masters']
        self.ticket_ttl = self.config['ticket_ttl']
    def json(self):
        """For browser or to save"""
        return json.dumps(self.config)
    def save(self):
        """Save the configuration"""
        with open('c5.cf', 'w') as file:
            file.write(self.json())
    def set_value(self, key, value):
        """Update the configuration"""
        self.config[key] = value
        self.save()
        self.update()
    def is_admin(self, login):
        """Returns True if it is an admin login"""
        if login in self.masters:
            return True
        if self.masters:
            return False
        # No master, so check the login
        return not login[-1].isdigit()

CONFIG = Config()

class Session:
    """Session management"""
    session_cache = {}
    def __init__(self, ticket, client_ip, browser, login=None, creation_time=None):
        self.ticket = ticket
        self.client_ip = client_ip
        self.browser = browser
        self.login = login
        if creation_time is None:
            creation_time = time.time()
        self.creation_time = creation_time
    async def get_login(self, service):
        """Return a validated login"""
        if self.login:
            return self.login
        service = service.replace(f'http://{C5_IP}:{C5_HTTP}/', f'https://{C5_URL}/')
        if C5_VALIDATE:
            async with aiohttp.ClientSession() as session:
                url = C5_VALIDATE % (urllib.request.quote(service),
                                               urllib.request.quote(self.ticket))
                async with session.get(url) as data:
                    lines = await data.text()
                    lines = lines.split('\n')
                    if lines[0] == 'yes':
                        self.login = lines[1].lower()
                        self.record()
            if not self.login:
                print(('?', service))
                raise web.HTTPFound(C5_REDIRECT + urllib.request.quote(service))
        else:
            if self.ticket and self.ticket.isdigit():
                self.login = f'Anon#{self.ticket}'
                self.record()
            else:
                raise web.HTTPFound(
                    service + f'?ticket={int(time.time())}{len(self.session_cache)}')

        return self.login
    def record(self):
        """Record the ticket for the compile server"""
        with open(f'TICKETS/{self.ticket}', 'w') as file:
            file.write(str(self))
    def __str__(self):
        return repr((self.client_ip, self.browser, self.login, self.creation_time))
    def too_old(self):
        if time.time() - self.creation_time > CONFIG.ticket_ttl:
            try:
                os.unlink(f'TICKETS/{self.ticket}')
            except FileNotFoundError:
                # Yet removed by another process
                pass
            if self.ticket in self.session_cache:
                del self.session_cache[self.ticket]
            return True
        return False
    def check(self, request, client_ip, browser):
        """Check for hacker"""
        if self.client_ip != client_ip or self.browser != browser or self.too_old():
            raise web.HTTPFound(str(request.url).split('?')[0])

    @classmethod
    def load_ticket_file(cls, ticket):
        """Load the ticket from file"""
        with open(f'TICKETS/{ticket}', 'r') as file:
            session = Session(ticket, *eval(file.read())) # pylint: disable=eval-used
        cls.session_cache[ticket] = session
        return session

    @classmethod
    def get(cls, request, ticket=None):
        """Get or create a session.
        Raise an error if hacker.
        """
        if not ticket:
            ticket = request.query.get('ticket', '')
        try:
            # aiohttp
            headers = request.headers
            client_ip, _port = request.transport.get_extra_info('peername')
        except AttributeError:
            # websocket
            headers = request.request_headers
            client_ip, _port = request.remote_address
        forward = headers.get('x-forwarded-for', '')
        if forward:
            client_ip = forward.split(",")[0]
        browser = headers.get('user-agent', '')
        if ticket in cls.session_cache:
            session = cls.session_cache[ticket]
            session.check(request, client_ip, browser)
        elif ticket and os.path.exists(f'TICKETS/{ticket}'):
            session = cls.load_ticket_file(ticket)
            session.check(request, client_ip, browser)
        else:
            session = Session(ticket, client_ip, browser)
            if ticket:
                cls.session_cache[ticket] = session
        return session
    def is_admin(self):
        """The user is admin"""
        return CONFIG.is_admin(self.login)

    def header(self, courses=(), more=''):
        """Standard header"""
        return f"""<!DOCTYPE html>
            <html>
            <head>
            <base href="https://{C5_URL}/">
            <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="/favicon.ico?ticket={self.ticket}">
            </head>
            <body></body></html>
            <script>
            TICKET = {json.dumps(self.ticket)};
            COURSES = {json.dumps(courses)};
            MORE = {json.dumps(more)};
            LOGIN = {json.dumps(self.login)};
            CONFIG = {CONFIG.json()};
            </script>
            """

C5_HOST = os.getenv('C5_HOST', local_ip())           # Production host (for SSH)
C5_IP = os.getenv('C5_IP', local_ip())               # For Socket IP binding
C5_ROOT = os.getenv('C5_ROOT', 'root')               # login allowed to sudo
C5_LOGIN = os.getenv('C5_LOGIN', os.getlogin())      # c5 login
C5_HTTP = int(os.getenv('C5_HTTP', '8000'))          # HTTP server port
C5_SOCK = int(os.getenv('C5_SOCK', '4200'))          # WebSocket server port
C5_MAIL = os.getenv('C5_MAIL', f'root@{C5_ROOT}')    # For Let's encrypt certificate
C5_CERT = os.getenv('C5_CERT', 'SS')                 # Encrypt by self or NGINX
C5_URL = os.getenv('C5_URL', f'{C5_HOST}:{C5_HTTP}') # c5 public URL
C5_DIR = os.getenv('C5_DIR', 'C5')                   # c5 install directory name
C5_WEBSOCKET = os.getenv('C5_WEBSOCKET', f'{C5_HOST}:{C5_SOCK}') # c5 public websocket
# CAS redirection as: 'https://cas.univ-lyon1.fr/login?service='
C5_REDIRECT = os.getenv('C5_REDIRECT', '')
# CAS login validation as:  'https://cas.univ-lyon1.fr/cas/validate?service=%s&ticket=%s'
C5_VALIDATE = os.getenv('C5_VALIDATE', '')
C5_LOCAL = int(os.getenv('C5_LOCAL', '1'))

def print_state():
    """Print the current configuration"""
    print(f"""Uses environment shell variables :
{'C5_HOST=' + str(C5_HOST):<40}     # Production host (for SSH)
{'C5_IP=' + str(C5_IP):<40}     # For Socket IP binding
{'C5_ROOT=' + str(C5_ROOT):<40}     # login allowed to sudo
{'C5_LOGIN=' + str(C5_LOGIN):<40}     # c5 login
{'C5_HTTP=' + str(C5_HTTP):<40}     # Port number for HTTP
{'C5_SOCK=' + str(C5_SOCK):<40}     # Port number for WebSocket
{'C5_MAIL=' + str(C5_MAIL):<40}     # Mail address to create Let's Encrypt certificate
{'C5_CERT=' + str(C5_CERT):<40}     # SS: C5/SSL directory, NGINX: NGINX
{'C5_LOCAL=' + str(C5_LOCAL):<40}     # Run on local host
{'C5_URL=' + str(C5_URL):<40}     # Browser visible address
{'C5_DIR=' + str(C5_DIR):<40}     # c5 install directory name
{'C5_WEBSOCKET=' + str(C5_WEBSOCKET):<40}     # Browser visible address for WebSocket
{'C5_REDIRECT=' + str(C5_REDIRECT):<40} # CAS redirection
{'C5_VALIDATE=' + str(C5_VALIDATE):<40} # CAS get login
""")

def print_help():
    """Print help and default configuration values"""
    print(f"""Arguments may be:
   * os : configure production OS
   * SSL-LE : create SSL Certificate with Let's Encrypt (NGINX does the encrypting)
   * SSL-SS : create a Self Signed certificate (c5 does the encrypting itself)
   * nginx : configure NGINX (needs SSL-LE certificate)
   * c5 : update C5 source (pull)
   * start : servers
   * stop : servers
   * restart : servers
   * open : launch web browser (second argument may be js|python|cpp|remote)
""")
    print_state()
    os.system("ps -fe | grep -e http_server.py -e compile_server.py | grep -v grep")
    sys.exit(1)

ACTIONS = {
    'os': """#C5_ROOT
        sudo sh -c '
            set -e
            apt update
            apt -y install nginx certbot python3-websockets python3-aiohttp npm
            apt -y upgrade
            # set-timezone Europe/Paris
            '
        """,
    'c5': f"""#C5_LOGIN
        set -e
        if [ -d {C5_DIR} ]
        then
            cd {C5_DIR}
            git pull
        else
            git clone https://github.com/texcoffier/C5.git
            git config pull.ff only
            cd {C5_DIR}
        fi
        """,
    'cp': f"""
        scp $(git ls-files) favicon.ico {C5_LOGIN}@{C5_HOST}:{C5_DIR}
        """,
    'nginx': f"""#C5_ROOT
        sudo sh -c '
            cat >/etc/nginx/sites-available/default <<%
server {{
    listen 443 ssl;
    server_name {C5_URL};
    ssl_certificate /etc/letsencrypt/live/{C5_URL}/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/{C5_URL}/privkey.pem; # managed by Certbot
    location /WebSocket/ {{
        proxy_pass http://127.0.0.1:{C5_SOCK};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\\\\$http_upgrade;
        proxy_set_header Connection Upgrade;
        proxy_set_header Host \\\\\\$host;
        }}
    location ~ {{
    proxy_pass http://127.0.0.1:{C5_HTTP};
    }}
  }}
%
            systemctl restart nginx
'
    """,
    'SSL-LE': f"""#C5_ROOT
        sudo sh -c '
            set -e
            if [ -d /etc/letsencrypt/live/{C5_URL} ]
                then
                exit 0
                fi
            certbot certonly --standalone -d {C5_URL} -m {C5_MAIL}
            '
        """,
    'SSL-SS': f"""#C5_LOGIN
        set -e
        cd {C5_DIR}
        if [ -d SSL ]
            then
            exit 0
            fi
        mkdir SSL
        cd SSL
        openssl req -x509 -nodes -new -sha256 -days 1024 -newkey rsa:2048 -keyout RootCA.key -out RootCA.pem -subj '/C=US/CN=_______C5_______'
        openssl x509 -outform pem -in RootCA.pem -out RootCA.crt
        echo '
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names
[alt_names]
DNS.1 = localhost:{C5_SOCK}
DNS.2 = 127.0.0.1:{C5_SOCK}
DNS.3 = localhost:{C5_HTTP}
DNS.4 = 127.0.0.1:{C5_HTTP}
DNS.5 = {local_ip()}:{C5_HTTP}
DNS.6 = {local_ip()}:{C5_SOCK}
DNS.7 = {C5_URL}
' >domains.ext
        openssl req -new -nodes -newkey rsa:2048 -keyout localhost.key -out localhost.csr -subj '/C=US/ST=YourState/L=YourCity/O=Example-Certificates/CN=localhost.local'
        openssl x509 -req -sha256 -days 1024 -in localhost.csr -CA RootCA.pem -CAkey RootCA.key -CAcreateserial -extfile domains.ext -out localhost.crt

        echo '
********************************************************************
********************************************************************
You must indicate to the browser to add a security exception
********************************************************************
********************************************************************
With Firefox:
    * about:preferences
    * Search «certificate»
    * Click on the button «View certificates»
    * Goto on tab «Servers»
    * Click on «Add exception»
    * Add : «https://{C5_URL}»
    * Add : «https://{C5_WEBSOCKET}»
    * Confirm
********************************************************************
        '
    """,
    'start': fr"""#C5_LOGIN
        set -e
        echo START SERVERS
        cd {C5_DIR} 2>/dev/null || true
        mkdir TICKETS 2>/dev/null || true
        make prepare
        if [ '' != '{C5_URL}' ]
        then
            ./http_server.py >>http_server.log 2>&1 &
            echo \$! >http_server.pid
            ./compile_server.py >>compile_server.log 2>&1 &
            echo \$! >compile_server.pid
            sleep 0.5
            tail -1 http_server.log
            tail -1 compile_server.log
        fi
        """,
    'stop': fr"""#C5_LOGIN
        echo STOP SERVERS
        cd {C5_DIR}
        kill \$(cat http_server.pid) \$(cat compile_server.pid) || true
        rm http_server.pid compile_server.pid
        """,
    'open': f"""
        xdg-open https://{C5_URL}/=course_{sys.argv[2] if len(sys.argv) >= 3 else 'js'}.js
        """,
    'load': "./load_testing.py"
}
ACTIONS['restart'] = ACTIONS['stop'] + 'sleep 1\n' + ACTIONS['start']

def main():
    """MAIN"""
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print_help()
    action = sys.argv[1]
    if action != 'open':
        print(f"{' '.join(sys.argv)}")
        print_state()
    action = f"""
export C5_HOST={C5_HOST}
export C5_IP={C5_IP}
export C5_ROOT={C5_ROOT}
export C5_LOGIN={C5_LOGIN}
export C5_HTTP={C5_HTTP}
export C5_URL={C5_URL}
export C5_DIR={C5_DIR}
export C5_SOCK={C5_SOCK}
export C5_MAIL={C5_MAIL}
export C5_CERT={C5_CERT}
export C5_WEBSOCKET='{C5_WEBSOCKET}'
export C5_REDIRECT='{C5_REDIRECT}'
export C5_VALIDATE='{C5_VALIDATE}'
export C5_LOCAL='{C5_LOCAL}'
""" + ACTIONS[action]
    assert '"' not in action
    if '#C5_ROOT' in action:
        if C5_LOCAL:
            action = 'cd ..; sh -c "' + action + '"'
        else:
            action = f'ssh {C5_ROOT}@{C5_HOST} "' + action + '"'
    elif '#C5_LOGIN' in action:
        if C5_LOCAL:
            action = 'cd ..; sh -c "' + action + '"'
        else:
            action = f'ssh {C5_LOGIN}@{C5_HOST} "' + action + '"'
    sys.exit(os.system(action))

if __name__ == "__main__":
    main()
