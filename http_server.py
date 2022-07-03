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
            content = content.replace('__ADMIN__', str(int(utilities.is_admin(session.login))))
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
                if not utilities.is_admin(login):
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
    course = utilities.CourseConfig.get(request.match_info['course'])
    if not course.running(login):
        return
    data = request.match_info['data']
    if not os.path.exists(f'{course.course}/{login}'):
        os.mkdir(f'{course.course}/{login}')
    with open(f'{course.course}/{login}/http_server.log', "a") as file:
        file.write(urllib.request.unquote(data))
    return File('favicon.ico').response(session)

async def startup(_app):
    """For the log"""
    print('http serveur running!', flush=True)

async def get_admin_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    print(('log', request.url), flush=True)
    session = Session.get(request)
    login = await session.get_login(str(request.url).split('?')[0])
    if not utilities.is_admin(login):
        raise web.HTTPFound('..')
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
        for filename in os.listdir(f'{course}/{user}'):
            if '.' in filename:
                # To not display executables
                files.append(filename)
        try:
            with open(f'{course}/{user}/http_server.log') as file:
                student['http_server'] = file.read()
        except IOError:
            pass

    return web.Response(
        body=f"""
            <html><body></body></html>
            <script>STUDENTS = {json.dumps(students)}; COURSE = '{course}';</script>
            <script src="adm_home.js?ticket={session.ticket}"></script>
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

async def adm_home(request):
    """Home page for administrators"""
    session = await get_admin_login(request)
    text = ['''<!DOCTYPE html>
<script>
URL = location.toString();
CLEAN = URL.replace(RegExp('(.*)/adm_.*([?]ticket=.*)'), "$1/adm_home$2");
console.log(URL);
console.log(CLEAN);
window.history.replaceState('_a_', '_t_', CLEAN);
</script>
    <title>C5 Administration</title>
               <h1>C5 Administration</h1>
               <style>
               TABLE { border-spacing: 0px; border-collapse: collapse ; }
               TABLE TD { border: 1px solid #888; padding: 0px }
               TABLE TD INPUT { margin: 0.5em ; margin-right: 0px }
               TABLE TD TEXTAREA { border: 0px; height: 4em }
               TT, PRE, INPUT { font-family: monospace, monospace; font-size: 100% }
               TD > BUTTON { margin-left: 5px ; margin-right: 5px; height: 3em }
               .done { background: #FDD }
               .running { background: #DFD }
               .running_tt { background: #FEB }
               </style>
               <script>
               function T(x) { return x + "?ticket=''', session.ticket, '''";}
               function TV(self, x) { return T(x + encodeURIComponent(self.value));}
               function J(x) { window.location = x; return undefined;}
               </script>
            Colors:
               <span class="done">The session is done</span>,
               <span class="running">The session is running</span>,
               <span class="running_tt">The session is running for tiers-temps</span>,
               <span>The session has not yet started</span>.
               <p>
               Changing the stop date will not update onscreen timers.
               <table>
               <tr><th>Course<th>Master<th>Logs<th>Try<th>Start<th>Stop<th>TT logins<th>ZIP</tr>\n'''
           ]
    for course in sorted(os.listdir('.')):
        if course.startswith('course_') and course.endswith('.js'):
            if course in ('course_js_done.js', 'course_js_pending.js'):
                continue
            course = course[:-3]
            config = utilities.CourseConfig.get(course)
            status = config.status('')
            text.append(f'<tr class="{status}"><td><b>')
            text.append(course.split('_', 1)[1])
            text.append('</b><td>')
            text.append(config.master)
            text.append('<td>')
            if os.path.exists(course):
                text.append(f'<button onclick="J(T(\'adm_course={course}\'))">Logs</a>')
            text.append(f'<td><button onclick="J(T(\'={course}.js\'))">Try</a>')
            text.append(f'<td><input onchange="J(TV(this,\'adm_config={course}=start:\'))" value="')
            text.append(config.start)
            text.append('">')
            if status != 'running':
                text.append(f'<button onclick="J(T(\'adm_config={course}=start\'))">Now</button>')
            text.append(f'<td><input onchange="J(TV(this,\'adm_config={course}=stop:\'))" value="')
            text.append(config.stop)
            text.append('">')
            if status != 'done':
                text.append(f'<button onclick="J(T(\'adm_config={course}=stop\'))">Now</button>')
            text.append(f'<td><textarea onchange="J(TV(this,\'adm_config={course}=tt:\'))">')
            text.append(html.escape(config.config['tt']))
            text.append('</textarea><td>')
            if os.path.exists(course):
                text.append(f'<button onclick="J(T(\'adm_get/{course}.zip\'))">ZIP</a>')
            text.append('</tr>\n')
    text.append('</table>')
    return web.Response(
        body=''.join(text),
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


APP = web.Application()
APP.add_routes([web.get('/', handle()),
                web.get('/adm_home', adm_home),
                web.get('/adm_course={course}', adm_course),
                web.get('/adm_config={course}={action}', adm_config),
                web.get('/{filename}', handle()),
                web.get('/log/{course}/{data}', log),
                web.get('/brython/{filename}', handle('brython')),
                web.get('/adm_get/{filename:.*}', adm_get),
                web.get('/adm_answers/{course:.*}', adm_answers),
                ])
APP.on_startup.append(startup)

web.run_app(APP, host=utilities.local_ip(), port=utilities.C5_HTTP,
            ssl_context=utilities.get_certificate(False))
