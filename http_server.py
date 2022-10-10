#!/usr/bin/python3
"""
Simple web server with session management
"""

import os
import time
import json
import collections
import tempfile
import zipfile
import asyncio
import logging
import ast
import urllib.request
from aiohttp import web
from aiohttp.abc import AbstractAccessLogger
import utilities

# To make casauth work we should not use a proxy
for i in ('http_proxy', 'https_proxy'):
    if i in os.environ:
        del os.environ[i]

class File:
    """Manage file answer"""
    file_cache = {}

    def __init__(self, filename):
        self.filename = filename
        self.mtime = 0
        self.content = ''
        if '/.' in filename:
            raise ValueError('Hacker')
        self.charset = 'utf-8'
        if filename.endswith('.html'):
            self.mime = 'text/html'
        elif filename.endswith('.js'):
            self.mime = 'application/x-javascript'
        elif filename.endswith('.ico'):
            self.mime = 'image/vnd.microsoft.icon'
            self.charset = None
        elif filename.endswith('.css'):
            self.mime = 'text/css'
        else:
            print('Unknow mimetype', filename)
            self.mime = 'text/plain'
    def get_content(self):
        """Check file date and returns content"""
        mtime = os.path.getmtime(self.filename)
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.filename, "rb") as file:
                content = file.read()
                if self.charset is not None:
                    content = content.decode(self.charset)
                self.content = content
        return self.content
    def response(self, content=''):
        """Get the response to send"""
        return web.Response(
            body=content or self.get_content(),
            content_type=self.mime,
            charset=self.charset,
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                'Cache-Control': 'no-cache',
                # 'Cache-Control': 'max-age=60',
            }
        )
    @classmethod
    def get(cls, filename):
        """Get or create File object"""
        if filename not in cls.file_cache:
            cls.file_cache[filename] = File(filename)
        return cls.file_cache[filename]

def handle(base=''):
    """Send the file content"""
    async def real_handle(request): # pylint: disable=too-many-branches
        if base:
            session = None # Not authenticated
        else:
            session = await utilities.Session.get(request)
            login = await session.get_login(str(request.url).split('?')[0])
        filename = request.match_info['filename']
        course = None
        if base:
            assert '/.' not in filename
            filename = base + '/' + filename
        else:
            if filename.startswith("="):
                course = utilities.CourseConfig.get(utilities.get_course(filename[1:]))
                if not course.dirname:
                    return session.message('unknown')
                answers, _blurs = get_answers(course.dirname, session.login, saved=True)
                for key, value in answers.items():
                    for _source, answer, _time in value:
                        if answer == 1:
                            value[-1][1] = 1 # Correct answer even if changed after
                            break
                    answers[key] = value[-1] # Only the last answer
                status = course.status(login, session.client_ip)
                if course:
                    stop = course.get_stop(session.login)
                else:
                    stop = ''
                if not session.is_admin():
                    if status == 'done':
                        return session.message('done')
                    if status == 'pending':
                        return session.message('pending')
                    if status == 'checkpoint':
                        return session.message('checkpoint')
                return File.get('ccccc.html').response(
                    session.header() + f'''
                    <title>{course.course.split('=', 1)[1]}</title>
                    <link rel="stylesheet" href="/HIGHLIGHT/{course.theme}.css?ticket={session.ticket}">
                    <link rel="stylesheet" href="/ccccc.css?ticket={session.ticket}">
                    <script src="/HIGHLIGHT/highlight.js?ticket={session.ticket}"></script>
                    <script>
                        SOCK = "wss://{utilities.C5_WEBSOCKET}";
                        ADMIN = "{int(session.is_admin())}";
                        STOP = "{stop}";
                        CP = {course.config['copy_paste']};
                        SAVE_UNLOCK = {int(course.config['save_unlock'])};
                        SEQUENTIAL = {int(course.config['sequential'])};
                        INFOS = {json.dumps(session.infos)};
                        CHECKPOINT = {course.checkpoint};
                        ANSWERS = {json.dumps(answers)};
                        WHERE = {json.dumps(course.active_teacher_room.get(login,(False,'?','?,0,0',0,0,0,'ip',0)))};
                    </script>
                    <script src="/ccccc.js?ticket={session.ticket}"></script>''')
            if '=' in filename:
                course = utilities.CourseConfig.get(utilities.get_course(filename))
                filename = course.filename.replace('.cf', '.js')
                status = course.status(login, session.client_ip)
                if not session.is_admin() and not status.startswith('running'):
                    return session.message('done')
        return File.get(filename).response()
    return real_handle

async def log(request):
    """Log user actions"""
    session = await utilities.Session.get(request)
    post = await request.post()
    course = utilities.CourseConfig.get(utilities.get_course(post['course']))
    if not course.running(session.login, session.client_ip):
        return web.Response(
            body=r"""<!DOCTYPE html>
            <script>
            alert("Ce que vous faites n'est plus enregistré :\n"
                  + "  * L'examen est terminé\n"
                  + "  * ou bien votre adresse IP a changé !\n"
                  + "Contactez l'enseignant."
                 )
            </script>""",
            content_type="text/html",
            charset='utf-8',
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                'Cache-Control': 'no-cache',
                # 'Cache-Control': 'max-age=60',
            }
        )
    data = urllib.request.unquote(post['line'])
    # Must do sanity check on logged data
    try:
        json.loads(data)
        bad_json = 0
    except: # pylint: disable=bare-except
        bad_json = 10
    if bad_json:
        utilities.student_log(
            course.dirname, session.login, json.dumps([int(time.time()), ["HACK", data]]))
    else:
        utilities.student_log(course.dirname, session.login, data)

    if session.login in course.active_teacher_room:
        infos = course.active_teacher_room[session.login]
        infos[3] = int(time.time())
        infos[4] += data.count('"Blur"') + bad_json
        infos[5] += data.count('["answer",')

    return web.Response(
        body="<!DOCTYPE html>\n<script>window.parent.ccccc.record_done()</script>",
        content_type="text/html",
        charset='utf-8',
        headers={
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Embedder-Policy": "require-corp",
            'Cache-Control': 'no-cache',
        }
    )

async def load_student_infos():
    """Load all student info in order to answer quickly"""
    utilities.CourseConfig.load_all_configs()
    for config in utilities.CourseConfig.configs.values():
        for login in config.active_teacher_room:
            await utilities.LDAP.infos(login)

async def startup(app):
    """For student names and computer names"""
    app['ldap'] = asyncio.create_task(utilities.LDAP.start())
    app['dns'] = asyncio.create_task(utilities.DNS.start())
    app['load_student_infos'] = asyncio.create_task(load_student_infos())
    print("DATE HOUR STATUS TIME METHOD(POST/GET) TICKET/URL")

async def get_admin_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    if not session.is_admin():
        raise session.message('not_admin', exception=True)
    return session

async def get_teacher_login_and_course(request, allow=None):
    """Get the teacher login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    course = utilities.CourseConfig.get(utilities.get_course(request.match_info['course']))
    if session.is_student() and allow != session.login:
        raise session.message('not_teacher', exception=True)
    # if session.login not in course.teachers:
    #     raise session.message('not_teacher', exception=True)
    return session, course

async def adm_course(request):
    """Course details page for administrators"""
    session, course = await get_teacher_login_and_course(request)
    students = {}
    for user in sorted(os.listdir(course.dirname)):
        await asyncio.sleep(0)
        files = []
        students[user] = student = {'files': files}
        for filename in sorted(os.listdir(f'{course.dirname}/{user}')):
            if '.' in filename:
                # To not display executables
                files.append(filename)
        try:
            student['status'] = course.status(user)
            with open(f'{course.dirname}/{user}/http_server.log') as file:
                student['http_server'] = file.read()
        except IOError:
            pass

    return web.Response(
        body=session.header() + f"""
            <script>
            STUDENTS = {json.dumps(students)};
            COURSE = '{course.course}';
            </script>
            <script src="/adm_course.js?ticket={session.ticket}"></script>
            """,
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def adm_config(request): # pylint: disable=too-many-branches
    """Course details page for administrators"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    config = utilities.CourseConfig.get(utilities.get_course(course))
    action = request.match_info['action']
    value = request.match_info.get('value', '')
    if value == 'now':
        value = time.strftime('%Y-%m-%d %H:%M:%S')
    if action == 'stop':
        config.set_parameter('stop', value)
        if config.start > value:
            config.set_parameter('start', value)
        feedback = f"«{course}» Stop date updated to «{value}"
    elif action == 'start':
        config.set_parameter('start', value)
        config.set_parameter('stop', '2100-01-01 00:00:00')
        feedback = f"«{course}» Start date updated to «{value}»"
    elif action == 'tt':
        config.set_parameter('tt', value)
        feedback = f"«{course}» TT list updated with «{value}»"
    elif action == 'teachers':
        config.set_parameter('teachers', value)
        feedback = f"«{course}» Teachers list updated with «{value}»"
    elif action == 'theme':
        if os.path.exists(f'HIGHLIGHT/{value}.css'):
            config.set_parameter('theme', value)
            feedback = f"«{course}» Highlight theme updated to «{value}»"
        else:
            feedback = f"«{course}» Highlight theme «{value}» does not exists"
    elif action == 'copy_paste':
        config.set_parameter('copy_paste', value)
        feedback = f"«{course}» Copy Paste «{'not' if value == '0' else ''} allowed»"
    elif action == 'save_unlock':
        config.set_parameter('save_unlock', value)
        feedback = f"«{course}» Unlock next question on save «{'not' if value == '0' else ''} allowed»"
    elif action == 'checkpoint':
        config.set_parameter('checkpoint', value)
        if value == '0':
            feedback = f"«{course}» Automatic access to the session"
        else:
            feedback = f"«{course}» Need teacher approval to start"
    elif action == 'sequential':
        config.set_parameter('sequential', value)
        if value == '0':
            feedback = f"«{course}» All questions are accessible in a random order."
        else:
            feedback = f"«{course}» Questions are accessible only if the previous are corrects."
    elif action == 'highlight':
        config.set_parameter('highlight', value)
        if value == '0':
            feedback = f"«{course}» The session is no more highlighted in the student list"
        else:
            feedback = f"«{course}» The session (even in the future) is displayed in green to the student session list."
    elif action == 'delete':
        if not os.path.exists('Trash'):
            os.mkdir('Trash')
        dirname, filename = config.dirname.split('/')
        dirname = f"Trash/{dirname}"
        if not os.path.exists(dirname):
            os.mkdir(dirname)
        for extension in ('', '.cf', '.py', '.js'):
            if os.path.exists(config.dirname + extension):
                os.rename(config.dirname + extension, f'{dirname}/{filename}{extension}')
        del utilities.CourseConfig.configs[config.dirname]
        feedback = f"«{course}» moved to Trash directory."

    return await adm_home(request, feedback)

def text_to_dict(text):
    """Transform a user text to a dict.
             key1 value1
             key2 value2
        Become: {'key1': 'value1', 'key2': 'value2'}
    """
    dictionary = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            key, value = line.split(' ', 1)
            dictionary[key] = value
    return dictionary

async def adm_c5(request): # pylint: disable=too-many-branches
    """Remove a C5 master"""
    _session = await get_admin_login(request)
    action = request.match_info['action']
    value = request.match_info['value']
    more = "Nothing to do"
    if action == 'add_master':
        if value not in utilities.CONFIG.masters:
            utilities.CONFIG.masters.append(value)
            utilities.CONFIG.set_value('masters', utilities.CONFIG.masters)
            more = f"Master «{value}» added"
    elif action == 'del_master':
        if value in utilities.CONFIG.masters:
            utilities.CONFIG.masters.remove(value)
            utilities.CONFIG.set_value('masters', utilities.CONFIG.masters)
            more = f"Master «{value}» removed"
    elif action == 'ips_per_room':
        try:
            utilities.CONFIG.set_value(action, text_to_dict(value))
            more = f"IPs per room updated to<pre>{value}</pre>"
        except ValueError:
            more = "Invalid syntax!"
    elif action == 'messages':
        try:
            utilities.CONFIG.set_value(action, text_to_dict(value))
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
            session = utilities.Session.load_ticket_file(ticket)
            if session.too_old():
                nr_deleted += 1
        more = f"{nr_deleted} tickets deleted."
    else:
        more = "You are a hacker!"
    return await adm_home(request, more)

async def adm_home(request, more=''):
    """Home page for administrators"""
    if more:
        if more.endswith('!'):
            more = '<div id="more" style="background: #F88">' + more + '</div>'
        else:
            more = '<div id="more">' + more + '</div>'

    utilities.CourseConfig.load_all_configs()
    session = await get_admin_login(request)
    courses = []
    for _course_name, config in sorted(utilities.CourseConfig.configs.items()):
        attrs = {
            'course': config.course,
            'status': config.status(''),
            'logs': os.path.exists(config.dirname),
        }
        attrs.update(config.config)
        attrs.pop('active_teacher_room')
        attrs.pop('messages')
        courses.append(attrs)

    return web.Response(
        body=session.header(courses, more)
        + f'<script src="/adm_home.js?ticket={session.ticket}"></script>',
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def adm_get(request):
    """Get a file or a ZIP"""
    _session = await get_admin_login(request)
    filename = request.match_info['filename']
    if '/.' in filename:
        content = 'Hacker'
    else:
        if filename.endswith('.zip'):
            response = web.StreamResponse()
            response.content_type = 'application/zip'
            await response.prepare(request)
            course = filename[:-4]
            process = await asyncio.create_subprocess_exec(
                'zip', '-r', '-', course, course + '.py', course + '.cf',
                stdout=asyncio.subprocess.PIPE,
                )
            data = 'Go!'
            while data:
                data = await process.stdout.read(64 * 1024)
                await response.write(data)
            return response
        with open(filename, 'r') as file:
            content = file.read()
    return web.Response(
        body=content,
        content_type='text/plain',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

def get_answers(course, user, saved=False):
    """Get question answers"""
    answers = collections.defaultdict(list)
    blurs = collections.defaultdict(int)
    try:
        with open(f'{course}/{user}/http_server.log') as file:
            question = 0
            for line in file:
                line = line.strip()
                if line:
                    seconds = 0
                    for cell in json.loads(line):
                        if isinstance(cell, list):
                            what = cell[0]
                            if what == 'answer':
                                answers[cell[1]].append([cell[2], 1, seconds])
                            elif what == 'question':
                                question = cell[1]
                            elif saved and what == 'save':
                                answers[cell[1]].append([cell[2], 0, seconds])
                        elif isinstance(cell, str):
                            if cell == 'Blur':
                                blurs[question] += 1
                        else:
                            seconds += cell
    except IOError:
        return {}, {}
    return answers, blurs


def get_compiled(course, student):
    """Returns a dict with last version of each compiled question"""
    d = {}
    try:
        with open(f'{course.dirname}/{student}/compile_server.log') as file:
            for line in file:
                if "('COMPILE'," in line:
                    line = ast.literal_eval(line)
                    d[line[2][1][1]] = [line[0], line[2][1][6]]
    except (IndexError, FileNotFoundError):
        pass
    return d

async def adm_answers(request):
    """Get students answers"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    saved = int(request.match_info['saved'])
    assert '/.' not in course and course.endswith('.zip')
    course = utilities.get_course(course[:-4])
    config = utilities.CourseConfig(course)
    fildes, filename = tempfile.mkstemp()
    if course.startswith('SQL'):
        comment = '-- '
    elif course.startswith('PYTHON'):
        comment = '# '
    else:
        comment = '// '
    try:
        zipper = zipfile.ZipFile(os.fdopen(fildes, "wb"), mode="w")
        for user in sorted(os.listdir(course)):
            await asyncio.sleep(0)
            answers, blurs = get_answers(course, user, saved)
            compiled = get_compiled(config, user)
            if answers:
                infos = config.active_teacher_room.get(user)
                building, pos_x, pos_y, version = ((infos[2] or '?') + ',?,?,?').split(',')[:4]
                version = version.upper()
                where = f'Surveillant: {infos[1]}, {building} {pos_x}×{pos_y}, Version: {version}'
                zipper.writestr(
                    f'{course}/{user}#answers',
                    ''.join(f"""
{comment} ##################################################################
{comment} {where}
{comment} {f'Nombre de pertes de focus : {blurs[question]}' if blurs[question] else ''}
{comment} {user}     Question {question+1}   Good {answer[1]}
{comment} Date sauvegarde : {time.ctime(answer[2])}
{comment} ##################################################################

{answer[0]}

{
 f'''{comment} --------------------------------------------------------------
{comment} Date compilation : {time.ctime(compiled[question][0])}
{comment} --------------------------------------------------------------

{compiled[question][1]}
 '''
 if question in compiled
    and compiled[question][0] > answer[2]
    and compiled[question][1].strip() != answer[0].strip()
 else ''}
"""
                        for question in sorted(answers)
                        for answer in answers[question][-1:]),
                    )
        zipper.close()
        with open(filename, 'rb') as file:
            data = file.read()
    finally:
        os.unlink(filename)
        del zipper

    return web.Response(
        body=data,
        content_type='application/zip',
        headers={'Cache-Control': 'no-cache'}
    )

async def upload_course(request): # pylint: disable=too-many-branches
    """Add a new course"""
    session = await get_admin_login(request)
    post = await request.post()
    filehandle = post['course']
    if not hasattr(filehandle, 'filename'):
        more = "You must select a file!"
    src_filename = getattr(filehandle, 'filename', None)
    replace = post.get('replace', '')
    if src_filename:
        dst_filename = replace or src_filename
        if '=' in dst_filename:
            compiler = f"compile_{dst_filename.split('=')[0].lower()}.py"
            dst_filename = utilities.get_course(dst_filename[:-3]) # Remove .py
    else:
        more = "You must select a file!"
    if src_filename is None:
        more = "You forgot to select a course file!"
    elif '=' not in src_filename:
        more = """The file name shape must be : COMPILER=SESSION.py<br>
        For example: «PYTHON=introduction.py» or «JS=example.py»!"""
    elif not src_filename.endswith('.py'):
        more = "Only «.py» file allowed!"
    elif '/' in src_filename:
        more = f"«{src_filename}» invalid name (/)!"
    elif not os.path.exists(compiler):
        more = f"«{src_filename}» use a not defined compiler: «{compiler}»!"
    elif not replace and os.path.exists(dst_filename + '.py'):
        more = f"«{dst_filename}.py» file exists!"
    else:
        with open(dst_filename + '.py', "wb") as file:
            file.write(filehandle.file.read())
        config = utilities.CourseConfig.get(dst_filename)
        if session.login not in config.teachers:
            config.set_parameter('teachers', session.login + ' ' + config.config['teachers'])
        config.set_parameter('stop', '2000-01-01 00:00:01')
        process = await asyncio.create_subprocess_exec("make", dst_filename + '.js')
        await process.wait()
        if replace:
            more = f"Course «{src_filename}» replace «{dst_filename}.py» file"
        else:
            more = f"Course «{src_filename}» added into «{dst_filename}.py» file"
    return await adm_home(request, more)

async def config_reload(request):
    """For regression tests"""
    _session = await utilities.Session.get(request)
    utilities.CONFIG.load()
    return web.Response(
        body='done',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_list(request):
    """Liste all checkpoints"""
    session = await utilities.Session.get(request)
    content = [
        session.header(),
        '''
        <style>
        TABLE { border-collapse: collapse }
        TABLE TD, TABLE TH { border: 1px solid #AAA ; }
        </style>
        <table>
        <tr><th>Course<th>Stud<br>ents<th>Wait<br>ing<th>Work<br>ing<th>Done<th>With me<th>Start date<th>Stop date</tr>
        '''
        ]
    utilities.CourseConfig.load_all_configs()
    now = time.time()
    for _course_name, course in sorted(utilities.CourseConfig.configs.items()):
        if now > course.stop_tt_timestamp:
            continue # Exam done
        waiting = []
        working = []
        with_me = []
        done = []
        for student, active_teacher_room in course.active_teacher_room.items():
            if active_teacher_room[0]:
                working.append(student)
                if active_teacher_room[1] == session.login:
                    with_me.append(student)
            else:
                if active_teacher_room[2]:
                    done.append(student)
                else:
                    waiting.append(student)
        # if session.login in course.teachers:
        content.append(f'''
        <tr>
        <td>{course.course}
        <td>{len(course.active_teacher_room)}
        <td>{len(waiting)}
        <td>{len(working)}
        <td>{len(done)}
        <td>{len(with_me)}
        <td style="white-space: nowrap">{course.start if course.start > "2001" else ""}
        <td style="white-space: nowrap">{course.stop if course.stop < "2100" else ""}
        <td {'style="background:#8F8"'
             if course.start > "2001"
             and course.stop < "2100"
             and course.status('').startswith('running')
             else ''}
        >{'Exam' if course.checkpoint else ''}
        <td><a href="/checkpoint/{course.course}?ticket={session.ticket}"
            {'style="background:#8F8"' if course.highlight else ''}
        >Checkpoint</a>
        <td style="white-space: nowrap">{' '.join(course.teachers)}
        </tr>''')
    return web.Response(
        body=''.join(content),
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint(request):
    """Display the students waiting checkpoint"""
    session, course = await get_teacher_login_and_course(request)
    return web.Response(
        body=session.header() + f'''
        <script>
        COURSE = {json.dumps(course.course)};
        STUDENTS = {json.dumps(await course.get_students())};
        MESSAGES = {json.dumps(course.messages)};
        CHECKPOINT = {json.dumps(course.checkpoint)};
        </script>
        <script src="/checkpoint/BUILDINGS?ticket={session.ticket}"></script>
        <script src="/checkpoint.js?ticket={session.ticket}"></script>
        <link rel="stylesheet" href="/HIGHLIGHT/{course.theme}.css?ticket={session.ticket}">
        <script src="/HIGHLIGHT/highlight.js?ticket={session.ticket}"></script>
        ''',
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def update_browser_data(course):
    """Send update values"""
    return web.Response(
        body=f'''
        STUDENTS = {json.dumps(await course.get_students())};
        MESSAGES = {json.dumps(course.messages)};
        CONFIG.computers = {json.dumps(utilities.CONFIG.computers)};
        ''',
        content_type='application/javascript',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def update_browser(request):
    """Send update values"""
    _session, course = await get_teacher_login_and_course(request)
    return await update_browser_data(course)

async def checkpoint_student(request):
    """Display the students waiting checkpoint"""
    student = request.match_info['student']
    room = request.match_info['room']
    if room == 'STOP':
        # The student is allowed to stop the session
        allow = student
    else:
        allow = None
    session, course = await get_teacher_login_and_course(request, allow=allow)
    seconds = int(time.time())
    old = course.active_teacher_room[student]
    if room == 'STOP':
        old[0] = 0
        to_log = [seconds, ["checkpoint_stop", session.login]]
    elif room == 'RESTART':
        old[0] = 1
        old[1] = session.login
        to_log = [seconds, ["checkpoint_restart", session.login]]
    elif room == 'EJECT':
        old[0] = 0
        old[1] = old[2] = ''
        old[3] = seconds # Make it bold for other teachers
        to_log = [seconds, ["checkpoint_eject", session.login]]
    else:
        if old[1] == '':
            old[0] = 1 # A moved STOPed student must not be reactivated
        old[1] = session.login
        old[2] = room
        to_log = [seconds, ["checkpoint_move", session.login, room]]
    utilities.student_log(course.dirname, student, json.dumps(to_log) + '\n')
    course.record()
    return await update_browser_data(course)

async def checkpoint_bonus(request):
    """Set student time bonus"""
    student = request.match_info['student']
    bonus = request.match_info['bonus']
    session, course = await get_teacher_login_and_course(request)
    seconds = int(time.time())
    old = course.active_teacher_room[student]
    old[7] = int(bonus)
    utilities.student_log(course.dirname, student, f'[{seconds},["time bonus",{bonus},"{session.login}"]]\n')
    course.record()
    return await update_browser_data(course)

async def home(request):
    """Test the user rights to display the good home page"""
    session = await utilities.Session.get(request)
    if session.is_admin():
        return await adm_home(request)
    if not session.is_student():
        return await checkpoint_list(request)
    utilities.CourseConfig.load_all_configs()
    now = time.time()
    content = [session.header()]
    for course_name, course in sorted(utilities.CourseConfig.configs.items()):
        if now > course.stop_tt_timestamp:
            continue # No more running
        if now < course.start_timestamp and not course.highlight:
            continue # Not started nor highlighted
        if course.highlight:
            style = ' style="background: #8F8"'
        else:
            style = ''
        content.append(
            f'<li> <a href="/={course.course}?ticket={session.ticket}"{style}>{course_name}</a>')

    return web.Response(
        body=''.join(content),
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_buildings(request):
    """Building list"""
    _ = await utilities.Session.get(request)
    buildings = {}
    for filename in os.listdir('BUILDINGS'):
        with open('BUILDINGS/' + filename) as file:
            buildings[filename] = file.read()
    return web.Response(
        body=f'BUILDINGS = {json.dumps(buildings)};',
        content_type='application/javascript',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def computer(request):
    """Set value for computer"""
    _session = await utilities.Session.get(request)
    course = utilities.CourseConfig.get(utilities.get_course(request.match_info['course']))
    message = request.match_info.get('message', '')
    building = request.match_info['building']
    column = int(request.match_info['column'])
    line = int(request.match_info['line'])
    if message:
        utilities.CONFIG.computers.append([building, column, line, message, int(time.time())])
    else:
        utilities.CONFIG.computers = utilities.CONFIG.config['computers'] = [
            bug
            for bug in utilities.CONFIG.computers
            if bug[0] != building or bug[1] != column or bug[2] != line
            ]
    utilities.CONFIG.save()
    return await update_browser_data(course)

async def checkpoint_spy(request):
    """All the sources of the student as a list of:
           [timestamp, question, compile | save | answer, source]
    """
    _session, course = await get_teacher_login_and_course(request)
    student = request.match_info['student']
    answers = []
    try:
        with open(f'{course.dirname}/{student}/compile_server.log') as file:
            for line in file:
                if "('COMPILE'," in line:
                    line = ast.literal_eval(line)
                    answers.append([line[0], line[2][1][1], 'c', line[2][1][6]])
                    await asyncio.sleep(0)
    except (IndexError, FileNotFoundError):
        pass

    try:
        with open(f'{course.dirname}/{student}/http_server.log') as file:
            for line in file:
                if '["answer",' in line or '["save",' in line:
                    seconds = 0
                    for item in json.loads(line):
                        if isinstance(item, list) and item[0] in ('answer', 'save'):
                            answers.append([seconds, item[1], item[0][0], item[2]])
                        elif isinstance(item, int):
                            seconds += item
    except (IndexError, FileNotFoundError):
        pass

    return web.Response(
        body=f'''spy({json.dumps(answers)},
                     {json.dumps(student)},
                     {json.dumps(await utilities.LDAP.infos(student))})''',
        content_type='application/javascript',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_message(request):
    """The last answer from the student"""
    session, course = await get_teacher_login_and_course(request)
    course.messages.append([session.login, int(time.time()), request.match_info['message']])
    course.set_parameter('messages', course.messages)
    return web.Response(
        body=f'''MESSAGES.push({json.dumps(course.messages[-1])});ROOM.update_messages()''',
        content_type='application/javascript',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

APP = web.Application()
APP.add_routes([web.get('/', home),
                web.get('/{filename}', handle()),
                web.get('/node_modules/{filename:.*}', handle('node_modules')),
                web.get('/HIGHLIGHT/{filename:.*}', handle('HIGHLIGHT')),
                web.get('/adm/get/{filename:.*}', adm_get),
                web.get('/adm/answers/{saved}/{course:.*}', adm_answers),
                web.get('/adm/home', adm_home),
                web.get('/adm/course/{course}', adm_course),
                web.get('/adm/config/{course}/{action}/{value}', adm_config),
                web.get('/adm/config/{course}/{action}/', adm_config),
                web.get('/adm/c5/{action}/{value}', adm_c5),
                web.get('/config/reload', config_reload),
                web.get('/checkpoint/*', checkpoint_list),
                web.get('/checkpoint/BUILDINGS', checkpoint_buildings),
                web.get('/checkpoint/{course}', checkpoint),
                web.get('/checkpoint/SPY/{course}/{student}', checkpoint_spy),
                web.get('/checkpoint/MESSAGE/{course}/{message:.*}', checkpoint_message),
                web.get('/checkpoint/TIME_BONUS/{course}/{student}/{bonus}', checkpoint_bonus),
                web.get('/checkpoint/{course}/{student}/{room}', checkpoint_student),
                web.get('/computer/{course}/{building}/{column}/{line}/{message:.*}', computer),
                web.get('/computer/{course}/{building}/{column}/{line}', computer),
                web.get('/update/{course}', update_browser),
                web.post('/upload_course', upload_course),
                web.post('/log', log),
                ])
APP.on_startup.append(startup)
logging.basicConfig(level=logging.DEBUG)

class AccessLogger(AbstractAccessLogger): # pylint: disable=too-few-public-methods
    """Logger for aiohttp"""
    def log(self, request, response, run_time): # pylint: disable=arguments-differ
        path = request.path.replace('\n', '\\n')
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {response.status} "
              f"{run_time:5.3f} {request.method[0]} "
              f"{request.query_string.replace('ticket=ST-', '').split('-')[0]:>8}"
              f"{path}",
              flush=True)

web.run_app(APP, host=utilities.C5_IP, port=utilities.C5_HTTP,
            access_log_format="%t %s %D %r", access_log_class=AccessLogger,
            ssl_context=utilities.get_certificate(False))
