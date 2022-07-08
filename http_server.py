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
import urllib.request
import html
import asyncio
import aiohttp
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
        self.safe = filename.startswith(('compile.', 'ccccc.', 'course_', 'favicon'))
        if '/.' in filename:
            self.safe = False
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
    def get_content(self, session, course=None):
        """Check file date and returns content"""
        mtime = os.path.getmtime(self.filename)
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.filename, "rb") as file:
                content = file.read()
                if self.charset is not None:
                    content = content.decode(self.charset)
                self.content = content
        if self.filename == 'ccccc.html':
            content = self.content.replace('__LOGIN__', session.login)
            content = content.replace('__TICKET__', session.ticket)
            content = content.replace('__SOCK__', f"wss://{utilities.C5_WEBSOCKET}")
            content = content.replace('__ADMIN__', str(int(utilities.CONFIG.is_admin(session.login))))
            answers = get_answers(course.course, session.login)
            for key, value in answers.items():
                answers[key] = value[-1] # Only the last answer
            content = content.replace('__ANSWERS__', json.dumps(answers))
            if course:
                content = content.replace('__STOP__', str(course.get_stop(session.login)))
            return content

        return self.content
    def response(self, session, course=None):
        """Get the response to send"""
        return web.Response(
            body=self.get_content(session, course),
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

# Sauvegarde disque
# Menage temporel

class Session:
    """Session management"""
    session_cache = {}
    def __init__(self, ticket, client_ip, browser, login=None):
        self.ticket = ticket
        self.client_ip = client_ip
        self.browser = browser
        self.login = login
    async def get_login(self, service):
        """Return a validated login"""
        if self.login:
            return self.login
        service = service.replace(
            f'http://{utilities.C5_IP}:{utilities.C5_HTTP}/',
            f'https://{utilities.C5_URL}/')
        if utilities.C5_VALIDATE:
            async with aiohttp.ClientSession() as session:
                url = utilities.C5_VALIDATE % (urllib.request.quote(service),
                                               urllib.request.quote(self.ticket))
                async with session.get(url) as data:
                    lines = await data.text()
                    lines = lines.split('\n')
                    if lines[0] == 'yes':
                        self.login = lines[1]
                        self.record()
            if not self.login:
                print(('?', service))
                raise web.HTTPFound(
                    utilities.C5_REDIRECT + urllib.request.quote(service))
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
        return repr((self.client_ip, self.browser, self.login))
    def check(self, request, client_ip, browser):
        """Check for hacker"""
        if self.client_ip != client_ip or self.browser != browser:
            raise web.HTTPFound(str(request.url).split('?')[0])

    @classmethod
    def get(cls, request):
        """Get or create a session.
        Raise an error if hacker.
        """
        ticket = request.query.get('ticket', '')
        client_ip = request.headers.get('x-forwarded-for', '')
        if client_ip:
            client_ip = client_ip.split(",")[0]
        else:
            client_ip, _port = request.transport.get_extra_info('peername')
        browser = request.headers.get('user-agent', '')
        if ticket in cls.session_cache:
            session = cls.session_cache[ticket]
            session.check(request, client_ip, browser)
        elif ticket and os.path.exists(f'TICKETS/{ticket}'):
            with open(f'TICKETS/{ticket}', 'r') as file:
                session = Session(ticket, *eval(file.read())) # pylint: disable=eval-used
            session.check(request, client_ip, browser)
        else:
            session = Session(ticket, client_ip, browser)
            if ticket:
                cls.session_cache[ticket] = session
        return session

def handle(base=''):
    """Send the file content"""
    async def real_handle(request):
        print(('get', request.url), flush=True)
        if base:
            session = None # Not authenticated
        else:
            session = Session.get(request)
            login = await session.get_login(str(request.url).split('?')[0])
            print((login, request.url))
        filename = request.match_info.get('filename', "=course_js.js")
        course = None
        if base:
            filename = base + '/' + filename
        else:
            if filename.startswith("="):
                course = utilities.CourseConfig.get(filename[1:-3])
                filename = 'ccccc.html'
            if filename.startswith('course_'):
                course = utilities.CourseConfig.get(filename[:-3])
                status = course.status(login)
                if not utilities.CONFIG.is_admin(login):
                    if status == 'done':
                        filename = "course_js_done.js"
                    elif status == 'pending':
                        filename = "course_js_pending.js"
        return File(filename).response(session, course)
    return real_handle

async def log(request):
    """Log user actions"""
    print(('log', request.url), flush=True)
    session = Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    post = await request.post()
    course = utilities.CourseConfig.get(post['course'])
    if not course.running(login):
        return
    line = post['line']
    if not os.path.exists(f'{course.course}/{login}'):
        if not os.path.exists(course.course):
            os.mkdir(course.course)
        os.mkdir(f'{course.course}/{login}')
    with open(f'{course.course}/{login}/http_server.log', "a") as file:
        file.write(urllib.request.unquote(line))
    return File('favicon.ico').response(session)

async def startup(_app):
    """For the log"""
    print('http serveur running!', flush=True)

async def get_admin_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    session = Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    if not utilities.CONFIG.is_admin(login):
        print(('notAdmin', request.url), flush=True)
        raise web.HTTPFound('..')
    print(('Admin', request.url), flush=True)
    return session

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
        body=f"""<!DOCTYPE html>
            <html>
            <head>
            <link REL="icon" HREF="favicon.ico?ticket={session.ticket}">
            </head>
            <body></body></html>
            <script>STUDENTS = {json.dumps(students)}; COURSE = '{course}';</script>
            <script src="adm_course.js?ticket={session.ticket}"></script>
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
    if ':' in action:
        action, more = action.split(':', 1)
    else:
        more = time.strftime('%Y-%m-%d %H:%M:%S')
    if action == 'stop':
        config.set_stop(more)
        if config.start > more:
            config.set_start(more)
    elif action == 'start':
        config.set_start(more)
        config.set_stop('2100-01-01 00:00:00')
    elif action == 'tt':
        config.set_tt(more)

    return await adm_home(request)

async def adm_add_master(request):
    """Add a C5 master"""
    _session = await get_admin_login(request)
    login = request.match_info['master']
    utilities.CONFIG.add_master(login)
    return await adm_home(request)

async def adm_del_master(request):
    """Remove a C5 master"""
    _session = await get_admin_login(request)
    login = request.match_info['master']
    utilities.CONFIG.del_master(login)
    return await adm_home(request)


async def adm_home(request, more=''):
    """Home page for administrators"""
    session = await get_admin_login(request)
    courses = []
    for course in sorted(os.listdir('.')):
        if course.startswith('course_') and course.endswith('.js'):
            if course in ('course_js_done.js', 'course_js_pending.js'):
                continue
            course = course[:-3]
            config = utilities.CourseConfig.get(course)
            courses.append({
                'course': course,
                'status': config.status(''),
                'master': config.master,
                'logs': os.path.exists(course),
                'start': config.start,
                'stop': config.stop,
                'tt': html.escape(config.config['tt']),
                })

    return web.Response(
        body=f"""<!DOCTYPE html>
            <html>
            <head>
            <link REL="icon" HREF="favicon.ico?ticket={session.ticket}">
            </head>
            <body></body></html>
            <script>
            TICKET = {json.dumps(session.ticket)};
            COURSES = {json.dumps(courses)};
            MORE = {json.dumps(more)};
            LOGIN = {json.dumps(session.login)};
            CONFIG = {utilities.CONFIG.json()};
            </script>
            <script src="adm_home.js?ticket={session.ticket}"></script>
            """,
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

def get_answers(course, user):
    """Get question answers"""
    answers = collections.defaultdict(list)
    try:
        with open(f'{course}/{user}/http_server.log') as file:
            for line in file:
                if ',["answer",' in line:
                    for cell in json.loads(line)[1:]:
                        if isinstance(cell, list) and cell[0] == 'answer':
                            answers[cell[1]].append(cell[2])
    except IOError:
        return {}
    return answers

async def adm_answers(request):
    """Get students answers"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    assert '/.' not in course and course.endswith('.zip')
    course = course[:-4]
    fildes, filename = tempfile.mkstemp()
    try:
        zipper = zipfile.ZipFile(os.fdopen(fildes, "wb"), mode="w")
        for user in sorted(os.listdir(course)):
            await asyncio.sleep(0)
            answers = get_answers(course, user)
            if answers:
                zipper.writestr(
                    f'{course}/{user}#answers',
                    ''.join(
                        '#' * 80 + '\n###################    '
                        + f'{user}     Question {question+1}     Answer {i+1}\n'
                        + '#' * 80 + '\n'
                        + answer + '\n'
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
        config.set_master(session.login)
        process = await asyncio.create_subprocess_exec(
            "make", filename.replace('.py', '.js'))
        await process.wait()
        if 'replace' in post:
            more = f"Course «{filename}» replaced"
        else:
            more = f"Course «{filename}» added"
    more = '<div class="more">' + more + '</div>'
    return await adm_home(request, more)

APP = web.Application()
APP.add_routes([web.get('/', handle()),
                web.get('/adm_home', adm_home),
                web.get('/adm_course={course}', adm_course),
                web.get('/adm_config={course}={action}', adm_config),
                web.get('/adm_add_master={master}', adm_add_master),
                web.get('/adm_del_master={master}', adm_del_master),
                web.get('/{filename}', handle()),
                web.get('/brython/{filename}', handle('brython')),
                web.get('/adm_get/{filename:.*}', adm_get),
                web.get('/adm_answers/{course:.*}', adm_answers),
                web.post('/log', log),
                web.post('/upload_course', upload_course),
                ])
APP.on_startup.append(startup)
web.run_app(APP, host=utilities.C5_IP, port=utilities.C5_HTTP,
            ssl_context=utilities.get_certificate(False))
