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
import html
import copy
import traceback
import urllib.request
import urllib.parse
import asyncio
import aiohttp
from aiohttp import web
import options

def local_ip() -> str:
    """Get the local IP"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return '127.0.0.1'

# To please pylint:
C5_HOST = C5_IP = C5_ROOT = C5_LOGIN = C5_HTTP = C5_SOCK = C5_MAIL = C5_CERT = None
C5_LOCAL = C5_URL = C5_DIR = C5_WEBSOCKET = C5_REDIRECT = C5_VALIDATE = C5_LDAP = None
C5_LDAP_LOGIN = C5_LDAP_PASSWORD = C5_LDAP_BASE = C5_LDAP_ENCODING = None

CONFIGURATIONS = (
    ('C5_HOST'         ,'Production host (for SSH)'            , local_ip()),
    ('C5_IP'           ,'For Socket IP binding'                , local_ip()),
    ('C5_ROOT'         ,'login allowed to sudo'                , 'root'),
    ('C5_LOGIN'        ,'user C5 login'                        , os.getlogin()),
    ('C5_HTTP'         ,'Port number for HTTP'                 , 8000),
    ('C5_SOCK'         ,'Port number for WebSocket'            , 4200),
    ('C5_MAIL'         ,"To create Let's Encrypt certificate"  , lambda: 'root@' + C5_ROOT),
    ('C5_CERT'         ,"SS: C5/SSL directory, NGINX: NGINX"   , 'SS'),
    ('C5_LOCAL'        ,'Run on local host'                    , 1),
    ('C5_URL'          ,'Browser visible address'              , ''),
    ('C5_DIR'          ,'C5 install directory name'            , 'C5'),
    ('C5_WEBSOCKET'    ,'Browser visible address for WebSocket', lambda: f'{C5_HOST}:{C5_SOCK}'),
    ('C5_REDIRECT'     ,'CAS redirection'                      , ''), # https://cas.univ-lyon1.fr/login?service=
    ('C5_VALIDATE'     ,'CAS get login'                        , ''), # https://cas.univ-lyon1.fr/cas/validate?service=%s&ticket=%s
    ('C5_LDAP'         ,'LDAP URL'                             , ''),
    ('C5_LDAP_LOGIN'   ,'LDAP reader login'                    , ''),
    ('C5_LDAP_PASSWORD','LDAP reader password'                 , ''),
    ('C5_LDAP_BASE'    ,'LDAP user search base'                , ''),
    ('C5_LDAP_ENCODING','LDAP character encoding'              , 'utf-8'),
)

def var(name, comment, export='export '):
    """Display a shell affectation with the current variable value"""
    val = globals()[name]
    escaped = str(val).replace("'", "'\"'\"'")
    affectation = f"{export}{name}='{escaped}'"
    return affectation.ljust(50) + " # " + comment

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

    def __init__(self, command, name):
        self.command = command
        self.cache_dir = f'CACHE.{name}/'
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

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
            if '/' not in infos[0]:
                with open(self.cache_dir + infos[0], 'w', encoding='latin1') as file:
                    file.write(json.dumps(infos[1]))

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
        if '/' not in key and os.path.exists(self.cache_dir + key):
            with open(self.cache_dir + key, 'r', encoding='ascii') as file:
                infos = json.loads(file.read())
            self.cache[key] = infos # Will be updated when the answer is received
            return infos
        while key not in self.cache:
            await asyncio.sleep(0.1)
        return self.cache[key]

LDAP = Process('./infos_server.py', 'LDAP')
DNS = Process('./dns_server.py', 'DNS')

def student_log(course_name:str, login:str, data:str) -> None:
    """Add a line to the student log"""
    if not os.path.exists(f'{course_name}/{login}'):
        if not os.path.exists(course_name):
            os.mkdir(course_name)
        os.mkdir(f'{course_name}/{login}')
    with open(f'{course_name}/{login}/http_server.log', "a", encoding='utf-8') as file:
        file.write(data)

def get_buildings() -> Dict[str,str]:
    """Building list"""
    if time.time() - get_buildings.time > 300:
        get_buildings.cache = {}
        for filename in os.listdir('BUILDINGS'):
            with open('BUILDINGS/' + filename, encoding='utf-8') as file:
                get_buildings.cache[filename] = file.read()
    return get_buildings.cache
get_buildings.time = 0

# Active : examination is running
# Inactive & Room=='' : wait access to examination
# Inactive & Room!='' : examination done
# Feedback for the student after the examination (same values than for CourseConfig)
class State(list): # pylint: disable=too-many-instance-attributes
    """State of the student"""
    slots = [ # The order is fundamental: do not change it
        'active', 'teacher', 'room', 'last_time', 'nr_blurs', 'nr_answers',
        'hostname', 'bonus_time', 'grade', 'blur_time', 'feedback']
    slot_index = {key: i for i, key in enumerate(slots)}

    def __setattr__(self, attr, value):
        """Store in the list"""
        self[self.slot_index[attr]] = value

    def __getattr__(self, attr):
        """Get from the list"""
        return self[self.slot_index[attr]]

class CourseConfig: # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """A course session"""
    configs:Dict[str,"CourseConfig"] = {}
    def __init__(self, course):
        if not os.path.exists(course):
            return
        self.course = course.replace('COMPILE_', '').replace('/', '=')
        self.compiler, self.session = self.course.split('=', 1)
        self.file_cf = course + '/session.cf'
        self.file_js = course + '/questions.js'
        self.file_json = course + '/questions.json'
        self.file_py = course + '/questions.py'
        self.dir_log = course + '/LOGS'
        self.dir_media = course + '/MEDIA'
        self.dir_compiler = course.split('/')[0]
        self.dir_session = course
        self.time = 0
        self.parse_position = 0
        try:
            with open(self.file_json, 'r', encoding="ascii") as file:
                self.questions = json.loads(file.read())
        except FileNotFoundError:
            self.questions = []
        self.load()
        self.update()
        self.configs[course] = self
        self.streams = [] # To send changes
        self.to_send = [] # Data to send
        self.send_journal_running = False

    def get_config(self):
        """Config not leaking informations to students"""
        config = dict(self.config)
        del config['notation']
        del config['notationB']
        del config['messages']
        del config['active_teacher_room']
        del config['git_url']
        return config

    def load(self):
        """Load course configuration file"""
        self.config = {'creator': 'nobody',
                       'notation': '',
                       'notationB': '',
                       'notation_max': '?',
                       'messages': [],
                       'active_teacher_room': {},
                      }
        for line in options.DEFAULT_COURSE_OPTIONS: # Defaults
            if len(line) == 3:
                self.config[line[0]] = line[1]
        self.config = copy.deepcopy(self.config) # To be really safe
        self.config['default_building'] = sorted(os.listdir('BUILDINGS'))[0]
        if self.questions:
            self.config.update(self.questions[0]['options']) # Course defaults
        else:
            print('******* No questions in', self.file_py)

        try:
            self.parse()
        except (IOError, FileNotFoundError):
            if os.path.exists(self.file_py):
                self.record_config()
        except SyntaxError:
            print(f"Invalid configuration file: {self.file_cf}", flush=True)
            raise
        # Update old data structure
        if self.config['highlight'] == '0':
            self.config['highlight'] = '#FFF'
        elif self.config['highlight'] == '1':
            self.config['highlight'] = '#0F0'

    def parse(self):
        """Parse the end of the file"""
        if os.path.getsize(self.file_cf) < self.parse_position:
            # The file was rewrote. Read it from scratch
            self.__init__(self.course)
            return

        with open(self.file_cf, 'br') as file:
            self.time = time.time()
            file.seek(self.parse_position)
            config = self.config
            try: # pylint: disable=too-many-nested-blocks
                for binary_line in file:
                    data = eval(binary_line.decode('utf-8')) # pylint: disable=eval-used
                    self.parse_position += len(binary_line) # file.tell() forbiden here
                    if len(data) == 2:
                        if data[1] in ('0', '1', True, False):
                            config[data[0]]  = int(data[1]) # XXX To read old files (to remove)
                        else:
                            config[data[0]] = data[1]
                    elif len(data) == 3:
                        if data[0] == 'active_teacher_room':
                            state = data[2]
                            if len(state) <= 10:
                                if len(state) <= 9:
                                    if len(state) <= 8:
                                        if len(state) <= 7:
                                            state.append(0) # Bonus time
                                        state.append('') # Grade
                                    state.append(0) # Blur time
                                state.append(1) # Feedback default: Student work
                            config[data[0]][data[1]] = State(state)
                        else:
                            config[data[0]][data[1]] = data[2]
                    else:
                        config[data[0]][data[1]][data[2]] = data[3]
            # except (KeyError, IndexError):
            #     # Rewrite configuration with the new format
            #     config.update(data)
            #     self.record_config()
            except: # pylint: disable=bare-except
                print('Filename:', self.file_cf)
                print('Line:', binary_line, flush=True)
                traceback.print_exc()

    def record_config(self):
        """Record the default start configuration"""
        with open(self.file_cf, 'w', encoding='utf-8') as file:
            for key, value in self.config.items():
                if isinstance(value, dict):
                    for key2, value2 in value.items():
                        file.write(repr((key, key2, value2)) + '\n')
                else:
                    file.write(repr((key, value)) + '\n')
        self.parse_position = os.path.getsize(self.file_cf)
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
        self.notationB = self.config['notationB']
        self.theme = self.config['theme']
        self.active_teacher_room = self.config['active_teacher_room']
        self.messages = self.config['messages']
        self.state = self.config['state']
        self.feedback = self.config['feedback']
        self.expected_students = set(re.split('[ \n\r\t]+', self.config['expected_students']))
        self.expected_students_required = int(self.config['expected_students_required'])
        if os.path.exists(self.dir_media):
            self.media = os.listdir(self.dir_media)
        else:
            self.media = []

    def number_of_active_students(self, last_seconds:int=600) -> int:
        """Compute the number of active students the last seconds"""
        nb_active = 0
        now = time.time()
        for info in self.active_teacher_room.values():
            if now - info.last_time < last_seconds:
                nb_active += 1
        return nb_active

    def set_parameter(self, parameter:str, value:Any, key:str=None, index:int=None):
        """Set one of the parameters"""
        if key:
            if index is None:
                if self.config[parameter].get(key, None) == value:
                    return
                self.config[parameter][key] = value
            else:
                if self.config[parameter][key][index] == value:
                    return
                self.config[parameter][key][index] = value
        else:
            if self.config[parameter] == value:
                return
            self.config[parameter] = value
            self.update() # Only update for top config changes
        with open(self.file_cf, 'a', encoding='utf-8') as file:
            timestamp = f' # {time.strftime("%Y-%m-%d %H:%M:%S")}\n'
            if key:
                if index is None:
                    file.write(f'{(parameter, key, value)}{timestamp}')
                else:
                    file.write(f'{(parameter, key, index, value)}\n')
            else:
                file.write(f'{(parameter, value)}{timestamp}')
        self.time = time.time()
        self.to_send.append((parameter, value, key, index))
        if not self.send_journal_running:
            self.send_journal_running = True
            asyncio.ensure_future(self.send_journal())
    async def send_journal(self):
        """Send the changes to all listening browsers"""
        while self.to_send:
            data = self.to_send.pop(0)
            if data[0] == 'active_teacher_room' and data[3] is None: # New student
                self.to_send.append(('infos', data[2], await LDAP.infos(data[2])))
            data = (json.dumps(data) + '\n').encode('utf-8')
            for stream in tuple(self.streams):
                try:
                    await stream.write(data)
                    await stream.drain()
                except: # pylint: disable=bare-except
                    self.streams.remove(stream)
        self.send_journal_running = False
    def get_stop(self, login:str) -> int:
        """Get stop date, taking login into account"""
        if login in self.active_teacher_room:
            bonus_time = self.active_teacher_room[login].bonus_time
        else:
            bonus_time = 0
        if login in self.tt_list:
            return self.stop_tt_timestamp + bonus_time
        return self.stop_timestamp + bonus_time
    def update_checkpoint(self, login:str, hostname:Optional[str], now:int) -> Optional[Tuple]:
        """Update active_teacher_room"""
        if not login:
            return None
        active_teacher_room = self.active_teacher_room.get(login, None)
        if active_teacher_room is None:
            if not hostname:
                # There is an http_server.log but nothing in session.cf
                hostname = 'broken_cf_file'
            if self.checkpoint:
                place = ''
            else:
                place = CONFIG.host_to_place.get(hostname, '')
            # Add to the checkpoint room
            active_teacher_room = State((0, '', place, now, 0, 0, hostname, 0, '', 0, 1))
            self.set_parameter('active_teacher_room', active_teacher_room, login)
            to_log = [now, ["checkpoint_in", hostname]]
        elif hostname and hostname != active_teacher_room.hostname:
            # Student IP changed
            if self.checkpoint and not self.allow_ip_change:
                # Undo checkpointing
                self.set_parameter('active_teacher_room', hostname, login, 6)
                self.set_parameter('active_teacher_room', 0, login, 0)
                to_log = [now, ["checkpoint_ip_change_eject", hostname]]
            else:
                # No checkpoint: so allows the room change
                self.set_parameter('active_teacher_room', hostname, login, 6)
                self.set_parameter('active_teacher_room', CONFIG.host_to_place.get(hostname, ''), login, 2)
                to_log = [now, ["checkpoint_ip_change", hostname]]
        else:
            to_log = None
        if to_log:
            student_log(self.dir_log, login, json.dumps(to_log) + '\n')
        return active_teacher_room

    def status(self, login:str, hostname:str=None) -> str: # pylint: disable=too-many-return-statements,too-many-statements,too-many-branches
        """Status of the course"""
        try:
            if os.path.getmtime(self.file_cf) > self.time:
                self.parse() # Load only the file end
                self.update()
        except FileNotFoundError:
            pass
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
        if hostname:
            active_teacher_room = self.update_checkpoint(login, hostname, now)
            if not active_teacher_room:
                raise ValueError('Bug')
            if self.checkpoint and not active_teacher_room.active:
                if active_teacher_room.teacher == '':
                    # Always in the checkpoint or examination is done
                    return 'checkpoint'
                return 'done'
        if now < self.start_timestamp:
            return 'pending'
        if now < self.get_stop(login):
            return 'running'
        if self.checkpoint:
            active_teacher_room = self.active_teacher_room.get(login, None)
            if not active_teacher_room or active_teacher_room.teacher == '':
                return 'checkpoint' # Always in the checkpoint after examination start
        return 'done'

    def get_feedback(self, login:str) -> int:
        """Return the feedback level"""
        active_teacher_room = self.active_teacher_room.get(login, None)
        if not active_teacher_room:
            return 0
        if self.status(login) != 'done':
            return 0
        if self.state != 'Done':
            return 0
        return min(self.feedback, active_teacher_room.feedback)

    def get_notation(self, login:str) -> str:
        """Return the notation for the student"""
        version = self.active_teacher_room.get(login)[2].split(',')
        if len(version) < 3:
            return self.notation
        version = version[3]
        if version == 'b' and self.notationB:
            return self.notationB
        return self.notation

    def get_comments(self, login:str) -> str:
        """Get the comments"""
        comment_file = f'{self.dir_log}/{login}/comments.log'
        if os.path.exists(comment_file):
            with open(comment_file, "r", encoding='utf-8') as file:
                return file.read()
        return ''
    def append_comment(self, login:str, comment:List) -> None:
        """Append a comment to the file"""
        comment_file = f'{self.dir_log}/{login}/comments.log'
        with open(comment_file, "a", encoding='utf-8') as file:
            file.write(json.dumps(comment) + '\n')

    def get_grades(self, login:str) -> str:
        """Get the grades"""
        grade_file = f'{self.dir_log}/{login}/grades.log'
        if os.path.exists(grade_file):
            with open(grade_file, "r", encoding='utf-8') as file:
                return file.read()
        return ''
    def append_grade(self, login:str, grade:List) -> str:
        """Append a grade to the file"""
        grade_file = f'{self.dir_log}/{login}/grades.log'
        with open(grade_file, "a", encoding='utf-8') as file:
            file.write(json.dumps(grade) + '\n')
        grades = self.get_grades(login)
        grading = {}
        for line in grades.split('\n'):
            if line:
                line = json.loads(line)
                if line[3]:
                    grading[line[2]] = float(line[3])
                else:
                    grading.pop(line[2], None)
        new_value = [sum(grading.values()), len(grading)]
        self.set_parameter('active_teacher_room', new_value, login, 8)
        return grades

    def running(self, login:str, hostname:str=None) -> bool:
        """If the session running for the user"""
        return self.status(login, hostname).startswith('running') or not CONFIG.is_student(login)

    async def get_students(self) -> List[List[Any]]:
        """Get all the students"""
        # Clearly not efficient
        students = []
        for student, active_teacher_room in self.active_teacher_room.items():
            if C5_VALIDATE:
                infos = await LDAP.infos(student)
            else:
                infos = {'fn': 'FN' + student, 'sn': 'SN'+student}
            students.append([student, active_teacher_room, infos])
        return students

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
        # Update file layout
        for course in sorted(glob.glob('COMPILE_*/*.py')):
            course = course[:-3]
            session = course.split('/')[1]
            tmp = 'XXX-' + session + '/'
            os.mkdir(tmp)
            for extension, name in (
                ('.cf', 'session.cf'),
                ('.py', 'questions.py'),
                ('.js', 'questions.js'),
                ('.json', 'questions.json'),
                ('', 'LOGS'),
            ):
                if os.path.exists(course + extension):
                    os.rename(course + extension, tmp + name)
            for media in glob.glob(course + '-*'):
                if not os.path.exists(tmp + 'MEDIA'):
                    os.mkdir(tmp + '/MEDIA')
                os.rename(media, tmp + 'MEDIA/' + media.split('-')[-1])
            os.rename(tmp, course)

        # Load configs
        for course in sorted(glob.glob('COMPILE_*/*')):
            cls.get(course)

    def is_admin(self, login:str) -> bool:
        """Is admin or creator"""
        return login in self.admins or login == self.creator or CONFIG.is_admin(login)

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
    if course.endswith('.zip'):
        course = course[:-4]
    return f'COMPILE_{compilator}/{course}'

class Config: # pylint: disable=too-many-instance-attributes
    """C5 configuration"""
    authors:List[str] = []
    masters:List[str] = []
    mappers:List[str] = []
    roots:List[str] = []
    ticket_ttl = 86400
    computers:List[Tuple[str, int, int, str, int]] = []
    host_to_place:Dict[str,str] = {} # hostname → building,x,y,a/b
    json = ''
    def __init__(self):
        self.config = {
            'roots': self.roots,
            'masters': self.masters,
            'authors': self.authors,
            'mappers': self.mappers,
            'ticket_ttl': self.ticket_ttl,
            'computers': [],
            'ips_per_room': {"Nautibus,TP3": "b710l0301.univ-lyon1.fr,20,10 b710l0302.univ-lyon1.fr,22,10"},
            'student': '[0-9][0-9]$',
            'messages': {
                'unknown': "Cette session n'existe pas",
                'checkpoint':
                    "Demandez à votre intervenant de vous dire quand il vous aura "
                    "ouvert l'examen puis rechargez cette page.",
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
        self.json = json.dumps(self.config)
        for room, hosts in self.config['ips_per_room'].items():
            building = room.split(',')[0]
            buildings = get_buildings()
            if building not in buildings:
                print(f"{building} from 'ips_per_room' not in BUILDINGS directory")
                continue
            map_rows = buildings[building].split('\n')
            for host in re.split(' +', hosts):
                host, pos_x, pos_y = (host + ',,').split(',')[:3]
                if pos_y:
                    pos_x = int(pos_x)
                    pos_y = int(pos_y)
                    subject = 'a'
                    if (pos_y < len(map_rows)
                        and pos_x < len(map_rows[pos_y])
                        and map_rows[pos_y][pos_x] == 'b'):
                        subject = 'b'
                    self.host_to_place[host] = f'{building},{pos_x},{pos_y},{subject}'
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
    def __init__(self, ticket, client_ip, browser, # pylint: disable=too-many-arguments
                 login=None, creation_time=None, infos=None, hostname=None):
        self.ticket = ticket
        self.client_ip = client_ip
        self.hostname = hostname
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
        self.hostname = (await DNS.infos(self.client_ip))['name']
        return self.login
    def record(self) -> None:
        """Record the ticket for the compile server"""
        with open(f'TICKETS/{self.ticket}', 'w', encoding='utf-8') as file:
            file.write(str(self))
    def __str__(self):
        return repr((self.client_ip, self.browser, self.login, self.creation_time,
                     self.infos, self.hostname))
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
            + "<br>\nLa sauvegarde n'a pas pu être faite.\n"
            + "<br>Copiez votre code source ailleurs et rechargez cette page.");
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
    def is_proctor(self, course:CourseConfig) -> bool:
        """The user is course proctor"""
        return course.is_proctor(self.login) or CONFIG.is_admin(self.login)
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

    def message(self, key:str, start_time=0) -> aiohttp.web_response.Response:
        """Error message for the user in a standalone page or a post request"""
        name = self.infos['sn'].upper() + ' ' + self.infos['fn'].title()
        if start_time:
            more = f'''
            <p>Début dans <span id="start"></span> secondes
            <script>
            START = {start_time} + Math.random() * 3;
            function display() {{
                var diff = START - (new Date()).getTime() / 1000;
                if (diff <= 0 )
                    window.location.reload();
                else
                    document.getElementById('start').innerHTML = 5 * Math.ceil(diff/5);
            }}
            setInterval(display, 5000);
            display();
            </script>

            '''
        else:
            more = ''
        return web.HTTPOk(
            body=f"""<!DOCTYPE html>
            <html>
            <head>
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="/favicon.ico?ticket={self.ticket}">
            </head>
            <h1>{name} : {CONFIG.config['messages'].get(key, key)}</h1>
            {more}
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

def init_globals():
    """Initialise global variables of this module from shell variables"""
    for name, _comment, default in CONFIGURATIONS:
        if not isinstance(default, (int, str)):
            default = default()
        value = os.getenv(name, default)
        if isinstance(default, int):
            value = int(value)
        globals()[name] = value

init_globals()

def print_state() -> None:
    """Print the current configuration"""
    print("Uses environment shell variables :")
    for name, comment, _default in CONFIGURATIONS:
        print(var(name, comment, export=''))

def create_start_script():
    """Create the start script on the distant host"""
    with open('xxx-start-c5', 'w', encoding='utf-8') as file:
        file.write('#!/bin/sh\n')
        file.write('# Starts C5 with configuration\n')
        file.write(''.join(var(name, comment).replace("LOCAL='0'", "LOCAL='1'") + '\n'
                           for name, comment, _default in CONFIGURATIONS))
        file.write('./utilities.py start\n')
    os.chmod('xxx-start-c5', 0o755)

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
   * restart_compile_server : only compile_server.py
   * compile : create JS
   * create_start_script : create 'xxx-start-c5' on server
   * open : launch web browser (second argument may be js|python|cpp|remote)
   * cp : copy local files to production ones
   * diff : compare local files to production ones
   * getall : copy production course (but not logs) locally
   * cleanup_session_cf : removes any modification history from 'session.cf' files
                          to do between semesters to speedup C5 startup time.
""")
    print_state()
    os.system("ps -fe | grep -e http_server.py -e compile_server.py -e dns_server.py -e infos_server.py | grep -v grep")
    print('for I in http compile infos dns; do pkill -f "$I"_server.py ; done ; rm *.log')
    sys.exit(1)

ACTIONS = {
    'os': """#C5_ROOT
        sudo sh -c '
            set -e
            apt update
            apt -y install astyle nginx certbot python3-websockets python3-ldap python3-aiohttp python3-psutil python3-certbot-nginx npm racket zip
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
        ssh {C5_LOGIN}@{C5_HOST} 'cd {C5_DIR} ; tar -xvf - ; touch *.py'
        """,
    'diff': f"""
        mkdir DIFF
        git ls-files | grep -v -e DOCUMENTATION -e BUILDINGS >xxx.tocopy
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
    'restart_compile_server': fr"""#C5_LOGIN
        set -e
        echo RESTART compile_server
        cd {C5_DIR} 2>/dev/null || true
        pkill --oldest -f compile_server.py || true
        ./compile_server.py >>compile_server.log 2>&1 &
        tail -f compile_server.log
        """,
    'start': fr"""#C5_LOGIN
        set -e
        echo START SERVERS
        cd {C5_DIR} 2>/dev/null || true
        chmod 700 . # No access for students
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
    'stop': r"""#C5_LOGIN
        echo STOP SERVERS
        for I in http_server compile_server infos_server dns_server
        do
            pkill --oldest -f python3\ ./\$I
        done
        """,
    'open': f"""
        xdg-open https://{C5_URL}/{'=' + sys.argv[2] if len(sys.argv) >= 3 else ''}
        """,
    'load': "./load_testing.py",
    'compile': fr"""#C5_LOGIN
        echo START SERVERS
        cd {C5_DIR} 2>/dev/null || true
        mkdir TICKETS 2>/dev/null || true
        make prepare
        """,
    'create_start_script': fr"""#C5_LOGIN
        echo CREATES START SCRIPT 'xxx-start-c5'
        cd {C5_DIR}
        ./utilities.py __create_start_script__
        """,
    'cleanup_session_cf': fr"""#C5_LOGIN
        echo 'CLEAN UP SESSION CF (remove history)'
        cd {C5_DIR}
        ./utilities.py __cleanup_session_cf__
        """,
    'create_stats': fr"""#C5_LOGIN
        echo CREATES STATS
        cd {C5_DIR}
        ./utilities.py __create_stats__
        """,
}
ACTIONS['restart'] = ACTIONS['compile'] + '\n' + ACTIONS['stop'] + 'sleep 1\n' + ACTIONS['start']

def main() -> None:
    """MAIN"""
    if '__create_start_script__' in sys.argv:
        create_start_script()
        return
    if '__cleanup_session_cf__' in sys.argv:
        CourseConfig.load_all_configs()
        for course in CourseConfig.configs.values():
            try:
                os.rename(course.file_cf, course.file_cf + '~')
                course.record_config()
                CourseConfig(course.dir_session)
                print('CLEANED ', course.file_cf,
                    os.path.getsize(course.file_cf + '~') // 1024, 'KB →',
                    os.path.getsize(course.file_cf) // 1024, 'KB')
            except: # pylint: disable=bare-except
                # Revert changes
                print('BUG ', course.file_cf)
                os.rename(course.file_cf + '~', course.file_cf)
        return
    if '__create_stats__' in sys.argv:
        import create_stats
        CourseConfig.load_all_configs()
        create_stats.compile_stats(CourseConfig.configs)
        return

    if 'options.html' in sys.argv:
        print('<table>')
        for line in options.DEFAULT_COURSE_OPTIONS:
            if len(line) == 3:
                if isinstance(line[1], str):
                    value = '<tt>' + html.escape(repr(line[1])) + '</tt>'
                elif isinstance(line[1], list):
                    value = '<pre>[\n' + ''.join(f'  {html.escape(repr(i))},\n'
                                            for i in line[1]) + ']</pre>'
                elif isinstance(line[1], dict):
                    value = '<pre>{\n' + ''.join(f'  {repr(key)}: {html.escape(repr(val))},\n'
                                            for key, val in line[1].items()) + '}</pre>'
                else:
                    value = repr(line[1])
                print(f'<tr><td>{line[0]}<td>{value}<td>{line[2]}</tr>')
            else:
                print(f'<tr><th style="background: #FFF" colspan="3">{html.escape(line)}</tr>')
        print('</table>')
        return
    if len(sys.argv) < 2 or sys.argv[1] not in ACTIONS:
        print_help()
    action = sys.argv[1]
    if action != 'open':
        print(f"{' '.join(sys.argv)}")
        print_state()
    action = ''.join(var(name, comment) + '\n'
                       for name, comment, _default in CONFIGURATIONS) + ACTIONS[action]
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

if aiohttp.__version__ < '3.8':
    HTTPUnauthorizedOriginal = web.HTTPUnauthorized
    def HTTPUnauthorizedFixed(*args, **kargs):
        kargs['body'] = kargs['body'].encode('utf-8')
        return HTTPUnauthorizedOriginal(*args, **kargs)
    web.HTTPUnauthorized = HTTPUnauthorizedFixed

if __name__ == "__main__":
    main()
