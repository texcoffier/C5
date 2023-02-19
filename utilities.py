#!/usr/bin/python3
"""
Script to put C5 in production on a remote host
And some utilities
"""

from typing import Dict, List, Tuple, Any, Optional
import os
import sys
import re
import json
import socket
import ssl
import time
import glob
import atexit
import urllib.request
import urllib.parse
import asyncio
import aiohttp
from aiohttp import web

def local_ip() -> str:
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


class Process: # pylint: disable=invalid-name
    """Create a LDAP or DNS process and get information from it.
    It is more simple than using an asyncio LDAP library.
    """
    cache:Dict[Any,Any] = {}
    started:bool = None

    def __init__(self, command):
        self.command = command

    async def start(self) -> None:
        """
        Start a process reading login on stdin and write information on stdout
        """
        self.process = await asyncio.create_subprocess_shell( # pylint: disable=attribute-defined-outside-init
            "exec " + self.command,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            )
        asyncio.ensure_future(self.reader())
        atexit.register(self.process.kill)

    async def reader(self) -> None:
        """Parse infos from process"""
        if not self.process.stdout:
            raise ValueError('Bug')
        while True:
            infos = await self.process.stdout.readline()
            infos = json.loads(infos)
            self.cache[infos[0]] = infos[1]

    async def infos(self, key:str) -> Dict[str, str]:
        """Get the informations about key"""
        if not self.started:
            if self.started is None:
                self.started = False
                await self.start()
            else:
                while not hasattr(self, "process"):
                    await asyncio.sleep(0.1)
        if not self.process.stdin:
            raise ValueError('Bug')
        if key in self.cache:
            return self.cache[key]
        while not self.process:
            await asyncio.sleep(0.1)
        self.process.stdin.write(key.encode('utf-8') + b'\n')
        while key not in self.cache:
            await asyncio.sleep(0.1)
        return self.cache[key]

LDAP = Process('./infos_server.py')
DNS = Process('./dns_server.py')

def student_log(course_name:str, login:str, data:str) -> None:
    """Add a line to the student log"""
    if not os.path.exists(f'{course_name}/{login}'):
        if not os.path.exists(course_name):
            os.mkdir(course_name)
        os.mkdir(f'{course_name}/{login}')
    with open(f'{course_name}/{login}/http_server.log', "a", encoding='utf-8') as file:
        file.write(data)

class CourseConfig: # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """A course session"""
    configs:Dict[str,"CourseConfig"] = {}
    def __init__(self, course):
        if not os.path.exists(course + '.py'):
            self.dirname = ''
            return
        self.course = course.replace('COMPILE_', '').replace('/', '=')
        self.compiler, self.session = self.course.split('=', 1)
        self.filename = course + '.cf'
        self.dirname = course
        self.time = 0
        self.disabled = False
        self.parse_position = 0
        self.load()
        self.update()
        self.configs[course] = self
        try:
            with open(self.dirname + '.json', 'r', encoding="ascii") as file:
                self.questions = json.loads(file.read())
        except FileNotFoundError:
            self.questions = []

    def load(self):
        """Load course configuration file"""
        self.config = {'start': "2000-01-01 00:00:00",
                       'stop': "2100-01-01 00:00:00",
                       'tt': '',
                       'creator': 'nobody',
                       'admins': '',
                       'graders': '',
                       'proctors': '',
                       'copy_paste': '0',
                       'coloring': '1',
                       'checkpoint': '0',
                       'allow_ip_change': '0',
                       'save_unlock': '0',
                       'sequential': '1',
                       'theme': 'a11y-light',
                       'highlight': '#FFF',
                       'notation': '',
                       'messages': [],
                       # For each student login :
                       #   [0] Active: True is the examination is possible.
                       #   [1] the teacher who checkpointed  (or '')
                       #   [2] Room: the building and the place
                       #   [3] timestamp of last student interaction
                       #   [4] Number of window blur
                       #   [5] Number of questions
                       #   [6] IP address
                       #   [7] Bonus time in seconds
                       #   [8] Grade
                       # Active : examination is running
                       # Inactive & Room=='' : wait access to examination
                       # Inactive & Room!='' : examination done
                       'active_teacher_room': {},
                       # The session state:
                       # ┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
                       # ┃ State  ┃    Visible by      ┃    Usable by       ┃
                       # ┡━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
                       # ┃Draft   ┃creator admin       │creator admin       │
                       # ┣━━━━━━━━╉────────────────────┼────────────────────┤
                       # ┃Ready   ┃                    │                    │
                       # ┃  before┃all                 │creator admin grader│
                       # ┃  while ┃all                 │all if no checkpoint│
                       # ┃  after ┃all except students │creator admin grader│
                       # ┣━━━━━━━━╉────────────────────┼────────────────────┤
                       # ┃Grade   ┃creator admin grader│creator admin grader│
                       # ┣━━━━━━━━╉────────────────────┼────────────────────┤
                       # ┃Done    ┃creator admin grader│creator admin grader│
                       # ┣━━━━━━━━╉────────────────────┼────────────────────┤
                       # ┃Archive ┃creator admin       │creator admin       │
                       # ┗━━━━━━━━┹────────────────────┴────────────────────┘
                       'state': 'Ready',
                      }
        try:
            self.parse()
        except (IOError, FileNotFoundError):
            if os.path.exists(self.filename.replace('.cf', '.js')):
                self.record_config()
        except SyntaxError:
            print(f"Invalid configuration file: {self.filename}", flush=True)
            raise
        # Update old data structure
        for active_teacher_room in self.config['active_teacher_room'].values():
            if len(active_teacher_room) == 7:
                active_teacher_room.append(0)
            if len(active_teacher_room) == 8:
                active_teacher_room.append('')
        if self.config['highlight'] == '0':
            self.config['highlight'] = '#FFF'
        elif self.config['highlight'] == '1':
            self.config['highlight'] = '#0F0'

    def parse(self):
        """Parse the end of the file"""
        with open(self.filename, 'r', encoding='utf-8') as file:
            self.time = time.time()
            file.seek(self.parse_position)
            config = self.config
            try:
                for line in file:
                    data = eval(line) # pylint: disable=eval-used
                    if len(data) == 2:
                        config[data[0]] = data[1]
                    elif len(data) == 3:
                        config[data[0]][data[1]] = data[2]
                    else:
                        config[data[0]][data[1]][data[2]] = data[3]
                self.parse_position = file.tell()
            except KeyError:
                # Rewrite configuration with the new format
                config.update(data)
                self.record_config()
            except: # pylint: disable=bare-except
                print(self.filename)
                print(line)
                raise

    def record_config(self):
        """Record the default start configuration"""
        with open(self.filename, 'w', encoding='utf-8') as file:
            for key, value in self.config.items():
                if isinstance(value, dict):
                    for key2, value2 in value.items():
                        file.write(repr((key, key2, value2)) + '\n')
                else:
                    file.write(repr((key, value)) + '\n')
        self.parse_position = os.path.getsize(self.filename)
        self.time = time.time()

    def update(self) -> None:
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
        if 'teachers' in self.config:
            teachers = re.split('[ \n\r\t]+', self.config['teachers'])
            self.config['creator'] = teachers[0]
            self.config['graders'] = ' '.join(teachers[1:])
            del self.config['teachers']
        self.creator = self.config['creator']
        self.admins = set(re.split('[ \n\r\t]+', self.config['admins']))
        self.graders = set(re.split('[ \n\r\t]+', self.config['graders']))
        self.proctors = set(re.split('[ \n\r\t]+', self.config['proctors']))
        self.checkpoint = int(self.config['checkpoint'])
        self.sequential = int(self.config['sequential'])
        self.highlight = self.config['highlight']
        self.allow_ip_change = int(self.config['allow_ip_change'])
        self.notation = self.config['notation']
        self.theme = self.config['theme']
        self.active_teacher_room = self.config['active_teacher_room']
        self.messages = self.config['messages']
        self.state = self.config['state']
        self.update_disabled()

    def update_disabled(self) -> None:
        """Compute disabled state on load or C5 configuration change"""
        self.disabled = False
        for login, regexp in CONFIG.disabled.items():
            if login == self.creator or login in self.admins:
                if regexp.match(self.session):
                    self.disabled = True

    def number_of_active_students(self, last_seconds:int=600) -> int:
        """Compute the number of active students the last seconds"""
        nb_active = 0
        now = time.time()
        for info in self.active_teacher_room.values():
            if now - info[3] < last_seconds:
                nb_active += 1
        return nb_active

    def set_parameter(self, parameter:str, value:Any, key:str=None, index:int=None):
        """Set one of the parameters"""
        if key:
            if index is None:
                self.config[parameter][key] = value
            else:
                self.config[parameter][key][index] = value
        else:
            if self.config[parameter] == value:
                return
            self.config[parameter] = value
        self.update()
        with open(self.filename, 'a', encoding='utf-8') as file:
            timestamp = f' # {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
            if key:
                if index is None:
                    file.write(f'{(parameter, key, value)}{timestamp}')
                else:
                    file.write(f'{(parameter, key, index, value)}\n')
            else:
                file.write(f'{(parameter, value)}{timestamp}')
        self.time = time.time()
    def get_stop(self, login:str) -> int:
        """Get stop date, taking login into account"""
        if login in self.active_teacher_room:
            bonus_time = self.active_teacher_room[login][7]
        else:
            bonus_time = 0
        if login in self.tt_list:
            return self.stop_tt_timestamp + bonus_time
        return self.stop_timestamp + bonus_time
    def update_checkpoint(self, login:str, client_ip:Optional[str], now:int) -> Optional[Tuple]:
        """Update active_teacher_room"""
        if not login:
            return None
        active_teacher_room = self.active_teacher_room.get(login, None)
        if active_teacher_room is None:
            if not client_ip:
                # There is an http_server.log but nothing in session.cf
                client_ip = 'broken_cf_file'
            # Add to the checkpoint room
            active_teacher_room = [0, '', '', now, 0, 0, client_ip, 0, '']
            self.set_parameter('active_teacher_room', active_teacher_room, login)
            to_log = [now, ["checkpoint_in", client_ip]]
        elif client_ip and client_ip != active_teacher_room[6]:
            # Student IP changed
            if self.checkpoint and not self.allow_ip_change:
                # Undo checkpointing
                self.set_parameter('active_teacher_room', client_ip, login, 6)
                self.set_parameter('active_teacher_room', 0, login, 0)
                to_log = [now, ["checkpoint_ip_change_eject", client_ip]]
            else:
                # No checkpoint: so allows the room change
                self.set_parameter('active_teacher_room', client_ip, login, 6)
                to_log = [now, ["checkpoint_ip_change", client_ip]]
        else:
            to_log = None
        if to_log:
            student_log(self.dirname, login, json.dumps(to_log) + '\n')
        return active_teacher_room

    def status(self, login:str, client_ip:str=None) -> str: # pylint: disable=too-many-return-statements,too-many-statements,too-many-branches
        """Status of the course"""
        if os.path.getmtime(self.filename) > self.time:
            self.parse() # Load only the file end
            self.update()
        if self.disabled:
            return 'disabled'
        if self.state == 'Draft' and not self.is_admin(login):
            return 'draft'
        if self.state != 'Ready' and not self.is_grader(login):
            return 'done'
        now = int(time.time())
        if not login: # For adm home
            if now < self.start_timestamp:
                return 'pending'
            if now < self.stop_timestamp:
                return 'running'
            return 'done'
        if client_ip:
            active_teacher_room = self.update_checkpoint(login, client_ip, now)
            if not active_teacher_room:
                raise ValueError('Bug')
            if self.checkpoint and not active_teacher_room[0]:
                if active_teacher_room[1] == '':
                    # Always in the checkpoint or examination is done
                    return 'checkpoint'
                return 'done'
        if now < self.start_timestamp:
            return 'pending'
        if now < self.get_stop(login):
            return 'running'
        return 'done'

    def running(self, login:str, client_ip:str=None) -> bool:
        """If the session running for the user"""
        return self.status(login, client_ip).startswith('running') or not CONFIG.is_student(login)

    async def get_students(self) -> List[List[Any]]:
        """Get all the students"""
        if C5_VALIDATE:
            # Clearly not efficient
            return [
                [student, active_teacher_room, await LDAP.infos(student)]
                for student, active_teacher_room in self.active_teacher_room.items()
                ]
        return [
                [student, active_teacher_room, {'fn': 'FN' + student, 'sn': 'SN'+student}]
                for student, active_teacher_room in self.active_teacher_room.items()
                ]

    @classmethod
    def get(cls, course:str) -> "CourseConfig":
        """Get a config from cache"""
        config = cls.configs.get(course, None)
        if config:
            return config
        config = CourseConfig(course)
        if hasattr(config, 'time'):
            return config
        raise ValueError("Session inconnue : " + course)

    @classmethod
    def load_all_configs(cls) -> None:
        """Read all configuration from disk"""
        for course in sorted(glob.glob('COMPILE_*/*.py')):
            cls.get(course[:-3])

    def is_admin(self, login:str) -> bool:
        """Is admin or creator"""
        return login in self.admins or login == self.creator

    def is_grader(self, login:str) -> bool:
        """Is grader or admin or creator"""
        return login in self.graders or self.is_admin(login)

    def is_proctor(self, login:str) -> bool:
        """Is proctor or grader or admin or creator"""
        return login in self.proctors or self.is_grader(login)

    def get_language(self) -> Tuple[str, str, str]:
        """Return the file extension and the comment for the compiler"""
        if self.compiler == 'SQL':
            return 'sql', '-- ', ''
        if self.compiler == 'PYTHON':
            return 'py', '# ', ''
        if self.compiler in ('REMOTE', 'CPP'):
            return 'cpp', '//', 'CPPFLAGS=-Wall'
        if self.compiler == 'JS':
            return 'js', '//', ''
        return self.compiler, '// ', ''

    def get_question_name(self, question:int) -> str:
        """Get a question title usable as filename"""
        if question >= len(self.questions):
            return 'deleted' # The answered question no more exists
        title = self.questions[question]["title"
            ].replace(' ', '_').replace('/', '_').replace("'", "´")
        return f'{question+1:02d}-{title}'

    def get_question_filename(self, question:int) -> str:
        """Get a question title usable as filename"""
        return f'{self.get_question_name(question)}.{self.get_language()[0]}'

    def get_question_path(self, question:int) -> str:
        """Get a question title usable as filename"""
        return f'C5/{self.course}/{self.get_question_filename(question)}'

    def get_makefile(self) -> str:
        """Get the text content of the Makefile"""
        options = self.get_language()[2]
        if not options:
            return ''
        content = [
            options + '\n\n',
            'all:', '\n\n' # Item updated in the loop
            ]
        for question in range(len(self.questions)):
            exec_name = self.get_question_name(question)
            source_name = self.get_question_filename(question)
            content[1] += ' \\\n\t' + exec_name
            content.append(f"{exec_name}:{source_name}\n")
            content.append(f"{question+1:02}:{exec_name}\n\t./{exec_name}\n\n")
        return ''.join(content)

def get_course(txt:str) -> str:
    """Transform «PYTHON:introduction» as «COMPILE_PYTHON/introduction»"""
    compilator, course = txt.split('=')
    return f'COMPILE_{compilator}/{course}'

class Config: # pylint: disable=too-many-instance-attributes
    """C5 configuration"""
    authors:List[str] = []
    masters:List[str] = []
    mappers:List[str] = []
    roots:List[str] = []
    ticket_ttl = 86400
    computers:List[Tuple[str, int, int, str, int]] = []
    disabled:Dict[str, re.Pattern] = {} # Login and pattern
    json = ''
    def __init__(self):
        self.config = {
            'roots': self.roots,
            'masters': self.masters,
            'authors': self.authors,
            'mappers': self.mappers,
            'ticket_ttl': self.ticket_ttl,
            'computers': [],
            'ips_per_room': {"Nautibus,TP3": "b710l0301.univ-lyon1.fr b710l0302.univ-lyon1.fr"},
            'student': '[0-9][0-9]$',
            # For each session creator/admin: a regexp of sessions to disable
            'disabled': {},
            'messages': {
                'unknown': "Cette session n'existe pas",
                'checkpoint':
                    "Donnez votre nom à l'enseignant pour qu'il vous ouvre l'examen.<br>"
                    "Rechargez cette page quand l'intervenant vous le dira.",
                'done': "La session d'exercice ou d'examen est terminée",
                'not_root': "Vous n'êtes pas root C5",
                'not_grader': "Vous n'êtes pas un correcteur de la session",
                'not_proctor': "Vous n'êtes pas un surveillant de la session",
                'not_admin': "Vous n'êtes pas administrateur C5",
                'not_author': "Vous n'êtes pas créateur de session",
                'not_teacher': "Vous ne surveillez pas cet examen",
                'not_mapper': "Vous n'avez pas le droit de faire les plans",
                'pending': "La session d'exercice ou d'examen n'a pas commencé",
                }
        }
        self.load()
    def load(self) -> None:
        """Load configuration from file"""
        if os.path.exists('c5.cf'):
            with open('c5.cf', 'r', encoding='utf-8') as file:
                config = self.config
                try:
                    for line in file:
                        data = eval(line) # pylint: disable=eval-used
                        if len(data) == 2:
                            config[data[0]] = data[1]
                        elif len(data) == 3:
                            config[data[0]][data[1]] = data[2]
                        else:
                            config[data[0]][data[1]][data[2]] = data[3]
                    self.parse_position = file.tell()
                except KeyError:
                    # Rewrite configuration with the new format
                    self.config.update(data)
                    self.save()
                except: # pylint: disable=bare-except
                    print('c5.cf :', line)
                    raise
        else:
            self.save()
        self.update()
    def update(self) -> None:
        """Update configuration attributes"""
        self.authors = self.config['authors']
        self.masters = self.config['masters']
        self.mappers = self.config['mappers']
        self.roots = self.config['roots']
        self.ticket_ttl = self.config['ticket_ttl']
        self.computers = self.config['computers']
        self.student:re.Pattern = re.compile(self.config['student']) # pylint: disable=attribute-defined-outside-init
        self.disabled = {login: re.compile(regexp)
                         for login, regexp in self.config['disabled'].items()
                         if regexp
                        }
        for course in CourseConfig.configs.values():
            course.update_disabled()
        self.json = json.dumps(self.config)
    def save(self) -> None:
        """Save the configuration"""
        with open('c5.cf', 'w', encoding='utf-8') as file:
            for key, value in self.config.items():
                if isinstance(value, dict):
                    for key2, value2 in value.items():
                        file.write(f'{(key, key2, value2)}\n')
                else:
                    file.write(f'{(key, value)}\n')
    def set_value(self, key:str, value:Any, index:Any=None) -> None:
        """Update the configuration"""
        with open('c5.cf', 'a', encoding='utf-8') as file:
            if index is None:
                self.config[key] = value
                file.write(f'{(key,value)} # {time.strftime("%Y%m%d%H%M%S")}\n')
            else:
                self.config[key][index] = value
                file.write(f'{(key,index,value)} # {time.strftime("%Y%m%d%H%M%S")}\n')
        self.update()
    def set_value_dict(self, key:str, new_dict:Dict) -> None:
        """Update the configuration"""
        for old_key, old_value in tuple(self.config[key].items()):
            if old_key not in new_dict and old_value:
                self.set_value(key, '', old_key)
        for new, value in new_dict.items():
            if value != self.config[key].get(new, None):
                self.set_value(key, value, new)

    def is_root(self, login:str) -> bool:
        """Returns True if it is an root login"""
        if login in self.roots:
            return True
        if self.roots:
            return False
        return not self.is_student(login)
    def is_admin(self, login:str) -> bool:
        """Returns True if it is an admin login"""
        return login in self.masters or login in self.roots
    def is_author(self, login:str) -> bool:
        """Returns True if it is an author login"""
        return login in self.authors or login in self.masters or login in self.roots
    def is_mapper(self, login:str) -> bool:
        """Returns True if it is a mapper login"""
        return login in self.mappers or login in self.masters or login in self.roots
    def is_student(self, login:str) -> bool:
        """The user is a student"""
        return bool(self.student.search(login))

CONFIG = Config()

class Session:
    """Session management"""
    session_cache:Dict[str,"Session"] = {}
    edit:Optional[CourseConfig] = None # XXX Lost on server reboot
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
    async def get_login(self, service:str) -> str:
        """Return a validated login"""
        if self.login:
            return self.login
        service = service.replace(f'http://{C5_IP}:{C5_HTTP}/', f'https://{C5_URL}/')
        if C5_VALIDATE:
            async with aiohttp.ClientSession() as session:
                url = C5_VALIDATE % (urllib.parse.quote(service),
                                     urllib.parse.quote(self.ticket))
                async with session.get(url) as data:
                    content = await data.text()
                    lines = content.split('\n')
                    if lines[0] == 'yes':
                        self.login = lines[1].lower()
                        self.infos = await LDAP.infos(self.login)
                        self.record()
            if not self.login:
                raise web.HTTPFound(C5_REDIRECT + urllib.parse.quote(service))
        else:
            if self.ticket and self.ticket.isdigit():
                self.login = f'Anon_{self.ticket}'
                self.infos = {'fn': 'fn' + self.ticket, 'sn': 'sn' + self.ticket}
                LDAP.cache[self.login] = self.infos
                self.record()
            else:
                raise web.HTTPFound(
                    service + f'?ticket={int(time.time())}{len(self.session_cache)}')

        return self.login
    def record(self) -> None:
        """Record the ticket for the compile server"""
        with open(f'TICKETS/{self.ticket}', 'w', encoding='utf-8') as file:
            file.write(str(self))
    def __str__(self):
        return repr((self.client_ip, self.browser, self.login, self.creation_time, self.infos))
    def too_old(self) -> bool:
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
    def check(self, request:aiohttp.web_request.Request, client_ip:str,
              browser:str, allow_ip_change:bool=False) -> bool:
        """Returns True if the session is valid.
        Do a redirection if possible (not in compile server)
        """
        if (self.client_ip != client_ip and not allow_ip_change
           ) or self.browser != browser or self.too_old():
            url = getattr(request, 'url', None)
            if url and request.method == 'GET':
                raise web.HTTPFound(str(request.url).split('?', 1)[0])
            return False
        return True

    @classmethod
    def load_ticket_file(cls, ticket:str) -> "Session":
        """Load the ticket from file"""
        with open(f'TICKETS/{ticket}', 'r', encoding='utf-8') as file:
            session = Session(ticket, *eval(file.read())) # pylint: disable=eval-used
        cls.session_cache[ticket] = session
        return session

    @classmethod
    async def get(cls, request:aiohttp.web_request.Request, ticket:Optional[str]=None,
                  allow_ip_change:bool=False) -> Optional["Session"]:
        """Get or create a session.
        Raise an error if hacker.
        """
        assert request.transport
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
        client_ip = (await DNS.infos(client_ip))['name']
        browser = headers.get('user-agent', '')
        if ticket in cls.session_cache:
            session = cls.session_cache[ticket]
            if not session.check(request, client_ip, browser, allow_ip_change=allow_ip_change):
                return None
        elif ticket and os.path.exists(f'TICKETS/{ticket}'):
            session = cls.load_ticket_file(ticket)
            if not session.check(request, client_ip, browser, allow_ip_change=allow_ip_change):
                return None
        else:
            session = Session(ticket, client_ip, browser)
            if ticket:
                cls.session_cache[ticket] = session
        if not session.login:
            await session.get_login(str(request.url).split('?', 1)[0])
        return session

    @classmethod
    async def get_or_fail(cls, request:aiohttp.web_request.Request,
                          ticket:Optional[str]=None, allow_ip_change:bool=False) -> "Session":
        """Send a mixed HTML / Javascript error message"""
        session = await cls.get(request, ticket, allow_ip_change=allow_ip_change)
        if session:
            return session
        message = "Votre session a expiré ou bien vous avez changé d'adresse IP."
        message_js = json.dumps(message)
        raise web.HTTPUnauthorized(body=f"""
    // {message} <!--
    try {{
        window.parent.ccccc.record_not_done({message_js}
            + "\nLa sauvegarde n'a pas pu être faite.\n"
            + "Copiez votre code source ailleurs et rechargez cette page.");
        }}
    catch(err) {{
        window.innerHTML = {message_js};
        }}
    // -->
    """)

    def is_author(self) -> bool:
        """The user is C5 session creator"""
        return CONFIG.is_author(self.login)
    def is_mapper(self) -> bool:
        """The user is C5 building mapper"""
        return CONFIG.is_mapper(self.login)
    def is_admin(self, course:CourseConfig=None) -> bool:
        """The user is C5 admin or course admin"""
        if course and course.is_admin(self.login):
            return True
        return CONFIG.is_admin(self.login)
    def is_course_admin(self, course:CourseConfig) -> bool:
        """The user is course admin"""
        return course.is_admin(self.login)
    def is_grader(self, course:CourseConfig) -> bool:
        """The user is course grader"""
        return course.is_grader(self.login) or CONFIG.is_admin(self.login)
    def is_course_grader(self, course:CourseConfig) -> bool:
        """The user is course grader"""
        return course.is_grader(self.login)
    def is_proctor(self, course:CourseConfig) -> bool:
        """The user is course proctor"""
        return course.is_proctor(self.login) or CONFIG.is_admin(self.login)
    def is_course_proctor(self, course:CourseConfig) -> bool:
        """The user is course proctor"""
        return course.is_proctor(self.login)
    def is_root(self) -> bool:
        """The user is C5 root"""
        return CONFIG.is_root(self.login)
    def is_student(self) -> bool:
        """The user is a student"""
        return CONFIG.is_student(self.login)

    def header(self, courses=(), more='') -> str:
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
            CONFIG = {CONFIG.json};
            </script>
            """

    def message(self, key:str) -> aiohttp.web_response.Response:
        """Error message for the user in a standalone page or a post request"""
        name = self.infos['sn'].upper() + ' ' + self.infos['fn'].title()
        return web.HTTPOk(
            body=f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="/favicon.ico?ticket={self.ticket}">
            </head>
            <h1>{name} : {CONFIG.config['messages'].get(key, key)}</h1>
            """,
            content_type='text/html',
            headers={'Cache-Control': 'no-cache'}
            )
    def exception(self, key:str) -> web.HTTPUnauthorized:
        """Error message for the user in a standalone page or a post request"""
        name = self.infos['sn'].upper() + ' ' + self.infos['fn'].title()
        return web.HTTPUnauthorized(
            body=f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="/favicon.ico?ticket={self.ticket}">
            </head>
            <h1>{name} : {CONFIG.config['messages'].get(key, key)}</h1>
            """,
            content_type='text/html',
            headers={'Cache-Control': 'no-cache'}
            )
def js_message(key:str) -> aiohttp.web_response.Response:
    """Send a pure javascript error message to display on the page"""
    message = json.dumps(CONFIG.config['messages'].get(key, key))
    return web.HTTPOk(
        body=f"document.body.innerHTML = {message}",
        content_type='application/javascript',
        headers={'Cache-Control': 'no-cache'})

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

def print_state() -> None:
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

def print_help() -> None:
    """Print help and default configuration values"""
    print("""Arguments may be:
   * os : configure production OS
   * SSL-LE : create SSL Certificate with Let's Encrypt (NGINX does the encrypting)
              or renew it if it exists.
   * SSL-SS : create a Self Signed certificate (c5 does the encrypting itself)
   * nginx : configure NGINX (needs SSL-LE certificate)
   * c5 : update C5 source (pull)
   * launcher : create 'launcher' (need to be root)
   * start : servers
   * stop : servers
   * restart : servers
   * compile : create JS
   * open : launch web browser (second argument may be js|python|cpp|remote)
   * cp : copy local files to production ones
   * diff : compare local files to production ones
   * getall : copy production course (but not logs) locally
""")
    print_state()
    os.system("ps -fe | grep -e http_server.py -e compile_server.py | grep -v grep")
    print('pkill -f http_server.py ; pkill -f compile_server.py  ; pkill -f infos_server.py ; rm *.log') # pylint: disable=line-too-long
    sys.exit(1)

ACTIONS = {
    'os': """#C5_ROOT
        sudo sh -c '
            set -e
            apt update
            apt -y install astyle nginx certbot python3-websockets python3-ldap python3-aiohttp python3-psutil python3-certbot-nginx npm racket
            apt -y upgrade
            # set-timezone Europe/Paris
            '
        """,
    'launcher': f"""#C5_ROOT
        sudo sh -c '
            set -e
            cd ~{C5_LOGIN}/{C5_DIR}
            make launcher
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
        tar -cf - $(git ls-files | grep -v -e DOCUMENTATION -e BUILDINGS) |
        ssh {C5_LOGIN}@{C5_HOST} 'cd {C5_DIR} ; tar -xvf -'
        """,
    'diff': f"""
        mkdir DIFF
        git ls-files | grep -v DOCUMENTATION >xxx.tocopy
        rsync --files-from=xxx.tocopy '{C5_LOGIN}@{C5_HOST}:{C5_DIR}' DIFF
        for I in $(cat xxx.tocopy)
        do
        diff -u $I DIFF/$I
        done
        rm -rf DIFF
        """,
    'getall': f"""
        rsync --archive --exclude '*/*/**' --exclude '*~' --prune-empty-dirs --verbose '{C5_LOGIN}@{C5_HOST}:{C5_DIR}/COMPILE_*' .
        rsync --archive --verbose '{C5_LOGIN}@{C5_HOST}:{C5_DIR}/BUILDINGS' .
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
server {{
    listen 80;
    server_name {C5_URL};
    rewrite  ^/(.*)$  https://{C5_URL}/$1  permanent;
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
                certbot renew --nginx
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
        xdg-open https://{C5_URL}/{'=' + sys.argv[2] if len(sys.argv) >= 3 else ''}
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

def main() -> None:
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
