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
import html
import asyncio
import urllib.request
from aiohttp import web
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
            print(filename)
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
        print(('get', request.url), flush=True)
        if base:
            session = None # Not authenticated
        else:
            session = utilities.Session.get(request)
            login = await session.get_login(str(request.url).split('?')[0])
            print((login, request.url))
        filename = request.match_info['filename']
        course = None
        if base:
            filename = base + '/' + filename
        else:
            if filename.startswith("="):
                course = utilities.CourseConfig.get(filename[1:-3])
                answers = get_answers(course.course, session.login, saved=True)
                for key, value in answers.items():
                    answers[key] = value[-1] # Only the last answer
                if course:
                    stop = course.get_stop(session.login)
                else:
                    stop = ''
                return File.get('ccccc.html').response(
                    session.header() + f'''
                    <title>C5 is Compiler Course Class in the Cloud</title>
                    <link rel="stylesheet" href="/xxx-highlight.css?ticket={session.ticket}">
                    <link rel="stylesheet" href="/ccccc.css?ticket={session.ticket}">
                    <script src="/xxx-highlight.js?ticket={session.ticket}"></script>
                    <script>
                        SOCK = "wss://{utilities.C5_WEBSOCKET}";
                        ADMIN = "{int(session.is_admin())}";
                        STOP = "{stop}";
                        CP = "{course.config['copy_paste']}",
                        ANSWERS = {json.dumps(answers)};
                    </script>
                    <script src="/ccccc.js?ticket={session.ticket}"></script>''')
            if filename.startswith('course_'):
                course = utilities.CourseConfig.get(filename[:-3])
                status = course.status(login)
                if not session.is_admin():
                    if status == 'done':
                        filename = "course_js_done.js"
                    elif status == 'pending':
                        filename = "course_js_pending.js"
                    elif status == 'checkpoint':
                        filename = "course_js_checkpoint.js"
        return File.get(filename).response()
    return real_handle

def student_log(course_name, login, data):
    """Add a line to the student log"""
    if not os.path.exists(f'{course_name}/{login}'):
        if not os.path.exists(course_name):
            os.mkdir(course_name)
        os.mkdir(f'{course_name}/{login}')
    with open(f'{course_name}/{login}/http_server.log', "a") as file:
        file.write(data)

async def log(request):
    """Log user actions"""
    print(('log', request.url), flush=True)
    session = utilities.Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    post = await request.post()
    course = utilities.CourseConfig.get(post['course'])
    if not course.running(login):
        return
    # XXX Must do sanity check
    student_log(course.course, login, urllib.request.unquote(post['line']))
    return File('favicon.ico').response()

async def startup(app):
    """For the log"""
    app['ldap'] = asyncio.create_task(utilities.LDAP.start())
    print('http serveur running!', flush=True)

async def get_admin_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    session = utilities.Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    if not session.is_admin():
        print(('notAdmin', request.url), flush=True)
        session.redirect('=course_js_not_admin.js')
    print(('Admin', request.url), flush=True)
    return session

async def get_teacher_login_and_course(request):
    """Get the teacher login or redirect to home page if it isn't one"""
    session = utilities.Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    course = utilities.CourseConfig.get(request.match_info['course'])
    if login not in course.teachers:
        print(('notTeacher', request.url), flush=True)
        session.redirect('=course_js_not_teacher.js')
    print(('Teacher', request.url), flush=True)
    return session, course

async def adm_course(request):
    """Course details page for administrators"""
    session = await get_admin_login(request)
    course = request.match_info['course']
    students = {}
    for user in sorted(os.listdir(course)):
        await asyncio.sleep(0)
        files = []
        students[user] = student = {'files': files}
        for filename in sorted(os.listdir(f'{course}/{user}')):
            if '.' in filename:
                # To not display executables
                files.append(filename)
        try:
            with open(f'{course}/{user}/http_server.log') as file:
                student['http_server'] = file.read()
        except IOError:
            pass

    return web.Response(
        body=session.header() + f"""
            <script>STUDENTS = {json.dumps(students)}; COURSE = '{course}';</script>
            <script src="/adm_course.js?ticket={session.ticket}"></script>
            """,
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def adm_config(request):
    """Course details page for administrators"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    config = utilities.CourseConfig.get(course)
    action = request.match_info['action']
    value = request.match_info['value']
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
    elif action == 'copy_paste':
        config.set_parameter('copy_paste', value)
        feedback = f"«{course}» Copy Paste «{'not' if value == '0' else ''} allowed»"
    elif action == 'checkpoint':
        config.set_parameter('checkpoint', value)
        if value == '0':
            feedback = f"«{course}» Automatic access to the courses"
        else:
            feedback = f"«{course}» Need teacher approval to start"

    return await adm_home(request, feedback)

async def adm_c5(request):
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
    elif action == 'ticket_ttl':
        try:
            utilities.CONFIG.set_value(action, int(value))
            more = f"Ticket TTL updated to {value} seconds"
        except ValueError:
            more = "Invalid ticket TTL"
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
        more = '<div class="more">' + more + '</div>'

    utilities.CourseConfig.load_all_configs()
    session = await get_admin_login(request)
    courses = []
    for config in utilities.CourseConfig.configs.values():
        courses.append({
            'course': config.course,
            'status': config.status(''),
            'teachers': config.config['teachers'],
            'logs': os.path.exists(config.course),
            'start': config.start,
            'stop': config.stop,
            'tt': html.escape(config.config['tt']),
            'copy_paste': config.config['copy_paste'],
            'checkpoint': config.config['checkpoint'],
            })

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
    try:
        with open(f'{course}/{user}/http_server.log') as file:
            for line in file:
                if ',["answer",' in line  or  saved and ',["save",' in line:
                    for cell in json.loads(line)[1:]:
                        if isinstance(cell, list):
                            if cell[0] == 'answer':
                                answers[cell[1]].append([cell[2], 1])
                            elif saved and cell[0] == 'save':
                                answers[cell[1]].append([cell[2], 0])
    except IOError:
        return {}
    return answers

async def adm_answers(request):
    """Get students answers"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    saved = int(request.match_info['saved'])
    assert '/.' not in course and course.endswith('.zip')
    course = course[:-4]
    fildes, filename = tempfile.mkstemp()
    try:
        zipper = zipfile.ZipFile(os.fdopen(fildes, "wb"), mode="w")
        for user in sorted(os.listdir(course)):
            await asyncio.sleep(0)
            answers = get_answers(course, user, saved)
            if answers:
                zipper.writestr(
                    f'{course}/{user}#answers',
                    ''.join(
                        '#' * 80 + '\n###################    '
                        + f'{user}     Question {question+1}     Answer {i+1}   Good {answer[1]}\n'
                        + '#' * 80 + '\n'
                        + answer[0] + '\n'
                        for question in sorted(answers)
                        for i, answer in enumerate(answers[question])),
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

async def upload_course(request):
    """Add a new course"""
    session = await get_admin_login(request)
    post = await request.post()
    filehandle = post['course']
    if not hasattr(filehandle, 'filename'):
        more = "You must select a file"
    filename = getattr(filehandle, 'filename', None)
    if filename:
        compiler = '_'.join(filename.split('_')[:2]) + '.py'
    if filename is None:
        more = "You forgot to select a course file"
    elif not filename.endswith('.py'):
        more = "Only «.py» file allowed"
    elif '/' in filename:
        more = f"«{filename}» invalid name (/)"
    elif not os.path.exists(compiler):
        more = f"«{filename}» use a not defined compiler: «{compiler}»"
    elif 'replace' not in post and os.path.exists(filename):
        more = f"«{filename}» name is yet used"
    else:
        with open(filename, "wb") as file:
            file.write(filehandle.file.read())
        config = utilities.CourseConfig.get(filename.replace('.py', ''))
        config.set_parameter('teachers', session.login)
        process = await asyncio.create_subprocess_exec(
            "make", filename.replace('.py', '.js'))
        await process.wait()
        if 'replace' in post:
            more = f"Course «{filename}» replaced"
        else:
            more = f"Course «{filename}» added"
    return await adm_home(request, more)

async def config_reload(request):
    """For regression tests"""
    session = utilities.Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    print(('LoadConfig', login), flush=True)
    utilities.CONFIG.load()
    return web.Response(
        body='done',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_list(request):
    """Liste all checkpoints"""
    session = utilities.Session.get(request)
    content = [
        session.header(),
        '''
        <style>
        TABLE { border-collapse: collapse }
        TABLE TD, TABLE TH { border: 1px solid #AAA ; }
        </style>
        <table>
        <tr><th>Course<th>Students<th>Waiting<th>Working<th>Done<th>With me</tr>
        '''
        ]
    utilities.CourseConfig.load_all_configs()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    for course_name, course in sorted(utilities.CourseConfig.configs.items()):
        if not course.checkpoint:
            continue
        if now > course.stop_tt:
            continue # Exam done
        waiting = []
        working = []
        with_me = []
        done = []
        for student, (active, teacher, room) in course.active_teacher_room.items():
            if active:
                working.append(student)
                if teacher == session.login:
                    with_me.append(student)
            else:
                if room:
                    done.append(student)
                else:
                    waiting.append(student)
        if session.login in course.teachers:
            checkurl = f'<a href="/checkpoint/{course_name}?ticket={session.ticket}">Checkpoint</a>'
        else:
            checkurl = ' '.join(course.teachers)
        content.append(f'''
        <tr>
        <td>{course_name}
        <td>{len(course.active_teacher_room)}
        <td>{len(waiting)}
        <td>{len(working)}
        <td>{len(done)}
        <td>{len(with_me)}
        <td>{checkurl}
        </tr>''')
    return web.Response(
        body=''.join(content),
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def get_students(session, course):
    """Get the student in checkpoint + teacher ones"""
    return [
        [student, active_teacher_room, await utilities.LDAP.infos(student)]
        for student, active_teacher_room in course.active_teacher_room.items()
        if not active_teacher_room[0] or active_teacher_room[1] == session.login
        ]

async def checkpoint(request):
    """Display the students waiting checkpoint"""
    session, course = await get_teacher_login_and_course(request)
    return web.Response(
        body=session.header() + f'''
        <script>
        COURSE = {json.dumps(course.course)};
        STUDENTS = {json.dumps(await get_students(session, course))};
        </script>
        <script src="/checkpoint/BUILDINGS?ticket={session.ticket}"></script>
        <script src="/checkpoint.js?ticket={session.ticket}"></script>''',
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_student(request):
    """Display the students waiting checkpoint"""
    session, course = await get_teacher_login_and_course(request)
    student = request.match_info['student']
    if student:
        room = request.match_info['room']
        seconds = int(time.time())
        if room == 'STOP':
            course.active_teacher_room[student][0] = False
            student_log(course.course, student, f'[{seconds},"checkpoint_stop"]\n')
        elif room == 'EJECT':
            course.active_teacher_room[student][0] = False
            course.active_teacher_room[student] = [False, '', '', int(time.time())]
            student_log(course.course, student, f'[{seconds},"checkpoint_eject"]\n')
        else:
            course.active_teacher_room[student] = [True, session.login, room]
            student_log(course.course, student,
                f'[{seconds},["checkpoint","{session.login}","{room}"]]\n')
        course.record()

    return web.Response(
        body=f'STUDENTS = {json.dumps(await get_students(session, course))};',
        content_type='application/javascript',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def home(request):
    """Test the user rights to display the good home page"""
    session = utilities.Session.get(request)
    if session.is_admin():
        return await adm_home(request)
    if not session.is_student():
        return await checkpoint_list(request)
    utilities.CourseConfig.load_all_configs()
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    content = [session.header()]
    for course_name, course in sorted(utilities.CourseConfig.configs.items()):
        if now > course.stop_tt or now < course.start:
            continue # Not running
        content.append(
            f'<li> <a href="/={course_name}.js?ticket={session.ticket}">{course_name}</a>')

    return web.Response(
        body=''.join(content),
        content_type='text/html',
        charset='utf-8',
        headers={'Cache-Control': 'no-cache'}
    )

async def checkpoint_buildings(request):
    """Building list"""
    _ = utilities.Session.get(request)
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

APP = web.Application()
APP.add_routes([web.get('/', home),
                web.get('/{filename}', handle()),
                web.get('/brython/{filename}', handle('brython')),
                web.get('/adm/get/{filename:.*}', adm_get),
                web.get('/adm/answers/{saved}/{course:.*}', adm_answers),
                web.get('/adm/home', adm_home),
                web.get('/adm/course/{course}', adm_course),
                web.get('/adm/config/{course}/{action}/{value}', adm_config),
                web.get('/adm/c5/{action}/{value}', adm_c5),
                web.get('/config/reload', config_reload),
                web.get('/checkpoint/*', checkpoint_list),
                web.get('/checkpoint/BUILDINGS', checkpoint_buildings),
                web.get('/checkpoint/{course}', checkpoint),
                web.get('/checkpoint/{course}/{student}/{room}', checkpoint_student),
                web.post('/upload_course', upload_course),
                web.post('/log', log),
                ])
APP.on_startup.append(startup)
web.run_app(APP, host=utilities.C5_IP, port=utilities.C5_HTTP,
            ssl_context=utilities.get_certificate(False))
