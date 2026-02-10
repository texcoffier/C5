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
import ssl
import time
import glob
import atexit
import copy
import traceback
import random
import urllib.request
import urllib.parse
import asyncio
import aiohttp
from aiohttp import web
import options
import common
from c5 import init_globals
import xxx_local

C5_IP = C5_SOCK = C5_COMPILE_UID = None

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

def set_of_logins(txt):
    return set(xxx_local.normalize_login(login)
               for login in re.split('[ \n\r\t]+', txt))

class Process: # pylint: disable=invalid-name
    """Create a LDAP or DNS process and get information from it.
    It is more simple than using an asyncio LDAP library.
    """
    cache:Dict[Any,Any] = {}
    started:Optional[bool] = None

    def __init__(self, command, name):
        self.command = command
        self.cache_dir = f'CACHE.{name}/'
        if not os.path.exists(self.cache_dir):
            os.mkdir(self.cache_dir)

    if False:
        def log(self, _txt):
            return
    else:
        log_file = open(time.strftime('LOGS/%Y%m%d-process-')
                        + sys.argv[0].split('/')[-1], 'a', encoding='utf-8')
        def log(self, txt):
            self.log_file.write(f'{time.strftime("%Y%m%d-%H%M%S")} {txt}\n')

    async def start(self) -> None:
        """
        Start a process reading login on stdin and write information on stdout
        """
        self.process = await asyncio.create_subprocess_shell( # pylint: disable=attribute-defined-outside-init
            "exec python3 " + self.command,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            )
        asyncio.ensure_future(self.reader())
        atexit.register(self.process.kill)
        self.log(f'Start {self.process} {self.command}')

    async def reader(self) -> None:
        """Parse infos from process"""
        if not self.process.stdout:
            raise ValueError('Bug')
        self.log(f'Start reader {self.process}')
        while True:
            infos = await self.process.stdout.readline()
            self.log(f'Read {infos}')
            if not infos:
                print('FAIL READ', self.process, self.process.stdout, flush=True)
                return
            infos = json.loads(infos)
            self.log('Write in memory cache')
            self.cache[infos[0]] = infos[1]
            if '/' not in infos[0]:
                self.log('Write on disc cache')
                with open(self.cache_dir + infos[0], 'w', encoding='latin1') as file:
                    file.write(json.dumps(infos[1]))
            self.log('Done')

    async def infos(self, key:str) -> Dict[str, str]:
        """Get the informations about key"""
        self.log(f'Ask about «{key}»')
        if not self.started:
            if self.started is None:
                self.log('Start')
                self.started = False
                await self.start()
                self.started = True
            else:
                self.log('Start wait')
                while not hasattr(self, "process"):
                    await asyncio.sleep(0.1)
            self.log('Started')
        if not self.process.stdin:
            raise ValueError('Bug')
        if key not in self.cache:
            # Get data from cache file if it is possible
            self.log('Not in memory cache')
            if '/' not in key and os.path.exists(self.cache_dir + key):
                with open(self.cache_dir + key, 'r', encoding='ascii') as file:
                    self.cache[key] = json.loads(file.read())
                self.log(f'Read from disc cache: {self.cache[key]}')
            else:
                self.log('Not in disc cache')
        if key not in self.cache or time.time() > self.cache[key].get('time', 0) + 86400:
            # Ask to update the cache
            self.log('Ask for cache creating or updating')
            self.process.stdin.write(key.encode('utf-8') + b'\n')
        while key not in self.cache:
            await asyncio.sleep(0.1) # Wait the reader task
        self.log(f'Answer about «{key}»: {self.cache[key]}')
        return self.cache[key]

LDAP = Process('infos_server.py', 'LDAP')
DNS = Process('dns_server.py', 'DNS')

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

DEFAULT_STATE = (
    0,         # Active
    '',        # Teacher login
    '',        # Building,Column,Line,Version
    0,         # Last interaction
    0,         # Number of blurs
    0,         # Number of good questions
    '',        # Last hostname used
    0,         # Bonus time in seconds
    '',        # Grade
    0,         # Blur time in seconds
    1,         # Feedback level (source, comments, grades...)
    0,         # Not fullscreen allowed
    '',        # Remarks
    )


class State(list): # pylint: disable=too-many-instance-attributes
    """State of the student"""
    slots = [ # The order is fundamental: do not change it
        'active', 'teacher', 'room', 'last_time', 'nr_blurs', 'nr_answers',
        'hostname', 'bonus_time', 'grade', 'blur_time', 'feedback', 'fullscreen',
        'remarks']
    slot_index = {key: i for i, key in enumerate(slots)}

    def complete(self):
        self.extend(DEFAULT_STATE[len(self):])
        return self

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
        self.file_config = course + '/session.json'
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
        self.doing_grading = {}
        # Add the API key stats if there is none:
        if not self.config['key_stats']:
            self.set_parameter('key_stats', f'{random.randrange(1 << 63, 1 << 64):x}')

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
                       'source_update': '',
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

        if (os.path.exists(self.file_config) and os.path.exists(self.file_py)
                and os.path.getmtime(self.file_config) >= os.path.getmtime(self.file_cf)):
            with open(self.file_config, 'r', encoding='utf-8') as file:
                content = file.read()
            self.config = json.loads(content)
            self.parse_position = len(content)
            self.file_config_need_update = False
            self.time = time.time()
            active_teacher_room = self.config['active_teacher_room']
            for login, state in active_teacher_room.items():
                active_teacher_room[login] = State(state).complete()
        else:
            self.file_config_need_update = True
            try:
                self.parse()
            except (IOError, FileNotFoundError):
                if os.path.exists(self.file_py):
                    self.record_config()
            except (SyntaxError, KeyError):
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
                    line = binary_line.decode('utf-8')
                    line_len = len(line)
                    self.parse_position += line_len # file.tell() forbiden here
                    if line_len <= 1:
                        continue
                    data = eval(line) # pylint: disable=eval-used
                    if len(data) == 2:
                        if data[1] in ('0', '1', True, False):
                            config[data[0]]  = int(data[1]) # XXX To read old files (to remove)
                        else:
                            config[data[0]] = data[1]
                    elif len(data) == 3:
                        if data[0] == 'active_teacher_room':
                            config[data[0]][data[1]] = State(data[2]).complete()
                        else:
                            if data[1] == '+':
                                config[data[0]].append(data[2])
                            else:
                                config[data[0]][data[1]] = data[2]
                    else:
                        config[data[0]][data[1]][data[2]] = data[3]
            # except (KeyError, IndexError):
            #     # Rewrite configuration with the new format
            #     config.update(data)
            #     self.record_config()
            except: # pylint: disable=bare-except
                try:
                    # Parse from start
                    self.__init__(self.dir_session)
                except:
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
        self.file_config_need_update = True

    def create_config(self, what):
        """Return the config filtered by what
              * option name
              * Placement
           No history recorded.
        """
        lines = []
        for key in tuple(what):
            if key in self.config:
                if key == 'active_teacher_room':
                    for login, value in self.config[key].items():
                        lines.append(repr(('active_teacher_room', login, value)))
                elif key == 'messages':
                    for message in self.config[key]:
                        lines.append(repr(('messages', '+', message)))
                else:
                    lines.append(repr((key, self.config[key])))
                what.remove(key)
        return '\n'.join(lines) + '\n'

    def update(self) -> None:
        """Compute some values"""
        self.start = self.config['start']
        self.start_timestamp = time.mktime(time.strptime(self.start, '%Y-%m-%d %H:%M:%S'))
        self.stop = self.config['stop']
        self.stop_timestamp = time.mktime(time.strptime(self.stop, '%Y-%m-%d %H:%M:%S'))
        self.tt_list = set_of_logins(self.config['tt'])
        self.tt_list.add('')
        if 'teachers' in self.config:
            teachers = re.split('[ \n\r\t]+', self.config['teachers'])
            self.config['creator'] = teachers[0]
            self.config['graders'] = ' '.join(teachers[1:])
            del self.config['teachers']
        self.creator = self.config['creator']
        self.admins = set_of_logins(self.config['admins'])
        self.graders = set_of_logins(self.config['graders'])
        self.proctors = set_of_logins(self.config['proctors'])
        self.checkpoint = int(self.config['checkpoint'])
        self.sequential = int(self.config['sequential'])
        self.highlight = self.config['highlight']
        self.allow_ip_change = int(self.config['allow_ip_change'])
        self.notation = self.config['notation']
        self.notation_parsed = common.Grades(self.notation)
        self.notationB = self.config['notationB']
        self.notationB_parsed = common.Grades(self.notationB)
        self.theme = self.config['theme']
        self.active_teacher_room = self.config['active_teacher_room']
        self.messages = self.config['messages']
        self.state = self.config['state']
        self.feedback = self.config['feedback']
        self.force_grading_done = int(self.config['force_grading_done'])
        self.feedback_for_all = int(self.config['feedback_for_all'])
        self.expected_students = set_of_logins(self.config['expected_students'])
        if tuple(self.expected_students) == ('',):
            self.expected_students = set()
        if os.path.exists(self.dir_media):
            self.media = os.listdir(self.dir_media)
        else:
            self.media = []
        self.hide_before_seconds = self.start_timestamp - 3600 * self.config['hide_before']
        self.title = self.config['title']

    def number_of_active_students(self, last_seconds:int=600) -> int:
        """Compute the number of active students the last seconds"""
        nb_active = 0
        now = time.time()
        for info in self.active_teacher_room.values():
            if now - info.last_time < last_seconds:
                nb_active += 1
        return nb_active

    def create_file_config(self):
        """Create the load accelerator"""
        with open(self.file_config, 'w', encoding='utf-8') as file:
            file.write(json.dumps(self.config, default=lambda x: list(x)))
        self.file_config_need_update = False

    def set_parameter(self, parameter:str, value:Any, key:str=None, index:int=None, who:str=''):
        """Set one of the parameters"""
        if not self.file_config_need_update:
            self.file_config_need_update = True
        if key:
            if key == '+':
                self.config[parameter].append(value)
            elif index is None:
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
            timestamp = f' # {time.strftime("%Y-%m-%d %H:%M:%S")}'
            if who:
                timestamp += ' ' + who
            if key:
                if index is None:
                    file.write(f'{(parameter, key, value)}{timestamp}\n')
                else:
                    file.write(f'{(parameter, key, index, value)}\n')
            else:
                file.write(f'{(parameter, value)}{timestamp}\n')
        self.time = time.time()
        self.to_send.append((parameter, value, key, index))
        if not self.send_journal_running:
            self.send_journal_running = True
            asyncio.ensure_future(self.send_journal())
    def set_active_teacher_room(self, student:str, key:str, value:Any):
        self.set_parameter('active_teacher_room', value, student, State.slot_index[key])
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
            bonus_time += (self.stop_timestamp - self.start_timestamp) / 3
        return self.stop_timestamp + bonus_time
    def update_checkpoint(self, login:str, hostname:Optional[str], now:int) -> Optional[State]:
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
            active_teacher_room = State((0, '', place, now, 0, 0, hostname)).complete()
            self.set_parameter('active_teacher_room', active_teacher_room, login)
        elif hostname and hostname != active_teacher_room.hostname:
            # Student IP changed
            self.set_active_teacher_room(login, 'hostname', hostname)
            if self.checkpoint and not self.allow_ip_change:
                # Undo checkpointing
                self.set_active_teacher_room(login, 'active', 0)
            else:
                if not self.checkpoint:
                    # Automaticaly place if no checkpoint
                    self.set_active_teacher_room(login, 'room', CONFIG.host_to_place.get(hostname, ''))
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
            active_teacher_room = self.active_teacher_room.get(login, None)
            if not active_teacher_room:
                return 'nothing'
            if self.checkpoint and active_teacher_room.teacher == '':
                # Not placed
                return 'checkpoint'
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
        if not active_teacher_room and not self.feedback_for_all:
            return 0
        if self.status(login) != 'done':
            return 0
        if self.state != 'Done':
            return 0
        if self.force_grading_done or not active_teacher_room:
            return self.feedback
        return min(self.feedback, active_teacher_room.feedback)

    def get_version(self, login:str) -> str:
        """Return the version for the student"""
        active_teacher_room = self.active_teacher_room.get(login)
        if active_teacher_room:
            version = active_teacher_room[2].split(',')
        else:
            return 'a'
        if len(version) < 3:
            return 'a'
        version = version[3]
        if version == 'b' and self.notationB:
            return 'b'
        return 'a'
    def get_notation(self, login:str) -> str:
        """Return the notation for the student"""
        if self.get_version(login) == 'a':
            return self.notation
        return self.notationB
    def get_notation_parsed(self, login:str) -> str:
        """Return the notation for the student"""
        if self.get_version(login) == 'a':
            return self.notation_parsed
        return self.notationB_parsed

    def get_comments(self, login:str) -> str:
        """Get the comments DEPRECATED"""
        comment_file = f'{self.dir_log}/{login}/comments.log'
        if os.path.exists(comment_file):
            with open(comment_file, "r", encoding='utf-8') as file:
                return file.read()
        return ''
    def append_comment(self, login:str, comment:List) -> None:
        """Append a comment to the file DEPRECATED"""
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
        grading = common.parse_grading(grades, fast=True)
        notation = self.get_notation_parsed(login)
        values = []
        for grade in notation.grades:
            value = grading.get(grade.key, None)
            if value is not None:
                values.append(float(value))
        competences = []
        for grade in notation.competences:
            value = grading.get(grade.key, None)
            if value is not None and value != '?':
                competences.append(float(value))
        new_value = [sum(values), len(values),
                     sum(competences)/len(competences) if competences else 0, len(competences)]
        self.set_active_teacher_room(login, 'grade', new_value)
        return grades

    def running(self, login:str, hostname:str=None) -> bool:
        """If the session running for the user"""
        return self.status(login, hostname).startswith('running') or not CONFIG.is_student(login) or self.is_grader(login)

    async def get_students(self) -> List[List[Any]]:
        """Get all the students"""
        # Clearly not efficient
        students = []
        for student, active_teacher_room in self.active_teacher_room.items():
            infos = await LDAP.infos(student)
            students.append([student, active_teacher_room, infos])
        return students

    @classmethod
    def get(cls, course:str) -> "CourseConfig":
        """Get a config from cache"""
        config = cls.configs.get(course, None)
        if config:
            return config
        config = CourseConfig(course)
        if not getattr(config, 'time', 0):
            # No file with this name
            cls.configs.pop(course, None)
            raise ValueError("Session inconnue : " + course)
        if not re.match('.*{[^:}{]+:([?],)?[-.,0-9]*}', config.notation, flags=re.S):
            return config
        try:
            print("REWRITE GRADES", course, flush=True)
            renames = []
            notations = []
            for notation in (config.notation, config.notationB):
                translate = {}
                grades = common.Grades(notation)
                notations.append(grades)
                for i, grade in enumerate(grades.content[:-1]):
                    if grade.key_original:
                        translate[str(i)] = str(grade.key)
                    else:
                        translate[str(i)] = str(i)
                renames.append(translate)
            for login, state in config.active_teacher_room.items():
                grades = config.get_grades(login)
                if not grades:
                    continue
                grade_file = f'{config.dir_log}/{login}/grades.log'
                print(f'Translate «{grade_file}»: ', end='')
                if state.room.count(',') < 3:
                    translate = renames[0]
                    print('no version, assume «a» ', end='')
                elif state.room.split(',')[3] == 'a': # Check subject version
                    translate = renames[0]
                else:
                    translate = renames[1]
                old = [json.loads(line) for line in grades.strip().split('\n')]
                new = []
                for line in old:
                    line = list(line)
                    # Use 'get' because the translations may yet has been done
                    line[2] = translate.get(line[2], line[2])
                    new.append(line)
                if old == new:
                    print('no change', flush=True)
                else:
                    with open(grade_file, "w", encoding='utf-8') as file:
                        for line in new:
                            file.write(json.dumps(line) + '\n')
                    print('done', flush=True)
            # Update configuration only if the translation was successful
            print("Update session configuration: ", end='', flush=True)
            if config.notation:
                config.set_parameter('notation', notations[0].with_keys())
            if config.notationB:
                config.set_parameter('notationB', notations[1].with_keys())
            print("done", flush=True)
            return config
        except: # pylint: disable=bare-except
            print('Grade translation failure')
            import traceback
            traceback.print_exc()
            sys.exit(1)

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
            try:
                if os.path.isdir(course):
                    yield cls.get(course)
            except ValueError as err:
                print(err)
    @classmethod
    def courses_matching(cls, course, session=None):
        """Returns instances with name matching 'course' regexp."""
        return [
            config
            for config in cls.configs.values()
            if (session is None or session.is_admin(config))
                and (re.match(course, config.session) or re.match(course, config.course))
        ]

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
            if self.config['compiler'] == 'racket':
                return 'rkt', ';', ''
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
        return f'C5/{self.course.replace("=", "_")}/{self.get_question_filename(question)}'

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

    def get_journal(self, login) -> Optional[common.Journal]:
        """Return the Journal or None"""
        try:
            with open(f'{self.dir_log}/{login}/journal.log', encoding='utf-8') as file:
                return common.Journal(file.read())
        except OSError:
            return None

    def get_waiting_withme_done(self, login):
        """Stats for checkpoint list"""
        waiting = []
        with_me = []
        done = []
        for student, active_teacher_room in self.active_teacher_room.items():
            if active_teacher_room.teacher == login:
                with_me.append(student)
            if not active_teacher_room.active:
                # Student is not working
                if active_teacher_room.room:
                    done.append(student) # Exam closed
                else:
                    waiting.append(student) # Not yet placed
        return waiting, with_me, done

def get_course(txt:str) -> str:
    """Transform «PYTHON:introduction» as «COMPILE_PYTHON/introduction»"""
    try:
        compilator, course = txt.split('=')
    except ValueError:
        raise ValueError(f'Invalid course name: «{txt}»') # pylint: disable=raise-missing-from
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
        service = f'https://{C5_URL}{service}'
        if C5_VALIDATE:
            if self.ticket:
                async with aiohttp.ClientSession() as session:
                    url = C5_VALIDATE % (urllib.parse.quote(service),
                                        urllib.parse.quote(self.ticket))
                    async with session.get(url) as data:
                        content = await data.text()
                        lines = content.split('\n')
                        if lines[0] == 'yes':
                            self.login = xxx_local.normalize_login(lines[1])
                            self.infos = await LDAP.infos(self.login)
                            self.record()
            if not self.login:
                raise web.HTTPFound(C5_REDIRECT + urllib.parse.quote(service))
        else:
            if self.ticket and self.ticket.isdigit():
                self.login = f'anonyme_{self.ticket}'
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
                raise web.HTTPFound(f'https://{C5_URL}{url.path}')
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
            try:
                headers = request.request.headers
            except AttributeError:
                headers = request.request_headers # Deprecated
            if request.remote_address:
                client_ip, _port = request.remote_address
            else:
                client_ip = '0.0.0.0'
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
            if not session.hostname:
                session.hostname = (await DNS.infos(client_ip))['name']
        else:
            session = Session(ticket, client_ip, browser)
            if ticket:
                cls.session_cache[ticket] = session
        if not session.login:
            await session.get_login(request.path)
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
        raise web.HTTPAccepted(body=f"""
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

    def header(self, courses=(), more='', login=None) -> str:
        """Standard header"""
        if not login:
            login = self.login
        return f"""<!DOCTYPE html>
            <html>
            <head>
            <base href="https://{C5_URL}/">
            <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
            <meta charset="utf-8">
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <link REL="icon" href="favicon.ico?ticket={self.ticket}">
            </head>
            <body></body></html>
            <script>
            BASE = "https://{C5_URL}";
            TICKET = {json.dumps(self.ticket)};
            COURSES = {json.dumps(courses)};
            MORE = {json.dumps(more)};
            LOGIN = {json.dumps(login)};
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
            <link REL="icon" href="https://{C5_URL}/favicon.ico?ticket={self.ticket}">
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
            <link REL="icon" href="https://{C5_URL}/favicon.ico?ticket={self.ticket}">
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

init_globals(globals())
