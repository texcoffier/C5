#!/usr/bin/python3
"""
Simple web server with session management
"""

import os
import time
import urllib.request
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
    def get_content(self, session):
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
            return self.content.replace(
                '__LOGIN__', session.login).replace(
                    '__TICKET__', session.ticket).replace(
                        '__SOCK__', f"wss://{utilities.C5_WEBSOCKET}")

        return self.content
    def response(self, session):
        """Get the response to send"""
        return web.Response(
            body=self.get_content(session),
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
                url = utilities.C5_VALIDATE % (urllib.request.quote(service), urllib.request.quote(self.ticket))
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
        with open(f'TICKETS/{self.ticket}', 'w') as file:
            file.write(str(self))
    def __str__(self):
        return repr((self.client_ip, self.browser, self.login))
    def check(self, request, client_ip, browser):
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
                session = Session(ticket, *eval(file.read()))
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
        session = Session.get(request)
        login = await session.get_login(str(request.url).split('?')[0])
        print((login, request.url))
        filename = request.match_info.get('filename', "course=")
        if base:
            filename = base + '/' + filename
        else:
            if filename.startswith("="):
                filename = 'ccccc.html'
        return File(filename).response(session)
    return real_handle

async def startup(_app):
    """For the log"""
    print('http serveur running!', flush=True)

APP = web.Application()
APP.add_routes([web.get('/', handle()),
                web.get('/{filename}', handle()),
                web.get('/brython/{filename}', handle('brython')),
                ])
APP.on_startup.append(startup)

web.run_app(APP, host=utilities.local_ip(), port=utilities.C5_HTTP,
            ssl_context=utilities.get_certificate(False))
