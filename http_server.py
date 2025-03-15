#!/usr/bin/python3
"""
Simple web server with session management
"""

from typing import Dict, List, Tuple, Any, Optional, Union, Callable, Coroutine, Set
import os
import sys
import time
import json
import collections
import tempfile
import zipfile
import asyncio
import logging
import re
import traceback
import html
import io
import pathlib
import glob
import csv
import signal
from aiohttp import web, WSMsgType
from aiohttp.web_request import Request
from aiohttp.web_response import Response,StreamResponse

from aiohttp.abc import AbstractAccessLogger
import options
import common
import xxx_local
import utilities
from utilities import Session, CourseConfig

# To make casauth work we should not use a proxy
for varname in ('http_proxy', 'https_proxy'):
    if varname in os.environ:
        del os.environ[varname]

Type = int # 0...3 type of source
Answer = Tuple[str, Type, int, str]
AnswerPerType = List[Optional[Answer]] # Only 4 items
Answers = Dict[int,List[Answer]]
Blurs = Dict[int,int]

COMPILERS = [i[8:-3].upper()
             for i in os.listdir('.')
             if i.startswith('compile_')
             and i.endswith('.py')
             and i != 'compile_server.py'
             ]

MAKEFILE_README = """
Le répertoire contient un fichier 'Makefile' définissant le projet.
Lancer les commandes :
    make # Pour compiler toutes les questions
    make 01 # Pour compiler (si c'est nécessaire) et exécuter la question 1
"""

DEFAULT_COURSE_OPTIONS_DICT = {
    line[0]: (line[1], line[2])
    for line in options.DEFAULT_COURSE_OPTIONS
    if len(line) == 3
}

def answer(content:Union[str,bytes], content_type:str="text/html",
           charset:str='utf-8', cache:bool=False) -> Response:
    """Standard response"""
    headers = {
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
        }
    if cache:
        headers['Cache-Control'] = 'max-age=86400'
    else:
        headers['Cache-Control'] = 'no-store'
    return web.Response(
        body=content,
        content_type=content_type,
        charset=charset,
        headers=headers
    )

class File:
    """Manage file answer"""
    file_cache:Dict[str,"File"] = {}
    cache = False

    def __init__(self, filename:str):
        self.filename = filename
        self.mtime = 0.
        self.content:Union[str,bytes] = ''
        if '/.' in filename:
            raise ValueError('Hacker')
        self.charset:Optional[str] = 'utf-8'
        if filename.endswith('.html'):
            self.mime = 'text/html'
        elif filename.endswith('.js'):
            self.mime = 'application/x-javascript'
        elif filename.endswith('.ico'):
            self.mime = 'image/vnd.microsoft.icon'
            self.charset = None
        elif filename.endswith('.css'):
            self.mime = 'text/css'
        elif filename.endswith('.png'):
            self.mime = 'image/png'
            self.charset = None
        elif filename.endswith('.gif'):
            self.mime = 'image/gif'
            self.charset = None
        elif filename.endswith('.jpg'):
            self.mime = 'image/jpg'
            self.charset = None
        else:
            log(f'Unknown mimetype {filename}')
            self.mime = 'text/plain'
    def get_content(self) -> Union[str,bytes]:
        """Check file date and returns content"""
        mtime = os.path.getmtime(self.filename)
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.filename, "rb") as file:
                content = file.read()
                self.cache = len(content) > 200000 # checkpoint.js must no yet be cached
                if self.charset is not None:
                    self.content = content.decode(self.charset)
                else:
                    self.content = content
        return self.content
    def answer(self, content:str='') -> Response:
        """Get the response to send"""
        return answer(
            content or self.get_content(),
            content_type=self.mime,
            charset=self.charset or 'binary',
            cache=self.cache
        )
    @classmethod
    def get(cls, filename:str) -> "File":
        """Get or create File object"""
        if filename not in cls.file_cache:
            if not os.path.exists(filename):
                raise web.HTTPUnauthorized(body="Arrêtez de hacker! " + filename)
            cls.file_cache[filename] = File(filename)
        return cls.file_cache[filename]

def filter_last_answer(answers:List[Answer]) -> AnswerPerType:
    """Return the last answer of each status"""
    last:AnswerPerType = [None, None, None, None]
    for source_answer_time in answers:
        last[source_answer_time[1]] = source_answer_time
    return last

async def editor(session:Session, is_admin:bool, course:CourseConfig, # pylint: disable=too-many-arguments,too-many-locals
                 login:str, grading:bool=False, feedback:int=0) -> Response:
    """Return the editor page.
    """
    stop = 8000000000
    real_course = course.course
    if login == 'PYTHON=editor' and is_admin:
        course = CourseConfig.get('COMPILE_PYTHON/editor')
        login = session.login
    else:
        stop = course.get_stop(login)
    infos = await utilities.LDAP.infos(login)
    if grading or feedback >= 5:
        notation = f"NOTATION = {json.dumps(course.get_notation(login))};"
        title = infos['sn'].upper() + ' ' + infos['fn'].title()
    else:
        notation = 'NOTATION = "";'
        title = course.course.split('=', 1)[1]

    grades = None
    the_grade = None
    if feedback >= 3:
        if feedback >= 4:
            active_teacher_room = course.active_teacher_room.get(login)
            if active_teacher_room:
                the_grade = active_teacher_room.grade
                if feedback >= 5:
                    grades = course.get_grades(login)
            else:
                the_grade = 0
                grades = []

    return answer(
        session.header(login=login) + f'''
        <title>{title}</title>
        <link rel="stylesheet" href="HIGHLIGHT/{course.theme}.css?ticket={session.ticket}">
        <link rel="stylesheet" href="ccccc.css?ticket={session.ticket}">
        <script src="HIGHLIGHT/highlight.js?ticket={session.ticket}"></script>
        <script>
            SESSION_LOGIN = "{session.login}";
            GRADING = {int(grading)};{notation}
            STUDENT = "{login}";
            COURSE = "{course.course}";
            REAL_COURSE = "{real_course}";
            SOCK = "wss://{utilities.C5_WEBSOCKET}";
            ADMIN = {int(is_admin)};
            STOP = {stop};
            INFOS = {json.dumps(infos)};
            WHERE = {json.dumps(course.active_teacher_room.get(
                login, utilities.State((False, '?', '?,0,0,a', 0, 0, 0, 'ip', 0, '', 0, 0))))};
            SERVER_TIME = {time.time()};
            GRADE = {json.dumps(the_grade)};
            GRADES = {json.dumps(grades)};
            COURSE_CONFIG = {json.dumps(course.get_config())};
            COURSE_CONFIG['feedback'] = {feedback};
            COMMENT_STRING = {json.dumps(course.get_language()[1])};
        </script>
        <script src="ccccc.js?ticket={session.ticket}"></script>''')


def handle(base:str='') -> Callable[[Request],Coroutine[Any, Any, Response]]:
    """Send the file content"""
    async def real_handle(request:Request) -> Response: # pylint: disable=too-many-branches,too-many-return-statements
        if base:
            session = None # Not authenticated
        else:
            session = await Session.get_or_fail(request)
            login = session.login
        filename = request.match_info['filename']
        course = None
        if not session:
            assert '/.' not in filename
            filename = base + '/' + filename
        else:
            if '=' in filename:
                course = CourseConfig.get(utilities.get_course(filename.lstrip('=')))
                if not course.dir_log:
                    return session.message('unknown')
                is_admin = session.is_grader(course)
                if session.is_student() and not is_admin:
                    login_as = ''
                    status = course.status(login, session.hostname)
                else:
                    login_as = request.query.get('login', '')
                    if login_as == login:
                        login_as = ''
                    if login_as and session.is_proctor(course):
                        status = course.status(login_as) # Should not modify anything
                    else:
                        status = course.status(login, session.hostname)
                # print('session=', session.login, "is_student=", session.is_student(),
                #       "is_admin=", is_admin, utilities.CONFIG.is_admin(session.login),
                #       "status=", status, "login_as=", login_as)
                if status == 'draft':
                    return session.message('draft')
                feedback = course.get_feedback(login_as or login)
                if not is_admin:
                    if status == 'done' and not feedback:
                        return session.message('done')
                    if status == 'pending':
                        return session.message('pending', course.start_timestamp)
                    if status == 'checkpoint':
                        return session.message('checkpoint')
            if filename.startswith("="):
                version = request.match_info.get('version', None)
                if version:
                    place = course.active_teacher_room[login][2]
                    changed = place.split(',')
                    if len(changed) <= 3:
                        changed = ['?', '0', '0', version]
                    else:
                        changed[3] = version
                    course.active_teacher_room[login][2] = ','.join(changed)
                    feedback = 0 # No feedback on try
                return await editor(session, is_admin, course, login_as or login, feedback=feedback)
            if '=' in filename:
                filename = course.file_js
        return File.get(filename).answer()
    return real_handle

async def grade(request:Request) -> Response:
    """Display the grading page"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_grader(course)
    if not is_grader:
        return answer("Vous n'êtes pas autorisé à noter.")
    return await editor(session, True, course, request.match_info['login'], grading=True)

async def record_grade(request:Request) -> Response:
    """Log a grade"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_grader(course)
    if not is_grader:
        return answer("window.parent.ccccc.record_not_done(\"Vous n'êtes pas autorisé à noter.\")")
    post = await request.post()
    login = str(post['student'])
    if not os.path.exists(f'{course.dir_log}/{login}'):
        return answer("window.parent.ccccc.record_not_done(\"Aucun travail à noter.\")")
    if 'grade' in post:
        grades = course.append_grade(
            login, [int(time.time()), session.login, post['grade'], post['value']])
        course.doing_grading[session.login] = time.time()
    else:
        grades = course.get_grades(login)
    return answer(f"window.parent.ccccc.update_grading({json.dumps(grades)})")

async def load_student_infos() -> None:
    """Load all student info in order to answer quickly"""
    for config in CourseConfig.load_all_configs():
        for login in config.active_teacher_room:
            await utilities.LDAP.infos(login)

async def simulate_active_student() -> None:
    """Send a student activity to checkpoints page every seconds"""
    course = CourseConfig.get('COMPILE_REMOTE/grapic')
    student = next(iter(course.active_teacher_room))
    while True:
        await asyncio.sleep(1)
        course.to_send.append(('active_teacher_room', 3, student, time.time()))
        if not course.send_journal_running:
            course.send_journal_running = True
            asyncio.ensure_future(course.send_journal())

async def startup(app:web.Application) -> None:
    """For student names and computer names"""
    if utilities.C5_VALIDATE:
        app['load_student_infos'] = asyncio.create_task(load_student_infos())
    # app['simulate_active_student'] = asyncio.create_task(simulate_active_student())
    log("DATE HOUR STATUS TIME METHOD(POST/GET) TICKET/URL")
    def close_all(*_args, **_kargs):
        JournalLink.close_all_sockets()
    signal.signal(signal.SIGTERM, close_all)


async def get_author_login(request:Request) -> Session:
    """Get the admin login or redirect to home page if it isn't one"""
    session = await Session.get_or_fail(request)
    if not session.is_author():
        raise session.exception('not_author')
    return session

async def get_admin_login(request:Request) -> Session:
    """Get the admin login or redirect to home page if it isn't one"""
    session = await Session.get_or_fail(request)
    if not session.is_admin():
        raise session.exception('not_admin')
    return session

async def get_root_login(request:Request) -> Session:
    """Get the root login or redirect to home page if it isn't one"""
    session = await Session.get_or_fail(request)
    if not session.is_root():
        raise session.exception('not_root')
    return session

async def get_teacher_login_and_course(request:Request, allow=None) -> Tuple[Session,CourseConfig]:
    """Get the teacher login or redirect to home page if it isn't one"""
    session = await Session.get_or_fail(request)
    course = CourseConfig.get(utilities.get_course(request.match_info['course']))
    if session.is_student() and allow != session.login and not session.is_proctor(course):
        raise session.exception('not_teacher')
    return session, course

async def adm_course(request:Request) -> Response:
    """Course details page for administrators"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.exception('not_proctor')

    stream = web.StreamResponse(headers={
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
        })
    stream.content_type = 'text/html;charset=UTF-8'
    await stream.prepare(request)
    await stream.write(
        (session.header() + f"""
            <script>
            STUDENT_DICT = {json.dumps(course.active_teacher_room)};
            COURSE = '{course.course}';
            NOTATION = {json.dumps(course.config['notation'])};
            NOTATIONB = {json.dumps(course.config['notationB'])};
            STUDENTS = {{
            """).encode('utf-8'))
    separator = ''
    for user in sorted(os.listdir(course.dir_log)):
        files:List[str] = []
        student:Dict[str,Any] = {'files': files}
        for filename in sorted(os.listdir(f'{course.dir_log}/{user}')):
            if '.' in filename:
                # To not display executables
                files.append(filename)
        try:
            student['status'] = course.status(user)
            with open(f'{course.dir_log}/{user}/journal.log', encoding='utf-8') as file:
                student['journal'] = file.read()

            filename = f'{course.dir_log}/{user}/grades.log'
            if os.path.exists(filename):
                with open(filename, encoding='utf-8') as file:
                    student['grades'] = file.read()
        except IOError:
            pass
        await stream.write(f'{separator} {json.dumps(user)}: {json.dumps(student)}'.encode('utf-8'))
        separator = ','

    await stream.write(
        f"""}}
            </script>
            <script src="adm_course.js?ticket={session.ticket}"></script>
            <div id="top"></div>
            """.encode('utf-8'))
    return stream

async def git_pull(course, stream):
    """GIT pull for a course."""
    await stream.write(f'<h1>{course.course}</h1>'.encode('utf-8'))
    git_url = course.config['git_url']
    if not git_url:
        await stream.write("Vous devez d'abord définir l'URL GIT".encode('utf-8'))
        return
    command = rf'''
    cd {course.dir_session}
    echo "
*.cf
*.js
*.json
*~
.gitignore
LOGS
" >.gitignore
    if [ ! -d .git ]
    then
        git init
        mkdir XXX
        mv questions.py MEDIA XXX 2>/dev/null
        git pull {git_url}
        mv XXX/questions.py .
        if [ -d XXX/MEDIA ]
            then
            mkdir MEDIA 2>/dev/null
            mv XXX/MEDIA/* MEDIA
            rmdir XXX/MEDIA
            fi
        rmdir XXX
        git status # The status should be clean
    else
        git stash
        git pull {git_url}
        git stash pop
        if ! git diff --exit-code --quiet
        then
            echo -n '<div style="background:#FF0">'
            (
            echo "############################# START ###########################"
            echo "patch -u -p1 <<%END-OF_FILE%"
            git diff --binary
            echo "%END-OF_FILE%"
            echo "git add questions.py MEDIA"
            echo "git commit -m 'Modifications venant de C5'"
            echo "git push"
            echo "############################# STOP ###########################"
            ) | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'
            echo "</div>"
        fi
    fi
    cd ../..
    make {course.dir_session}/questions.js
    '''

    await stream.write(b'<pre>')
    process = await asyncio.create_subprocess_exec(
                'sh', '-c', command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                )
    while True:
        data = await process.stdout.read(64 * 1024)
        if data:
            await stream.write(data)
        else:
            break
    await stream.write(b'</pre>')

async def adm_git_pull(request:Request) -> Response:
    """Course details page for administrators"""
    session, config = await get_course_config(request)
    course = request.match_info['course']
    if course.startswith('^'):
        configs = [
            config
            for config in CourseConfig.configs.values()
            if re.match(course, config.session)
        ]
    else:
        configs = [config]

    stream = web.StreamResponse()
    stream.content_type = 'text/html;charset=UTF-8'
    await stream.prepare(request)
    await stream.write(b'<title>GIT PULL</title>')

    for config in configs:
        if session.is_admin(config):
            await git_pull(config, stream)
    return stream

async def adm_force_grading_done(request:Request) -> Response:
    """Force grading done for complete grading"""
    session, config = await get_course_config(request)
    course = request.match_info['course']
    if course.startswith('^'):
        configs = [
            config
            for config in CourseConfig.configs.values()
            if re.match(course, config.session)
        ]
    else:
        configs = [config]

    stream = web.StreamResponse()
    stream.content_type = 'text/html;charset=UTF-8'
    await stream.prepare(request)
    await stream.write(b'<title>Force grading done</title>')

    for config in configs:
        if not session.is_admin(config):
            continue
        await stream.write(f'<h1>{config.course}</h1><pre>'.encode('utf-8'))
        nbr_grades = {'a': len(common.parse_notation(config.notation)) - 1}
        if config.notationB:
            nbr_grades['b'] = len(common.parse_notation(config.notationB)) - 1
        else:
            nbr_grades['b'] = nbr_grades['a']
        for student, state in config.active_teacher_room.items():
            if state.feedback == 5:
                await stream.write(f'{student}: yet with feedback.\n'.encode('utf-8'))
                continue
            if not state.grade:
                await stream.write(f'{student}: ungraded.\n'.encode('utf-8'))
                continue
            version = state.room.split(',')[3]
            if state.grade[1] != nbr_grades[version]:
                await stream.write(f'{student}: grading unfinished.\n'.encode('utf-8'))
                continue # Not finished grading
            config.set_parameter('active_teacher_room', 5, student, 10)
            await stream.write(f'{student}: <b>Force grading done.</b>\n'.encode('utf-8'))
        await stream.write(b'</pre>')
    return stream

def move_to_trash(path):
    """Move a file to the Trash"""
    if os.path.exists(path):
        timestamp = time.strftime('%Y%m%d%H%M%S')
        os.rename(path, f'Trash/{timestamp}-{path.replace("/", "_")}')

async def adm_media(request:Request) -> Response:
    """Display session media"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.exception('not_proctor')
    action = request.match_info['action']
    media = request.match_info['media']
    medias = []
    for media_name in tuple(course.media):
        if media == media_name:
            if action == 'delete':
                move_to_trash(f'{course.dir_media}/{media_name}')
                course.media.remove(media_name)
                continue
        medias.append(f'''
        <div style="background: #FFF; display: inline-block;">
        {media_name}
        <button onclick="window.location = 'https://{utilities.C5_URL}/adm/media/{course.course}/delete/{media_name}?ticket={session.ticket}'"
                style="float: right; font-family: emoji"
        >🗑</button>
        <br>
        <img src="media/{course.course}/{media_name}?ticket={session.ticket}"
             style="vertical-align: bottom"
        ></div>''')
    return answer(session.header() + ''.join(medias))

def fix_date(value):
    """Parse a date/hour entered by a human"""
    value = re.split('[- :]+', value)
    while len(value) < 6:
        value.append(0)
    value = [int(i or '0') for i in value]
    value = '{:4d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}'.format(*value) # pylint: disable=consider-using-f-string
    try:
        time.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value
    except ValueError:
        return None

async def adm_config_course(config:CourseConfig, action:str, value:str) -> Union[Response,str]: # pylint: disable=too-many-branches,too-many-statements
    """Configure a course"""
    course = config.course
    if value == 'now':
        value = time.strftime('%Y-%m-%d %H:%M:%S')
    if action == 'stop':
        fixed = fix_date(value)
        if fixed:
            config.set_parameter('stop', fixed)
            feedback = f"«{course}» Stop date updated to «{fixed}»"
        else:
            feedback = f"«{course}» Stop date invalid: «{value}»!"
    elif action == 'start':
        fixed = fix_date(value)
        if fixed:
            config.set_parameter('start', fixed)
            feedback = f"«{course}» Start date updated to «{fixed}»"
        else:
            feedback = f"«{course}» Start date invalid: «{value}»!"
    elif action == 'tt':
        value = xxx_local.normalize_logins(value)
        config.set_parameter('tt', value)
        feedback = f"«{course}» TT list updated with «{value}»"
    elif action == 'expected_students':
        value = xxx_local.normalize_logins(value)
        config.set_parameter('expected_students', value)
        feedback = f"«{course}» Expected student list updated with «{value}»"
    elif action == 'expected_students_required':
        config.set_parameter('expected_students_required', int(value))
        if value == '0':
            feedback = f"«{course}» All students see this session."
        else:
            feedback = f"«{course}» Restricted to expected students."
    elif action == 'admins':
        value = xxx_local.normalize_logins(value)
        config.set_parameter('admins', value)
        feedback = f"«{course}» Admins list updated with «{value}»"
    elif action == 'graders':
        value = xxx_local.normalize_logins(value)
        config.set_parameter('graders', value)
        feedback = f"«{course}» Graders list updated with «{value}»"
    elif action == 'proctors':
        value = xxx_local.normalize_logins(value)
        config.set_parameter('proctors', value)
        feedback = f"«{course}» Proctors list updated with «{value}»"
    elif action == 'theme':
        if os.path.exists(f'HIGHLIGHT/{value}.css'):
            config.set_parameter('theme', value)
            feedback = f"«{course}» Highlight theme updated to «{value}»"
        else:
            feedback = f"«{course}» Highlight theme «{value}» does not exists!"
    elif action == 'state':
        if value in ('Draft', 'Ready', 'Grade', 'Done', 'Archive'):
            config.set_parameter('state', value)
            feedback = f"«{course}» state updated to «{value}»"
        else:
            feedback = f"«{course}» state «{value}» does not exists!"
    elif action == 'allow_copy_paste':
        config.set_parameter('allow_copy_paste', int(value))
        feedback = f"«{course}» Copy Paste «{'not' if value == '0' else ''} allowed»"
    elif action == 'allow_ip_change':
        config.set_parameter('allow_ip_change', int(value))
        feedback = f"«{course}» Allow IP change «{'not' if value == '0' else ''} allowed»"
    elif action == 'coloring':
        config.set_parameter('coloring', int(value))
        feedback = f"«{course}» Syntax coloring: «{value != '0'}»"
    elif action == 'save_unlock':
        config.set_parameter('save_unlock', int(value))
        yes_no = 'not' if value == '0' else ''
        feedback = f"«{course}» Unlock next question on save «{yes_no} allowed»"
    elif action == 'checkpoint':
        config.set_parameter('checkpoint', int(value))
        if value == '0':
            feedback = f"«{course}» Automatic access to the session"
        else:
            feedback = f"«{course}» Need teacher approval to start"
    elif action == 'sequential':
        config.set_parameter('sequential', int(value))
        if value == '0':
            feedback = f"«{course}» All questions are accessible in a random order."
        else:
            feedback = f"«{course}» Questions are accessible only if the previous are corrects."
    elif action == 'notation':
        config.set_parameter('notation', value)
        feedback = f"«{course}» Notation version A set to {value[:100]}"
    elif action == 'notationB':
        config.set_parameter('notationB', value)
        feedback = f"«{course}» Notation version B set to {value[:100]}"
    elif action == 'notation_max':
        config.set_parameter('notation_max', float(value))
        feedback = f"«{course}» Maximum grade set to {value[:100]}"
    elif action == 'highlight':
        assert re.match('#[0-9A-Z]{3}', value)
        config.set_parameter('highlight', value)
        feedback = f"«{course}» The session color is now {value}"
    elif action in ('delete', 'delete_students'):
        if not os.path.exists('Trash'):
            os.mkdir('Trash')
        if action == 'delete':
            to_delete = config.dir_session
        else:
            to_delete = config.dir_log
        move_to_trash(to_delete)
        if action == 'delete':
            del CourseConfig.configs[config.dir_session]
            return f"«{course}» moved to Trash directory. Now close this page!"
        config.config['active_teacher_room'] = {}
        config.config['messages'] = []
        config.config['tt'] = ''
        config.config['expected_students'] = ''
        config.config['state'] = 'Draft'
        config.update()
        config.record_config()
        return f"«{course}» students moved to Trash. Now close this page!"
    elif action == 'rename':
        value = value.replace('.py', '')
        new_dirname = f'COMPILE_{config.compiler}/{value}'
        if '.' in value or '/' in value:
            return f"«{value}» invalid name because it contains «/», «.»"
        if os.path.exists(new_dirname):
            return f"«{value}» exists!"
        os.rename(config.dir_session, new_dirname)
        del CourseConfig.configs[config.dir_session] # Delete old
        CourseConfig.get(new_dirname) # Full reload of new (safer than updating)
        return f"«{course}» Renamed as «{config.compiler}={value}». Now close this page!"
    elif action == 'display_student_filter':
        config.set_parameter('display_student_filter', int(value))
        feedback = f"«{course}» «{'do not' if value == '0' else ''} display student filter."
    elif action == 'display_session_name':
        config.set_parameter('display_session_name', int(value))
        feedback = f"«{course}» «{'do not' if value == '0' else ''} display session name."
    elif action == 'display_my_rooms':
        config.set_parameter('display_my_rooms', int(value))
        feedback = f"«{course}» «{'do not' if value == '0' else ''} display «My rooms»."
    elif action == 'default_building':
        buildings = set(utilities.get_buildings())
        if value in buildings:
            config.set_parameter('default_building', value)
            feedback = f"«{course}» default building is «{value}»."
        else:
            feedback = f"«{course}» «{value}» not in {buildings}!"
    elif action in DEFAULT_COURSE_OPTIONS_DICT:
        default_value, _comment = DEFAULT_COURSE_OPTIONS_DICT[action]
        if isinstance(default_value, int):
            if value == 'on':
                value = 1
            value = int(value)
        if isinstance(default_value, float):
            value = float(value)
        elif isinstance(default_value, (list, dict)):
            value = json.loads(value)
        config.set_parameter(action, value)
        feedback = f"«{course}» {action}={value}"

    return answer(
        f'''<script>window.parent.update_course_config(
            {json.dumps(config.config)}, {json.dumps(feedback)})</script>''')

async def adm_config(request:Request) -> Response: # pylint: disable=too-many-branches
    """Course details page for administrators"""
    action = request.match_info['action']
    try:
        post = await request.post()
        value = post['value']
    except: # pylint: disable=bare-except
        value = request.match_info.get('value')

    session, config = await get_course_config(request)
    course = config.course
    if course.startswith('^'):
        # Configuration of multiple session with regular expression
        the_answers = []
        for conf in tuple(CourseConfig.configs.values()):
            if session.is_admin(conf) and re.match(course, conf.session):
                the_answers.append(await adm_config_course(conf, action, value))
    else:
        # Configuration of a single session
        the_answers = [await adm_config_course(config, action, value)]
    if the_answers:
        if isinstance(the_answers[0], str):
            return answer('<br>'.join(str(i) for i in the_answers))
        return the_answers[0]
    return answer("Aucune session ne correspond")

def text_to_dict(text:str) -> Dict[str,str]:
    """Transform a user text to a dict.
             key1 value1
             key2 value2
        Become: {'key1': 'value1', 'key2': 'value2'}
    """
    dictionary = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            try:
                key, value = line.split(' ', 1)
                dictionary[key] = value
            except ValueError:
                pass
    return dictionary

async def adm_c5(request:Request) -> Response: # pylint: disable=too-many-branches,too-many-statements
    """Remove a C5 master"""
    _session = await get_root_login(request)
    action = request.match_info['action']
    post = await request.post()
    value = str(post['value'])
    more = "Nothing to do"
    if action.startswith(('add_', 'del_')):
        deladd, what = action.split('_')
        logins = getattr(utilities.CONFIG, what + 's')
        if deladd == 'add':
            if value not in logins:
                logins.append(value)
        else:
            if value in logins:
                logins.remove(value)
        utilities.CONFIG.set_value(what + 's', logins)
        more = f"{what.title()} {deladd} «{value}»"
    elif action == 'ips_per_room':
        try:
            utilities.CONFIG.set_value_dict(action, text_to_dict(value))
            more = f"IPs per room updated to<pre>{value}</pre>"
        except ValueError:
            more = "Invalid syntax!"
    elif action == 'messages':
        try:
            utilities.CONFIG.set_value_dict(action, text_to_dict(value))
            more = f"Messages updated to<pre>{value}</pre>"
        except ValueError:
            more = "Invalid syntax!"
    elif action == 'ticket_ttl':
        try:
            utilities.CONFIG.set_value(action, int(value))
            more = f"Ticket TTL updated to {value} seconds"
        except ValueError:
            more = "Invalid ticket TTL!"
    elif action == 'student':
        try:
            utilities.CONFIG.set_value(action, value)
            more = f"Student detector updated to «{value}» regexp"
        except ValueError:
            more = "Invalid regexp!"
    elif action == 'remove_old_tickets':
        # Load in order to remove!
        nr_deleted = 0
        for ticket in os.listdir('TICKETS'):
            session = Session.load_ticket_file(ticket)
            if session.too_old():
                nr_deleted += 1
                await asyncio.sleep(0)
        more = f"{nr_deleted} tickets deleted."
    elif action == 'eval':
        try:
            result = repr(eval(value)) # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            result = traceback.format_exc()
        more = '<b>' + html.escape(value) + '</b><pre>' + html.escape(result) + '</pre>'
    else:
        more = "You are a hacker!"
    return await adm_root(request, more)

async def adm_root(request:Request, more:str='') -> Response:
    """Home page for roots"""
    if more:
        if more.endswith('!'):
            more = '<div id="more" style="background: #F88">' + more + '</div>'
        else:
            more = '<div id="more">' + more + '</div>'

    session = await get_root_login(request)
    return answer(
        session.header((), more)
        + f'<script src="adm_root.js?ticket={session.ticket}"></script>')

async def adm_get(request:Request) -> StreamResponse:
    """Get a file or a ZIP"""
    session = await get_admin_login(request)
    filename = request.match_info['filename']
    if '/.' in filename:
        content = 'Hacker'
    else:
        if filename.endswith('.zip'):
            stream = web.StreamResponse()
            stream.content_type = 'application/zip'
            await stream.prepare(request)
            course = filename[:-4]
            exclude = ['*/' + name + '*'
                       for name in request.match_info.get('exclude', '').split(' ')
                       if name and not name.startswith('-')
                      ]
            if course.startswith('COMPILE_^'):
                course = course.split('COMPILE_')[1]
                courses = [config.dir_session
                           for config in CourseConfig.configs.values()
                           if session.is_admin(config) and re.match(course, config.session)
                           ]
            else:
                courses = [course.replace('=', '/', 1)]
            args = ['zip', '-r', '-', *courses,
                    '--exclude', '*/HOME/*', '*/libsandbox.so', '*/.git/*', *exclude]
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                )
            assert process.stdout
            data = b'FakeData'
            while data:
                data = await process.stdout.read(64 * 1024)
                await stream.write(data)
            return stream
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
    return answer(content, content_type='text/plain')

async def my_zip(request:Request) -> StreamResponse: # pylint: disable=too-many-locals
    """Get ZIP"""
    session = await Session.get_or_fail(request)
    course = request.match_info['course']
    if course != 'C5.zip':
        configs = [CourseConfig.get(utilities.get_course(course))]
    else:
        configs = list(CourseConfig.configs.values())
    data = io.BytesIO()
    with zipfile.ZipFile(data, mode="w", compression=zipfile.ZIP_DEFLATED) as zipper:
        for config in configs:
            if (config.get_feedback(session.login) == 0
                    and config.checkpoint):
                continue
            journa = config.get_journal(session.login)
            if not journa:
                continue
            makefile = config.get_makefile()
            if makefile:
                zipper.writestr(f'C5/{config.course.replace("=", "_")}/Makefile', makefile)
            for question, stats in journa.questions.items():
                if question < 0:
                    continue
                source = stats.source
                mtime = time.localtime(int(journa.timestamps[stats.head-1]))
                timetuple = (mtime.tm_year, mtime.tm_mon, mtime.tm_mday,
                                mtime.tm_hour, mtime.tm_min, mtime.tm_sec)
                title = config.get_question_path(question)
                zipper.writestr(title, source)
                zipper.infolist()[-1].date_time = timetuple

    stream = web.StreamResponse()
    stream.content_type = 'application/zip'
    await stream.prepare(request)
    await stream.write(data.getvalue())

    return stream

async def my_git(request:Request) -> StreamResponse: # pylint: disable=too-many-locals
    """Create GIT repository"""
    session = await Session.get_or_fail(request)
    course = CourseConfig.get(utilities.get_course(request.match_info['course']))

    answers, _blurs = get_answers(course.dir_log, session.login)
    if not os.path.exists('xxx-GIT'):
        os.mkdir('xxx-GIT')
    root = f'xxx-GIT/{session.login}'
    if not os.path.exists(root):
        os.mkdir(root)
    git_dir = None

    async def run(program, *args, **kargs):
        if 'cwd' not in kargs:
            kargs['cwd'] = git_dir
        process = await asyncio.create_subprocess_exec(program, *args, **kargs)
        await process.wait()

    git_dir = ''
    infos = await utilities.LDAP.infos(session.login)
    author_name = f"{infos['fn'].title()} {infos['sn'].upper()}"
    author_email = infos.get('mail', 'x@y.z')
    question = None
    for (source, _type, timestamp, tag), question in sorted(
            ((source, question) # The saved sources
            for question, sources in answers.items()
            for source in sources
            if source[1] <= 1
            ),
            key = lambda x: x[0][2]):
        question = int(question)
        title = course.get_question_path(question)
        filename = pathlib.Path(root + '/' + title)
        filename.parent.mkdir(parents=True, exist_ok=True)
        filename.write_text(source, encoding='utf8')
        if not git_dir:
            git_dir = str(filename.parent)
            await run('git', 'init', '-b', 'master')
            makefile = course.get_makefile()
            if makefile:
                pathlib.Path(f'{root}/C5/{course.course.replace("=", "_")}/Makefile').write_text(
                    makefile, encoding='utf8')
                await run('git', 'add', 'Makefile')
        await run('git', 'add', course.get_question_filename(question))
        await run(
            'git', 'commit',
            '-m', f'{course.get_question_name(question)}: {tag}',
            '--date', str(timestamp),
            env={
                'GIT_AUTHOR_NAME': author_name,
                'GIT_AUTHOR_EMAIL': author_email,
                'GIT_COMMITTER_NAME': author_name,
                'GIT_COMMITTER_EMAIL': author_email,
             })
    if git_dir:
        await run('git', 'gc')
    else:
        return answer("Rien n'a été trouvé pour mettre dans le dépôt GIT")

    data = io.BytesIO()

    with zipfile.ZipFile(data, mode="w", compression=zipfile.ZIP_DEFLATED) as zipper:
        zipper.writestr('C5/README',
            f'''Dans un shell, mettez-vous dans la session C5 qui vous intéresse :
    cd '{str(filename.parent).replace(root + '/C5/', '')}'
{MAKEFILE_README}
Pour voir l'historique de vos modifications, voici les commandes :
    git log        # Les dates des changements et les TAG que vous avez mis.
    git log --stat # idem + nombre de lignes ajoutées et enlevées.
    git log -p     # Affiche les changements entre une version et la suivante.
    git log -p '{course.get_question_filename(question)}' # Seulement pour le fichier indiqué.

Toutes les commandes précédentes affichent un numéro de commit en hexadécimal.
    git show UnNuméroDeCommit     # affiche les modifications faites à cette date.
    git checkout UnNuméroDeCommit # modifie les fichiers pour revenir à cette date.
    # Affiche le contenu du fichier pour le commit indiqué :
    git show UnNuméroDeCommit:'{course.get_question_filename(question)}'

''')
        for filename in pathlib.Path(root + '/C5').rglob('**/*'):
            zipper.write(filename, arcname=str(filename).replace(root + '/', ''))
    await run('rm', '-rf', root, cwd='.')
    stream = web.StreamResponse()
    stream.content_type = 'application/zip'
    await stream.prepare(request)
    await stream.write(data.getvalue())
    return stream

def get_answers(course:str, user:str, compiled:bool=False) -> Tuple[Answers, Blurs] : # pylint: disable=too-many-branches,too-many-locals
    """Get question answers.
       The types are:
         * 0 : saved source
         * 1 : source passing the test
         * 2 : compilation (if compiled is True)
         * 3 : Final state of the source code
    Returns 'answers' and 'blurs'
    answers is a dict from question to a list of [source, type, timestamp, tag]
    """
    answers:Answers = collections.defaultdict(list)
    blurs:Dict[int,int] = collections.defaultdict(int)
    final:Dict[int,str] = {}
    filename = f'{course}/{user}/journal.log'
    if not os.path.exists(filename):
        return answers, blurs
    journa = common.Journal()
    with open(f'{course}/{user}/journal.log', newline='\n', encoding='utf-8') as file:
        for line in file:
            line = line[:-1]
            if not line:
                continue
            journa.append(line)
            timestamp = int(journa.timestamp)
            final[journa.question] = (journa.content, 3, timestamp, '')
            if line.startswith('Sanswer'):
                answers[journa.question].append((journa.content, 1, timestamp, ''))
            elif line.startswith('Ssave'):
                answers[journa.question].append((journa.content, 0, timestamp, ''))
            elif line.startswith('Ssnapshot'):
                answers[journa.question].append((journa.content, 3, timestamp, ''))
            elif line.startswith('t'):
                answers[journa.question].append((journa.content, 0, timestamp, line[1:-1]))
            elif line.startswith('B'):
                blurs[journa.question] += 1
            elif compiled and line.startswith('c'):
                answers[journa.question].append((journa.content, 2, timestamp, ''))
    # XXX These lines are only useful for journals generated by upgrade_logs.py
    for question, responses in enumerate(answers.values()):
        for response in responses:
            if response[1] == 3:
                break # Yet a snapshot
        else:
            if question in final:
                responses.append(final[question])
    return answers, blurs

def question_source(config:CourseConfig, comment:str, where:str, user:str, # pylint: disable=too-many-arguments,too-many-locals
                    question:int, answers:List[Answer], blurs:Blurs):
    """Nice source content"""
    content = [
        f"""
{comment} ##################################################################
{comment} {config.session}
{comment} {where}
{comment} {f'Nombre de pertes de focus : {blurs[question]}' if blurs[question] else ''}
{comment} {user}     Question {question+1}
{comment} ##################################################################

"""]

    last = filter_last_answer(answers)
    current = 0
    last_source = ''
    for infos, what in zip(last, (
        "sauvegarde manuelle par l'étudiant",
        'test réussi',
        'compilation faites après la sauvegarde manuelle (pouvant ajouter des bugs)',
        'sauvegarde de dernière seconde (aucune sauvegarde ni compilation)')):
        if not infos:
            continue
        source, _what, timestamp, tag = infos
        if timestamp < current:
            continue
        if last_source == source:
            continue
        last_source = source
        current = timestamp
        content.append(f"""
{comment} ------------------------------------------------------------------
{comment} {time.ctime(timestamp)} {tag} : {what}
{comment} ------------------------------------------------------------------

{source}
""")

    return ''.join(content)

async def adm_answers(request:Request) -> StreamResponse: # pylint: disable=too-many-locals
    """Get students answers"""
    _session, config = await get_teacher_login_and_course(request)
    fildes, filename = tempfile.mkstemp()
    extension, comment = config.get_language()[:2]
    students = request.match_info['students']
    if students != '*':
        students = set(students.split(','))
    try:
        with zipfile.ZipFile(os.fdopen(fildes, "wb"), mode="w") as zipper:
            for user in sorted(os.listdir(config.dir_log)):
                if students != '*' and user not in students:
                    continue
                await asyncio.sleep(0)
                answers, blurs = get_answers(config.dir_log, user, compiled=True)
                if not answers:
                    continue
                infos = config.active_teacher_room.get(user)
                building, pos_x, pos_y, version = ((infos.room or '?') + ',?,?,?').split(',')[:4]
                version = version.upper()
                where = f'Surveillant: {infos.teacher}, {building} {pos_x}×{pos_y}, Version: {version}'
                zipper.writestr(
                    f'{config.dir_log}/{user}#answers.{extension}',
                    ''.join(
                        question_source(config, comment, where, user,
                                        question, answers[question], blurs)
                        for question in answers
                    ))
        with open(filename, 'rb') as file:
            data = file.read()
    finally:
        os.unlink(filename)
        del zipper

    return answer(data, content_type='application/zip')

async def update_file(request:Request, session:Session, compiler:str, replace:str):
    """Update questionnary on disc if allowed"""
    # pylint: disable=too-many-return-statements,too-many-branches
    post = await request.post()
    filehandle = post['course']

    if not hasattr(filehandle, 'filename'):
        return "You must select a file!"
    src_filename = getattr(filehandle, 'filename', None)
    if not src_filename:
        return "You must select a file!"
    if src_filename is None:
        return "You forgot to select a course file!"
    if not src_filename.endswith('.py'):
        return "Only «.py» file allowed!"
    if '/' in src_filename:
        return f"«{src_filename}» invalid name: contains «/»!"
    if replace and replace != src_filename:
        return f"«{src_filename}» is not equal to «{replace}»!"
    compiler_py = 'compile_' + compiler.lower() + '.py'
    if not os.path.exists(compiler_py):
        return f"«{src_filename}» use a not defined compiler: «{compiler_py}»!"

    dst_dirname = f'COMPILE_{compiler}/{replace or src_filename}'[:-3]
    if os.path.exists(dst_dirname):
        if not replace:
            return f"«{dst_dirname}» file exists!"
    else:
        os.mkdir(dst_dirname)

    # All seems fine

    assert isinstance(filehandle, web.FileField)

    if os.path.exists(dst_dirname + '/questions.py'):
        os.rename(dst_dirname + '/questions.py', dst_dirname + '/questions.py~')
    with open(dst_dirname + '/questions.py', "wb") as file:
        file.write(filehandle.file.read())

    process = await asyncio.create_subprocess_exec(
        "make", dst_dirname + '/questions.js',
        stderr=asyncio.subprocess.PIPE
        )
    outputs = await process.stderr.read()
    if outputs:
        errors = f'<pre style="background:#FAA">{outputs.decode("utf-8")}</pre>'
    else:
        errors = ''
    await process.wait()
    if errors:
        if os.path.exists(dst_dirname + '/questions.py~'):
            os.rename(dst_dirname + '/questions.py~', dst_dirname + '/questions.py')
        else:
            for filename in os.listdir(dst_dirname):
                os.unlink(dst_dirname + '/' + filename)
            os.rmdir(dst_dirname)
        return errors

    if replace:
        return f"«{src_filename}» replace «{dst_dirname}/questions.py» file"

    config = CourseConfig.get(dst_dirname)
    config.set_parameter('creator', session.login)
    config.set_parameter('stop', '2100-01-01 00:00:01')
    config.set_parameter('state', 'Draft')
    return f"Course «{dst_dirname}» added"

async def upload_course(request:Request) -> Response:
    """Add a new course"""
    session = await Session.get_or_fail(request)
    message = ''
    compiler = request.match_info['compiler']
    replace = request.match_info['course']
    if replace == '_new_':
        replace = ''
    if replace:
        course = CourseConfig.get(f'COMPILE_{compiler.upper()}/{replace}')
        if not session.is_admin(course):
            message = "Session change is not allowed!"
        replace += '.py'
    else:
        if not session.is_author():
            message = "Session adding is not allowed!"
    if not message:
        message = await update_file(request, session, compiler, replace)
    if '!' not in message and '<pre' not in message and not replace:
        raise web.HTTPFound(f'https://{utilities.C5_URL}/checkpoint/*?ticket={session.ticket}')
    style = 'background:#FAA;'
    if '!' not in message:
        try:
            # Create session.cf
            CourseConfig.get(f'COMPILE_{compiler.upper()}/{replace[:-3]}')
            style = ''
        except ValueError:
            message = "ERROR: Le fichier Python ne contient pas un questionnaire."
    return answer('<style>BODY {margin:0px;font-family:sans-serif;}</style>'
        + '<div style="height:100%;' + style + '">'
        + message + '</div>')

async def store_media(request:Request, course:CourseConfig) -> str:
    """Store a file to allow its use in questionnaries"""
    post = await request.post()
    filehandle = post['course']
    if not hasattr(filehandle, 'filename'):
        return "You must select a file!"
    media_name = getattr(filehandle, 'filename', None)
    if not media_name:
        return "You must select a file!"
    if media_name is None:
        return "You forgot to select a course file!"
    assert isinstance(filehandle, web.FileField)
    if not os.path.exists(course.dir_media):
        os.mkdir(course.dir_media)
    with open(f'{course.dir_media}/{media_name}' , "wb") as file:
        file.write(filehandle.file.read())
    return f"""<tt style="font-size:100%">'&lt;img src="media/{course.course}/{media_name}'
        + location.search + '"&gt;'</tt>"""

async def upload_media(request:Request) -> Response:
    """Add a new media"""
    session = await Session.get_or_fail(request)
    message = ''
    compiler = request.match_info['compiler']
    course_name = request.match_info['course']
    course = CourseConfig.get(f'COMPILE_{compiler.upper()}/{course_name}')
    if session.is_admin(course):
        message = await store_media(request, course)
        course.update()
    else:
        message = "Not allowed to add media!"

    if '!' in message:
        style = 'background:#FAA;'
    else:
        style = ''
    return answer('<style>BODY {margin:0px;font-family:sans-serif;}</style>'
        + '<div style="height:100%;' + style + '">'
        + message + '</div>')

async def config_reload(request:Request) -> Response:
    """For regression tests"""
    _session = await Session.get(request)
    utilities.CONFIG.load()
    return answer('done')

def tipped(logins_spaced:str) -> str:
    """The best way to display truncated text"""
    logins = re.split('[ \t\n]+', logins_spaced.strip())
    if not logins:
        return '<td class="names"><div></div>'
    if len(logins) == 1:
        return '<td class="clipped names"><div>' + logins[0] + '</div>'
    return '<td class="tipped names"><div>' + ' '.join(logins) + '</div>'

def nice_duration(seconds):
    """Human readable duration"""
    minutes = int(seconds)//60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    if weeks > 100:
        duration = ''
    elif weeks:
        duration = f'{weeks} weeks'
        if days % 7:
            duration += f'+{days % 7}d'
    elif days:
        duration = f'{days} days'
        if hours % 24:
            duration += f'+{hours % 24}h'
    elif hours:
        duration = f'{hours}h'
        if minutes % 60:
            duration += f'{minutes % 60:02d}'
    else:
        duration = f'{minutes}m'
    return duration


def checkpoint_line(session:Session, course:CourseConfig, content:List[str]) -> None:
    """A line in the checkpoint table"""
    waiting, with_me, _done = course.get_waiting_withme_done(session.login)
    bools = ''
    for attr, letter, tip in (
        # ('coloring', '🎨', 'Syntaxic source code coloring'),
        ('allow_copy_paste', '✂', 'Copy/Paste allowed'),
        ('checkpoint', '🚦', 'Checkpoint required'),
        ('sequential', 'S', 'Sequential question access'),
        ('save_unlock', '🔓', 'Save unlock next question'),
        ('allow_ip_change', 'IP', 'Allow IP change'),
        ('expected_students_required', '🪪', 'Only expected students'),
    ):
        value = course.config.get(attr, 0)
        if str(value).isdigit():
            value = int(value)
        if value:
            if attr == 'coloring':
                tip += ' «' + course.theme + '»'
            bools += '<span>' + letter + '<var>' + tip + '</var></span>'

    medias = []
    for media in course.media:
        medias.append(f'<a target="_blank" href="media/{course.course}/{media}'
                      f'?ticket={session.ticket}">{media}</a>')
    medias = ' '.join(medias)
    if session.is_grader(course):
        run = 'Try'
    else:
        run = 'Take'
    content.append(f'''
    <tr>
    <td class="clipped course"><div>{course.course.split('=')[1]}</div></td>
    <td class="clipped compiler"><div>{course.course.split('=')[0].title()}</div>
    <td class="clipped title"><div>{html.escape(course.title)}</div>
    <td>{len(course.active_teacher_room) or ''}
    <td>{len(waiting) if course.checkpoint else ''}
    <td><b>{course.number_of_active_students() or ''}</b>
    <td>{len(with_me) or ''}
    <td style="white-space: nowrap">{course.start if course.start > "2001" else ""}
    <td style="white-space: nowrap">{course.stop if course.stop < "2100" else ""}
    <td style="white-space: nowrap">{nice_duration(course.stop_timestamp - course.start_timestamp)}
    <td style="white-space: nowrap; background:{course.config['highlight']}">{bools}
    <td> {
        f'<a target="_blank" href="adm/session/{course.course}?ticket={session.ticket}">Edit</a>'
        if session.is_admin(course) else ''
    }
    <td> {
        f'<a target="_blank" href="={course.course}?ticket={session.ticket}">{run}</a>'
        if course.status('').startswith('running') or session.is_grader(course)
        else ''
    }
    <td> {
        f'<a target="_blank" href="checkpoint/{course.course}?ticket={session.ticket}">Place</a>'
        if session.is_proctor(course) else ''
    }
    <td class="clipped names"><div>{course.creator}</div>
    {tipped(course.config['admins'])}
    {tipped(course.config['graders'])}
    {tipped(course.config['proctors'])}
    {tipped(medias)}
    </tr>''')

def checkpoint_table(session:Session, courses:List[CourseConfig],
                     test:Callable[[CourseConfig], bool],
                     content:List[str], done:Set[CourseConfig]) -> None:
    """A checkpoint table"""
    for course in courses:
        if test(course):
            if course not in done:
                checkpoint_line(session, course, content)
                done.add(course)

async def checkpoint_list(request:Request) -> Response:
    """Page with all checkpoints"""
    session = await Session.get_or_fail(request)
    titles = '''<tr class="sticky2"><th>Session<th>Comp<br>iler
        <th>Title
        <th>Stud<br>ents<th>Wait<br>ing<th>Act<br>ives<th>With<br>me
        <th>Start date<th>Stop date<th>Duration<th>Options<th>Edit<th>👁<th>Waiting<br>Room
        <th>Creator<th>Admins<th>Graders<th>Proctors<th>Media</tr>'''
    content = [
        session.header(),
        f'''
        <script src="checkpoint_list.js?ticket={session.ticket}"></script>
        <link rel="stylesheet" href="checkpoint_list.css?ticket={session.ticket}">
        <div id="header"></div>
        <table>''']
    def hide_header():
        if '<th>' in content[-1]:
            content.pop()
            content[-1] = content[-1].replace('<th', '<th style="color:#AAF"')
    def add_header(label):
        hide_header()
        content.append('<tr class="sticky">')
        content.append(f'<th class="header" colspan="{titles.count("th")}">{label}</tr>')
        content.append(titles)
    now = time.time()
    courses = [
        course
        for course in sorted(CourseConfig.configs.values(),
            key=lambda i: i.course.split('=')[::-1])
        if session.is_proctor(course) or course.status('').startswith('running')
        ]
    done:Set[CourseConfig] = set()
    add_header("Drafts")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Draft' and session.is_admin(course),
        content, done)
    add_header("Sessions not yet started")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Ready' and now < course.start_timestamp,
        content, done)
    add_header("Sessions running")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Ready'
                       and course.start_timestamp <= now <= course.stop_tt_timestamp,
        content, done)
    add_header("Sessions finished (to move in «grade» or «done» tables)")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Ready' and now > course.stop_tt_timestamp,
        content, done)
    add_header("Sessions to grade")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Grade' and session.is_grader(course),
        content, done)
    add_header("Sessions done")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Done' and session.is_grader(course),
        content, done)
    add_header("Sessions archived")
    checkpoint_table(session, courses,
        lambda course: course.state == 'Archive' and session.is_admin(course),
        content, done)
    hide_header()
    content.append('</table>')
    if session.is_author():
        content.append("""<script>IS_AUTHOR=true;</script><p>
        <div>Download a Python file to add a new session for the compiler: """)
        for compiler in COMPILERS:
            content.append(f'''
            <form method="POST" enctype="multipart/form-data"
                  action="/upload_course/{compiler}/_new_?ticket={session.ticket}">
            <label>
            <input type="file" name="course" accept="text/x-python"
                   onchange="this.parentNode.parentNode.submit()">
            <span>{compiler}</span>
            </label>
            </form>''')
    if session.is_mapper():
        content.append('<p>Edit building map: ')
        for building in sorted(utilities.get_buildings()):
            content.append(f'''
            <button onclick="window.open(\'/adm/building/{building}?ticket={session.ticket}\')"
            >{building}</button>''')
    nr_doing_grading = 0
    now = time.time() - 5 * 60
    for course in courses:
        for _teacher, timestamp in course.doing_grading.items():
            if timestamp > now:
                nr_doing_grading += 1

    content.append(f'</div><script>init_interface({nr_doing_grading});</script>')
    content.append('<p><a href="/checkpoint/MAPS/*">Display building maps with hostnames</a>.')

    return answer(''.join(content))

async def checkpoint(request:Request) -> Response:
    """Display the map with students waiting checkpoint"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.exception('not_proctor')
    return answer(
        session.header() + f'''
        <script>
        SERVER_TIME = {time.time()};
        COURSE = {json.dumps(course.course)};
        STUDENTS = {json.dumps(await course.get_students())};
        MESSAGES = {json.dumps(course.messages)};
        OPTIONS = {json.dumps(course.config)};
        </script>
        <script src="checkpoint/BUILDINGS?ticket={session.ticket}"></script>
        <script src="checkpoint.js?ticket={session.ticket}"></script>
        <link rel="stylesheet" href="HIGHLIGHT/{course.theme}.css?ticket={session.ticket}">
        <script src="HIGHLIGHT/highlight.js?ticket={session.ticket}"></script>
        ''')

async def checkpoint_hosts(request:Request, real_course="=IPS") -> Response:
    """Display the unexpected IP in rooms"""
    session = await Session.get_or_fail(request)
    if session.is_student():
        raise session.exception('not_teacher')
    buildings = utilities.get_buildings()
    ips:Dict[str,Dict[str,int]] = collections.defaultdict(lambda: collections.defaultdict(int))
    if real_course == "=IPS":
        for course in utilities.CourseConfig.configs.values():
            if not course.checkpoint:
                continue
            await asyncio.sleep(0)
            for infos in course.active_teacher_room.values():
                where = infos.room.split(',')
                if len(where) < 3:
                    continue
                if where[0] in buildings:
                    ips[','.join(where[:3])][infos.hostname] += 1
    return answer(
        session.header() + f'''
        <script>
        COURSE = '{real_course}';
        STUDENTS = [];
        MESSAGES = [];
        OPTIONS = {json.dumps({"default_building": ""})};
        IPS = {json.dumps(ips)};
        SERVER_TIME = {time.time()};
        </script>
        <script src="checkpoint/BUILDINGS?ticket={session.ticket}"></script>
        <script src="checkpoint.js?ticket={session.ticket}"></script>
        ''')

async def checkpoint_maps(request:Request) -> Response:
    """The hostname maps"""
    return await checkpoint_hosts(request, real_course="=MAPS")

async def update_browser_data(course:CourseConfig) -> Response:
    """Send update values"""
    return answer(
        f'''
        STUDENTS = {json.dumps(await course.get_students())};
        MESSAGES = {json.dumps(course.messages)};
        CONFIG.computers = {json.dumps(utilities.CONFIG.computers)};
        ''',
        content_type='application/javascript')

async def checkpoint_student(request:Request) -> Response:
    """Display the students waiting checkpoint"""
    student = request.match_info['student']
    room = request.match_info['room']
    if room == 'STOP':
        # The student is allowed to stop the session
        allow = student
    else:
        allow = None
    session, course = await get_teacher_login_and_course(request, allow=allow)
    if allow is None and not session.is_proctor(course):
        return utilities.js_message('not_proctor')
    seconds = int(time.time())
    old = course.active_teacher_room[student]

    if room == 'STOP':
        course.set_parameter('active_teacher_room', 0, student, 0)
        to_log = f'#checkpoint_stop {session.login}'
    elif room == 'RESTART':
        course.set_parameter('active_teacher_room', 1, student, 0)
        course.set_parameter('active_teacher_room', session.login, student, 1)
        to_log = f'#checkpoint_restart {session.login}'
    elif room == 'EJECT':
        course.set_parameter('active_teacher_room', 0, student, 0)
        course.set_parameter('active_teacher_room', '', student, 1)
        course.set_parameter('active_teacher_room', '', student, 2)
        course.set_parameter('active_teacher_room', seconds, student, 3)
        to_log = f'#checkpoint_eject {session.login}'
    else:
        if old.teacher == '':
            # A moved STOPed student must not be reactivated
            course.set_parameter('active_teacher_room', 1, student, 0)
        course.set_parameter('active_teacher_room', session.login, student, 1)
        course.set_parameter('active_teacher_room', room, student, 2)
        to_log = f'#checkpoint_move {session.login} {room}'
    await JournalLink.new(course, student, None, None, False).write(to_log)
    if session.is_student() and not session.is_proctor(course):
        return utilities.js_message("C'est fini.")
    return await update_browser_data(course)

async def checkpoint_bonus(request:Request) -> Response:
    """Set student time bonus"""
    student = request.match_info['student']
    bonus = request.match_info['bonus']
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        return utilities.js_message("not_proctor")
    # Information is stored twice
    course.set_parameter('active_teacher_room', int(bonus), student, 7)
    await JournalLink.new(course, student, None, None, False).write(
        f'#bonus_time {bonus} {course.get_stop(student)}')
    return await update_browser_data(course)

async def home(request:Request) -> Response:
    """Test the user rights to display the good home page"""
    session = await Session.get_or_fail(request)
    if session.is_student():
        login = ''
    else:
        login = request.query.get('login', '')
    if not login:
        login = session.login
        if session.is_root():
            return await adm_root(request)
        if not session.is_student():
            return await checkpoint_list(request)
    # Student

    now = time.time()
    courses = sorted(CourseConfig.configs.items())
    data = []
    for _course_name, course in courses:
        expected = (login in course.expected_students
                    or login in course.tt_list)
        if course.expected_students_required and not expected:
            continue
        status = course.status(login)
        feedback = course.get_feedback(login)
        if status not in ('pending', 'running') and not feedback:
            continue
        if now < course.hide_before_seconds:
            continue # Too soon to display
        data.append((course.course, course.highlight, expected, feedback,
                     course.title, course.start_timestamp, course.stop_timestamp,
                     login in course.tt_list))
    return answer(f'''{session.header(login=login)}
<script src="home.js?ticket={session.ticket}"></script>
<script>home({json.dumps(data)}, {await utilities.LDAP.infos(login)})</script>
''')

async def checkpoint_buildings(request:Request) -> Response:
    """Building list"""
    _session = await Session.get(request)
    return answer(
        f'BUILDINGS = {json.dumps(utilities.get_buildings())};',
        content_type='application/javascript')

async def computer(request:Request) -> Response:
    """Set value for computer"""
    _session = await Session.get(request)
    course = CourseConfig.get(utilities.get_course(request.match_info['course']))
    message = request.match_info.get('message', '')
    building = request.match_info['building']
    column = int(request.match_info['column'])
    line = int(request.match_info['line'])
    if message:
        utilities.CONFIG.computers.append((building, column, line, message, int(time.time())))
    else:
        utilities.CONFIG.computers = utilities.CONFIG.config['computers'] = [
            bug
            for bug in utilities.CONFIG.computers
            if bug[0] != building or bug[1] != column or bug[2] != line
            ]
    utilities.CONFIG.set_value('computers', utilities.CONFIG.computers)
    return await update_browser_data(course)

async def checkpoint_message(request:Request) -> Response:
    """The last answer from the student"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        return utilities.js_message("not_proctor")
    course.set_parameter(
        'messages',
        [session.login, int(time.time()), request.match_info['message']],
        key='+'
        )
    return answer('')

async def get_course_config(request:Request) -> Tuple[Session,CourseConfig]:
    """Returns the session and the courses configuration"""
    course = request.match_info['course']
    if course.startswith('^'):
        session = await Session.get_or_fail(request)
        matches = []
        for config in CourseConfig.configs.values():
            if session.is_admin(config) and re.match(course, config.session):
                matches.append(config)
        if not matches:
            raise web.HTTPUnauthorized(body='no_matching_session')
        class FakeConfig(CourseConfig): # pylint: disable=too-few-public-methods
            """Config for a set of sessions defined by regular expression"""
            def __init__(self, **kargs): # pylint: disable=super-init-not-called
                self.__dict__.update(kargs)
            active_teacher_room = ()
        first = min(matches, key=lambda x: x.course)
        config = FakeConfig(
            session=first.session,
            course=course,
            config=dict(first.config))
    else:
        session, config = await get_teacher_login_and_course(request)
        if not session.is_admin(config):
            raise web.HTTPUnauthorized(body='not_admin')
    return session, config

async def course_config(request:Request) -> Response:
    """The last answer from the student"""
    _session, config = await get_course_config(request)

    return answer(
        f'update_course_config({json.dumps(config.config)})',
        content_type='application/javascript')

async def adm_history(request:Request) -> Response:
    """Plain history of session changes"""
    session, config = await get_course_config(request)
    if not session.is_admin(config):
        raise web.HTTPUnauthorized(body='not_admin')
    content = []
    for i, line in enumerate(pathlib.Path(config.file_cf).read_text(encoding='utf-8').split('\n')):
        if i % 100 == 0:
            await asyncio.sleep(0)
        if line.startswith("('active_teacher_room'"):
            continue
        if not line:
            continue
        date = line[-22:]
        if re.match(' # [-0-9: ]*', date):
            line = line[:-22]
        else:
            date = ' # ????-??-?? ??:??:??'
        content.append(date[3:] + ' ' + line)
    return answer('\n'.join(content[::-1]), content_type="text/plain")

async def adm_session(request:Request) -> Response:
    """Session configuration for administrators"""
    session, config = await get_course_config(request)
    students = {login: await utilities.LDAP.infos(login)
                for login in config.active_teacher_room
               }
    return answer(
        session.header()
        + f'''
        <script>
        COURSE = {json.dumps(config.course)};
        BUILDINGS = {json.dumps(sorted(os.listdir('BUILDINGS')))};
        STUDENTS = {json.dumps(students)};
        </script>
        <script src="adm_session.js?ticket={session.ticket}"></script>''')

async def adm_editor(request:Request) -> Response:
    """Session questions editor"""
    session, course = await get_teacher_login_and_course(request)
    is_admin = session.is_admin(course)
    if not is_admin:
        return answer("Vous n'êtes pas autorisé à modifier les questions.")
    return await editor(session, is_admin, course, 'PYTHON=editor')

async def get_media(request:Request) -> Response:
    """Get a media file"""
    session = await Session.get_or_fail(request)
    course = CourseConfig.get(utilities.get_course(request.match_info['course']))
    if not session.is_grader(course) and not course.status(session.login).startswith('running'):
        return answer('Not allowed', content_type='text/plain')
    return File.get(f'{course.dir_media}/{request.match_info["value"]}').answer()

async def adm_building(request:Request) -> Response:
    """Get building editor"""
    session = await Session.get_or_fail(request)
    if not session.is_mapper():
        return session.message('not_mapper')
    building = request.match_info['building']
    with open(f'BUILDINGS/{building}', 'r', encoding="utf-8") as file:
        content = file.read()
    width = max(len(line) for line in content.split('\n')) + 1
    return answer(f'''{session.header()}
    <title>{building}</title>
    <form action="/adm/building/{building}?ticket={session.ticket}" method="POST">
    <input type="submit">
    <b>Legend</b> <span style="font-family: emoji">
    |-+:walls d:doors w:window s→💻 c→⑁ p→🖨 r→🚻 l→↕ h→♿ g→📝 a→Ⓐ b→Ⓑ</span><br>
    <textarea cols={width} spellcheck="false" style="height:calc(100vh - 5em)"
     name="map">{content}</textarea></form>''')

async def adm_building_store(request:Request) -> Response:
    """Store a building map"""
    session = await Session.get_or_fail(request)
    if not session.is_mapper():
        return session.message('not_mapper')
    building = request.match_info['building']
    post = await request.post()
    with open(f'BUILDINGS/{building}', 'w', encoding="utf-8") as file:
        file.write(str(post['map']).replace('\r', ''))
    utilities.get_buildings.time = 0 # Erase building cache
    return answer(f'«{building}» map recorded.')

async def write_lines(stream, lines):
    """Put CSV lines on stream"""
    if lines:
        output = io.StringIO()
        csv.writer(output).writerows(lines)
        await stream.write(output.getvalue().encode('utf-8'))

async def js_errors(request:Request) -> Response:
    """Display javascript errors"""
    # pylint: disable=too-many-branches,too-many-nested-blocks
    session = await Session.get_or_fail(request)
    if not session.is_root():
        return session.message('not_root')
    stream = web.StreamResponse()
    stream.content_type = 'text/plain'
    await stream.prepare(request)
    process = await asyncio.create_subprocess_exec(
        'awk', '/     ERROR / { if ($0 != P && $0 != Q) { print($0) ; Q=P ; P=$0 ;} }',
        *sorted(glob.glob('LOGS/*-http_server'), reverse=True),
        stdout=asyncio.subprocess.PIPE,
        )
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        await stream.write(line)
    process.terminate()
    return stream


async def journal(request:Request) -> StreamResponse:
    """Get a file or a ZIP"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.exception('not_proctor')
    stream = StreamResponse()
    await stream.prepare(request)
    course.streams.append(stream)
    while stream in tuple(course.streams):
        await asyncio.sleep(60)
        try:
            await stream.write(b'\n')
            await stream.drain()
        except ConnectionResetError:
            try:
                course.streams.remove(stream)
            except ValueError:
                pass
    return stream

async def record_feedback(request:Request) -> Response:
    """Record feedback status"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_grader(course)
    if not is_grader:
        return answer("Vous n'êtes pas autorisé à noter.")
    student = request.match_info['student']
    feedback = int(request.match_info['feedback'])
    course.set_parameter('active_teacher_room', feedback, student, 10)
    return answer(f"window.update_feedback({feedback})")

async def error(request:Request) -> Response:
    """Record errors"""
    session = await Session.get_or_fail(request)
    course = request.match_info['course']
    post = await request.post()
    data = str(post['data'])
    log(f'ERROR {session.login} {course} {data}')
    return answer('console.log("error recorded")')

async def change_session_ip(request:Request) -> Response:
    """Change the current session IP"""
    session = await Session.get_or_fail(request)
    session.client_ip += '*'
    return answer('done')

async def full_stats(request:Request) -> Response:
    """All session stats"""
    session = await Session.get_or_fail(request) # await get_author_login(request)
    with open('xxx-full-stats.js', 'r', encoding='utf-8') as file:
        data = file.read()
    return answer(f'''<!DOCTYPE html>
    <title>STATS</title>
    <script>STATS = {data}</script>
    <link REL="icon" href="favicon.ico?ticket={session.ticket}">
    <div id="header"></div>
    <div id="top"></div>
    <script src="stats.js?ticket={session.ticket}"></script>
    ''')

class JournalLink: # pylint: disable=too-many-instance-attributes
    """To synchronize multiple connections to the same student session"""
    journals:Dict[Tuple[str,str],"JournalLink"] = {} # Key is (session, login)

    def __init__(self, course, login, is_editor):
        self.login = login
        self.course = course
        self.editor = is_editor
        if is_editor:
            dirname = f'{self.course.dir_session}'
        else:
            dirname = f'{self.course.dir_log}/{login}'
        if not os.path.exists(dirname):
            if not os.path.exists(self.course.dir_log):
                os.mkdir(self.course.dir_log)
            os.mkdir(dirname)
        self.path = pathlib.Path(dirname + '/journal.log')
        if is_editor and not self.path.exists():
            content = pathlib.Path(course.file_py).read_text(encoding='utf-8')
            content = content.replace('\n', '\0')
            self.path.write_text(f'Q0\nI{content}\ntI\n', encoding='utf-8')
        if self.path.exists():
            content = self.path.read_text(encoding='utf-8')
            if content:
                self.content = content.split('\n')
                self.content.pop() # Empty string
            else:
                self.content = []
        else:
            self.content = []
        self.journal = self.path.open('a', encoding='utf-8')
        self.msg_id = str(len(self.content))
        self.connections = [] # List of Socket, port of connected browsers
        self.locked = False
        self.last_set_parameter = 0
        self.last_blur = None

    async def __aenter__(self):
        """Lock the JournalLink instance"""
        while self.locked:
            await asyncio.sleep(0)
        self.locked = True

    async def __aexit__(self, *_args):
        """Unock the JournalLink instance"""
        self.locked = False

    async def write(self, message):
        """Append an action to the journal.
              * update the session state (blurring, activity).
              * update the journal.log of the student.
              * update the JournalLink content.
              * Synchronize all the connected users
        """
        # pylint: disable=too-many-branches,too-many-nested-blocks
        # XXX Must check message validity and add timestamp
        self.content.append(message)
        # 'protect_crlf' does not work in some browser.
        # So redo it server side.
        self.journal.write(common.protect_crlf(message) + '\n')

        if self.editor:
            if message.startswith('t'):
                os.rename(self.course.file_py, self.course.file_py + '~')
                with open(self.course.file_py, 'w', encoding="utf-8") as file:
                    file.write(common.Journal('\n'.join(self.content)).content)
                with os.popen(f'make {self.course.file_js} 2>&1', 'r') as file:
                    errors = file.read()
                if 'ERROR' in errors or 'FAIL' in errors:
                    os.rename(self.course.file_py + '~', self.course.file_py)
        elif self.login in self.course.active_teacher_room:
            infos = self.course.active_teacher_room[self.login]
            infos.last_time = int(time.time())
            if message.startswith('B'):
                self.last_blur = infos.last_time
                self.course.set_parameter(
                    'active_teacher_room', infos.nr_blurs + 1, self.login, 4)
            elif message.startswith('F'):
                if self.last_blur is None:
                    # Here to not compute last_blur if not an exam session.
                    # Needed only when student close and reopen tab,
                    # because JournalLink is recreated and last_blur lost.
                    last_blur_found = False
                    for line in self.content[::-1]:
                        if last_blur_found:
                            if line.startswith('T'):
                                self.last_blur = int(line[1:])
                                break
                        elif line.startswith('B'):
                            last_blur_found = True
                if self.last_blur:
                    # Duration must change to indicate Focus to checkpoint window
                    duration = max(infos.last_time - self.last_blur, 1)
                    self.course.set_parameter(
                        'active_teacher_room', infos.blur_time + duration, self.login, 9)
                    self.last_blur = 0 # Needed if 2 Focus without Blur (should not happen)
            elif message.startswith('g'):
                self.course.set_parameter(
                    'active_teacher_room', infos.nr_answers + 1, self.login, 5)
            elif infos.last_time - self.last_set_parameter > 60:
                self.course.set_parameter('active_teacher_room', infos.last_time, self.login, 3)
                self.last_set_parameter = infos.last_time

        message = self.msg_id + ' ' + message
        self.journal.flush()
        self.msg_id = str(len(self.content))
        async with self: # Locked to garantee the order of events
            for socket, port in self.connections:
                try:
                    await socket.send_str(f'{port} {message}')
                except: # pylint: disable=bare-except
                    JournalLink.closed_socket(socket)

    def close(self, socket, port=None):
        """Close all the connection or the connection of the indicated port."""
        # Remove socket/port from the list
        self.connections = [connection
                            for connection in self.connections
                            if connection[0] is not socket
                               or port is not None and connection[1] != port
                            ]
        if not self.connections:
            JournalLink.journals.pop((self.course.course, self.login))

    @classmethod
    def new(cls, course, login, socket, port, is_editor): # pylint: disable=too-many-arguments
        """JournalLink is common to all the user connected to the session
        in order to synchronize their screens."""
        if is_editor:
            login = ''
        journa = JournalLink.journals.get((course.course, login), None)
        if not journa:
            journa = JournalLink(course, login, is_editor)
            JournalLink.journals[course.course, login] = journa
        if socket is not None:
            journa.connections.append((socket, port))
        return journa

    @classmethod
    def closed_socket(cls, socket):
        """Close socket (shared worker stop), so all the ports using this socket)"""
        # tuple() because journals may be removed while looping.
        for journa in tuple(JournalLink.journals.values()):
            journa.close(socket)

    @classmethod
    def close_all_sockets(cls):
        """Only called on server stop"""
        log("JournalLink.close_all_sockets()")
        for journa in JournalLink.journals.values():
            for socket, _port in journa.connections:
                try:
                    socket._writer.transport.close() # pylint: disable=protected-access
                except IOError:
                    pass
        log("JournalLink.close_all_socket() done")

    def erase_comment_history(self, bubble_id):
        """Replace old comment text by ?????? without changing its size
        in order to not rewrite the file.
        So the students can't see old comments"""
        j = common.Journal('\n'.join(self.content) + '\n')
        last_comment_change = j.bubbles[bubble_id].last_comment_change
        if last_comment_change is None:
            return # First comment
        old_comment = common.protect_crlf(j.bubbles[bubble_id].comment)
        assert j.lines[last_comment_change] == f'bC{bubble_id} {old_comment}'
        file_position = len('\n'.join(j.lines[:last_comment_change]).encode("utf-8")) + 1
        new_line = f'bC{bubble_id} {"?"*len(old_comment.encode("utf-8"))}'
        self.content[last_comment_change] = new_line
        with open(self.path, 'r+', encoding='utf-8') as file:
            file.seek(file_position, 0)
            file.write(new_line)
        log(f'Erase bubble_id={bubble_id} position={file_position} '
            f'old_content={j.lines[j.bubbles[bubble_id].last_comment_change]}')

async def live_link(request:Request) -> StreamResponse:
    """Live link beetween the browser and the server.
    It is an uniq link for all the opened tabs.

    For the editor, it receives:
       all student actions: cursor move, scroll, keys, question change...
       It stores these in the session/login journal.
       And dispatch change to the others

    Protocol is defined in «live_link.py»
    """
    # pylint: disable=too-many-branches,too-many-statements
    session = await Session.get_or_fail(request)
    socket = web.WebSocketResponse()
    try:
        await socket.prepare(request)
    except:
        log('bug')
        traceback.print_exc()
        raise

    journals:Dict[int,JournalLink] = {}

    async for msg in socket:
        if msg.type == WSMsgType.ERROR:
            log(f'socket connection closed with exception {socket.exception()}')
            break
        if msg.type != WSMsgType.TEXT:
            log(f'Type {msg.type}')
            break
        port, message = msg.data.split(' ', 1)
        journa, allow_edit = journals.get(port, (None, True))
        # log(f'{port} {message} {journa} {len(journa.msg_id) if journa else "?"} {allow_edit}')
        if journa and session.login != journa.login:
            log(f'{session.is_grader(journa.course)} {message.split(" ", 1)[1]}')
            if not allow_edit:
                if not session.is_grader(journa.course) or not message.split(' ', 1)[1][0] in 'bGTtLH':
                    continue
            # Allow grader comments
        if message == '-':
            if journa:
                journa.close(socket, port)
            else:
                log(f'Message «{msg.data}» close but no journal. bug={port in journals}')
            journals.pop(port, None)
        elif journa:
            msg_id, message = message.split(' ', 1)
            if msg_id == journa.msg_id:
                if not journa.course.running(session.login):
                    journa.close(socket, port)
                    continue
                if message.startswith('#'):
                    log(f'Not allowed via web interface «{message}»')
                elif message.startswith('b+') and not message.startswith(f'b+{session.login}'):
                    log(f'Hacker «{message}»')
                else:
                    if message.startswith('bC'):
                        journa.erase_comment_history(int(message[2:].split(' ')[0]))
                    await journa.write(message)
            else:
                log(f'{journa.msg_id} != {msg_id}  for  {message}')
        else:
            assert port not in journals
            session_name, asked_login = message.split(' ', 1)
            course = CourseConfig.get(utilities.get_course(session_name))
            allow_edit = asked_login == session.login or session.is_grader(course)
            if asked_login and session.is_proctor(course):
                login = asked_login
            else:
                login = session.login
            for_editor = login.startswith('_FOR_EDITOR_')
            if for_editor:
                login = login.replace('_FOR_EDITOR_', '')
                asked_login = asked_login.replace('_FOR_EDITOR_', '')
                if session.is_admin(course):
                    allow_edit = True
                else:
                    login = session.login
            journa = JournalLink.new(course, asked_login, socket, port, for_editor)
            journals[port] = [journa, allow_edit]
            await socket.send_str(
                port + ' J' + '\n'.join(journa.content) + '\n')
            if allow_edit:
                await journa.write(f'T{int(time.time())}')
                await journa.write(f'O{session.login} {session.client_ip} {port}')
            # log(f'New journalLink {asked_login}/{login} {for_editor} msg_id:{journa.msg_id}')
    JournalLink.closed_socket(socket)
    log(f'WebSocket close: {id(socket)} {socket}')

def log(message):
    """Formatte http_server messages (same beginning than aiohttp messages)"""
    print(f'{time.strftime("%Y-%m-%d %H:%M:%S")}     {message}', flush=True)

def main():
    """Run http server"""
    # Check if an upgrade is needed
    for filename in glob.glob('COMPILE_*/*/LOGS/*/http_server.log'):
        translation = filename.replace('http_server', 'journal')
        if os.path.exists(translation):
            break
        log('='*60)
        log('YOU MUST RUN « ./upgrade_logs.py »')
        log('TO TRANSLATE ALL «http_server.log»+«comments.log» to «journal.log»')
        log('='*60)
        sys.exit(1)

    app = web.Application()
    app.add_routes([web.get('/', home),
                    web.get('/{filename}', handle()),
                    web.get('/{filename}/V{version}', handle()),
                    web.get('/node_modules/{filename:.*}', handle('node_modules')),
                    web.get('/HIGHLIGHT/{filename:.*}', handle('HIGHLIGHT')),
                    web.get('/adm/get/{filename:.*}', adm_get),
                    web.get('/adm/get_exclude/{exclude}/{filename:.*}', adm_get),
                    web.get('/adm/answers/{course}/{students}/{filename:.*}', adm_answers),
                    web.get('/adm/root', adm_root),
                    web.get('/adm/session/{course}', adm_session), # Edit page
                    web.get('/adm/session2/{course}/{action}/{value}', adm_config),
                    web.get('/adm/session2/{course}/{action}', adm_config),
                    web.get('/adm/course/{course}', adm_course),
                    web.get('/adm/history/{course}', adm_history),
                    web.get('/adm/git_pull/{course}', adm_git_pull),
                    web.get('/adm/force_grading_done/{course}', adm_force_grading_done),
                    web.get('/adm/media/{course}/{action}/{media}', adm_media),
                    web.get('/adm/editor/{course}', adm_editor),
                    web.get('/adm/js_errors', js_errors),
                    web.get('/adm/building/{building}', adm_building),
                    web.get('/config/reload', config_reload),
                    web.get('/course_config/{course}', course_config),
                    web.get('/checkpoint/*', checkpoint_list),
                    web.get('/checkpoint/*/{filter:.*}', checkpoint_list),
                    web.get('/checkpoint/BUILDINGS', checkpoint_buildings),
                    web.get('/checkpoint/{course}', checkpoint),
                    web.get('/checkpoint/MESSAGE/{course}/{message:.*}', checkpoint_message),
                    web.get('/checkpoint/TIME_BONUS/{course}/{student}/{bonus}', checkpoint_bonus),
                    web.get('/checkpoint/HOSTS/*', checkpoint_hosts),
                    web.get('/checkpoint/MAPS/*', checkpoint_maps),
                    web.get('/checkpoint/{course}/{student}/{room}', checkpoint_student),
                    web.get('/journal/{course}', journal),
                    web.get('/computer/{course}/{building}/{column}/{line}/{message:.*}', computer),
                    web.get('/computer/{course}/{building}/{column}/{line}', computer),
                    web.get('/record_feedback/{course}/{student}/{feedback}', record_feedback),
                    web.get('/grade/{course}/{login}', grade),
                    web.get('/zip/{course}', my_zip),
                    web.get('/git/{course}', my_git),
                    web.get('/media/{course}/{value}', get_media),
                    web.get('/debug/change_session_ip', change_session_ip),
                    web.get('/stats/{param}', full_stats),
                    web.get('/live_link/session', live_link),
                    web.post('/error/{course}', error),
                    web.post('/upload_course/{compiler}/{course}', upload_course),
                    web.post('/upload_media/{compiler}/{course}', upload_media),
                    web.post('/record_grade/{course}', record_grade),
                    web.post('/adm/c5/{action}', adm_c5),
                    web.post('/adm/building/{building}', adm_building_store),
                    web.post('/adm/session/{course}/{action}', adm_config),
                    ])
    app.on_startup.append(startup)
    logging.basicConfig(level=logging.DEBUG)

    class AccessLogger(AbstractAccessLogger): # pylint: disable=too-few-public-methods
        """Logger for aiohttp"""
        def log(self, request, response, rtime): # pylint: disable=redefined-outer-name
            path = request.path.replace('\n', '\\n')
            session = Session.session_cache.get(
                request.query_string.replace('ticket=', ''), None)
            if session:
                login = session.login
            else:
                login = ''
            print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {response.status} "
                f"{rtime:5.3f} {request.method[0]} "
                f"{request.query_string.replace('ticket=ST-', '').split('-')[0]} "
                f"{login} "
                f"{path}",
                flush=True)

    web.run_app(app, host=utilities.C5_IP, port=utilities.C5_HTTP,
                access_log_format="%t %s %D %r", access_log_class=AccessLogger,
                ssl_context=utilities.get_certificate(False))

if __name__ == '__main__':
    main()
