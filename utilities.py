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
import glob
import urllib.request
import asyncio
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


class LDAP_process: # pylint: disable=invalid-name
    """Create a LDAP process and get information from it.
    It is more simple than using an asyncio LDAP library.
    """
    ldap_cache = {}
    process = None

    async def start(self):
        """
        Start a process reading login on stdin and write information on stdout
        """
        self.process = await asyncio.create_subprocess_shell(
            "exec ./infos_server.py",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            )
        asyncio.ensure_future(self.reader())

    async def reader(self):
        """Parse infos from LDAP process"""
        while True:
            infos = await self.process.stdout.readline()
            infos = json.loads(infos)
            self.ldap_cache[infos[0]] = infos[1]

    async def infos(self, login):
        """Get the informations about login"""
        if login in self.ldap_cache:
            return self.ldap_cache[login]
        self.process.stdin.write(login.encode('utf-8') + b'\n')
        while login not in self.ldap_cache:
            await asyncio.sleep(0.1)
        return self.ldap_cache[login]

LDAP = LDAP_process()

class CourseConfig: # pylint: disable=too-many-instance-attributes
    """A course session"""
    configs = {}
    def __init__(self, course):
        if not os.path.exists(course + '.py'):
            self.dirname = ''
            return
        self.course = course.replace('COMPILE_', '').replace('/', '=')
        self.filename = course + '.cf'
        self.dirname = course
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
                       'checkpoint': '0',
                       'sequential': '1',
                       'theme': 'a11y-light',
                       'messages': [],
                       # For each student login :
                       #   * Active: True is the examination is possible.
                       #   * the teacher who checkpointed  (or '')
                       #   * Room: the building and the place
                       #   * timestamp of last student interaction
                       #   * Number of window blur
                       #   * Number of questions
                       #   * IP address
                       # Active : examination is running
                       # Inactive & Room=='' : wait access to examination
                       # Inactive & Room!='' : examination done
                       'active_teacher_room': {},
                      }
        self.time = time.time()
        try:
            with open(self.filename, 'r') as file:
                self.config.update(eval(file.read())) # pylint: disable=eval-used
        except (IOError, FileNotFoundError):
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
        self.checkpoint = int(self.config['checkpoint'])
        self.sequential = int(self.config['sequential'])
        self.theme = self.config['theme']
        self.active_teacher_room = self.config['active_teacher_room']
        self.messages = self.config['messages']
    def record(self):
        """Record option on disk"""
        with open(self.filename, 'w') as file:
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
    def status(self, login, client_ip=None): # pylint: disable: too-many-return-statements
        """Status of the course"""
        if os.path.getmtime(self.filename) > self.time:
            self.load()
            self.update()
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        if now < self.start:
            return 'pending'
        if self.checkpoint and login:
            active_teacher_room = self.active_teacher_room.get(login, None)
            if active_teacher_room is None:
                seconds = int(time.time())
                # Add to the checkpoint room
                self.config['active_teacher_room'][login] = [
                    False, '', '', seconds, 0, 0, client_ip]
                self.record()
                with open(f'{self.dirname}/{login}/http_server.log', "a") as file:
                    file.write(f'[{seconds},"checkpoint_in"]\n')
                return 'checkpoint'
            if client_ip:
                # XXX Connecté à 2 IP différentes en même temps
                active_teacher_room[6] = client_ip # Update
            if not active_teacher_room[0]:
                if active_teacher_room[1] == '':
                    # Always in the checkpoint or examination is done
                    return 'checkpoint'
                return 'done'
        if now < self.stop:
            return 'running'
        if login in self.tt_list and now < self.stop_tt:
            return 'running_tt'
        return 'done'
    def running(self, login):
        """If the session running for the user"""
        return self.status(login).startswith('running') or not CONFIG.is_student(login)

    async def get_students(self):
        """Get all the students"""
        # Clearly not efficient
        return [
            [student, active_teacher_room, await LDAP.infos(student)]
            for student, active_teacher_room in self.active_teacher_room.items()
            ]

    @classmethod
    def get(cls, course):
        """Get a config from cache"""
        config = cls.configs.get(course, None)
        if config:
            return config
        return CourseConfig(course)

    @classmethod
    def load_all_configs(cls):
        """Read all configuration from disk"""
        for course in sorted(glob.glob('COMPILE_*/*.py')):
            cls.get(course[:-3])

def get_course(txt):
    """Transform «PYTHON:introduction» as «COMPILE_PYTHON/introduction»"""
    compilator, course = txt.split('=')
    return f'COMPILE_{compilator}/{course}'

class Config:
    """C5 configuration"""
    masters = []
    ticket_ttl = 86400
    computers = []
    student = None
    def __init__(self):
        self.config = {
            'masters': self.masters,
            'ticket_ttl': self.ticket_ttl,
            'computers': [],
            'ips_per_room': {"Nautibus,TP3": "192.168.0.1 192.168.0.2"},
            'student': '[0-9][0-9]$',
            'messages': {
                'unknown': "Cette session n'existe pas",
                'checkpoint': "Donnez votre nom à l'enseignant pour qu'il vous ouvre l'examen.<br>Rechargez cette page quand l'intervenant vous le dira.",
                'done': "La session d'exercice ou d'examen est terminée",
                'not_admin': "Vous n'êtes pas administrateur C5",
                'not_teacher': "Vous ne surveillez pas cet examen",
                'pending': "La session d'exercice ou d'examen n'a pas commencé",
                }
        }
        self.load()
    def load(self):
        """Load configuration from file"""
        if os.path.exists('c5.cf'):
            with open('c5.cf', 'r') as file:
                self.config.update(json.loads(file.read()))
        else:
            self.save()
        self.update()
    def update(self):
        """Update configuration attributes"""
        self.masters = self.config['masters']
        self.ticket_ttl = self.config['ticket_ttl']
        self.computers = self.config['computers']
        self.student = re.compile(self.config['student'])
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
        # No master, so all teachers are master
        return not self.is_student(login)
    def is_student(self, login):
        """The user is a student"""
        return self.student.search(login)

CONFIG = Config()

class Session:
    """Session management"""
    session_cache = {}
    def __init__(self, ticket, client_ip, browser, # pylint: disable=too-many-arguments
                 login=None, creation_time=None, infos=None):
        self.ticket = ticket
        self.client_ip = client_ip
        self.browser = browser
        self.login = login
        self.infos = infos
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
                        self.infos = await LDAP.infos(self.login)
                        self.record()
            if not self.login:
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
        return repr((self.client_ip, self.browser, self.login, self.creation_time, self.infos))
    def too_old(self):
        """Return True if the ticket is too old"""
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
    async def get(cls, request, ticket=None):
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
        if not session.login:
            await session.get_login(str(request.url).split('?')[0])
        return session
    def is_admin(self):
        """The user is admin"""
        return CONFIG.is_admin(self.login)
    def is_student(self):
        """The user is a student"""
        return CONFIG.is_student(self.login)

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

    def redirect(self, where):
        """In case of problem redirect to an error page"""
        raise web.HTTPFound(f'https://{C5_URL}/{where}?ticket={self.ticket}')

    def message(self, key, exception=False):
        """Error message for the user in a standalone page"""
        if exception:
            fct = web.HTTPSuccessful
        else:
            fct = web.Response
        return fct(
            body=f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="/favicon.ico?ticket={self.ticket}">
            </head>
            <h1>{CONFIG.config['messages'][key]}</h1>
            """,
            content_type='text/html',
            headers={'Cache-Control': 'no-cache'}
            )

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
C5_LDAP = os.getenv('C5_LDAP')
C5_LDAP_LOGIN = os.getenv('C5_LDAP_LOGIN')
C5_LDAP_PASSWORD = os.getenv('C5_LDAP_PASSWORD')
C5_LDAP_BASE = os.getenv('C5_LDAP_BASE')
C5_LDAP_ENCODING = os.getenv('C5_LDAP_ENCODING', 'utf-8')

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
{'C5_LDAP=' + str(C5_LDAP):<40}     # LDAP URL
{'C5_LDAP_LOGIN=' + str(C5_LDAP_LOGIN):<40}     # LDAP reader login
{'C5_LDAP_PASSWORD=' + str(C5_LDAP_PASSWORD):<40}     # LDAP reader password
{'C5_LDAP_BASE=' + str(C5_LDAP_BASE):<40}     # LDAP user search base
{'C5_LDAP_ENCODING=' + str(C5_LDAP_ENCODING):<40}     # LDAP character encoding
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
   * compile : create JS
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
            apt -y install nginx certbot python3-websockets python3-ldap python3-aiohttp npm
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
        tar -cf - $(git ls-files | grep -v DOCUMENTATION) |
        ssh {C5_LOGIN}@{C5_HOST} 'cd {C5_DIR} ; tar -xvf -'
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
DNS.7 = {C5_HOST}:{C5_SOCK}
DNS.8 = {C5_URL}
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
        xdg-open https://{C5_URL}/={sys.argv[2] if len(sys.argv) >= 3 else 'JS=introduction'}
        """,
    'load': "./load_testing.py",
    'compile': fr"""#C5_LOGIN
        set -e
        echo START SERVERS
        cd {C5_DIR} 2>/dev/null || true
        mkdir TICKETS 2>/dev/null || true
        make prepare
        """,
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
export C5_LDAP='{C5_LDAP}'
export C5_LDAP_LOGIN='{C5_LDAP_LOGIN}'
export C5_LDAP_PASSWORD='{C5_LDAP_PASSWORD}'
export C5_LDAP_BASE='{C5_LDAP_BASE}'
export C5_LDAP_ENCODING='{C5_LDAP_ENCODING}'

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
