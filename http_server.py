#!/usr/bin/python3

import os
from aiohttp import web
import utilities

# To make casauth work we should not use a proxy
for i in ('http_proxy', 'https_proxy'):
    if i in os.environ:
        del os.environ[i]

class FileCache:
    """Manage file answer"""
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
    def get_content(self):
        """Check file date and returns content"""
        mtime = os.path.getmtime(self.filename)
        if mtime != self.mtime:
            self.mtime = mtime
            with open(self.filename, "rb") as file:
                content = file.read()
                if self.charset is not None:
                    content = content.decode(self.charset)
                    content = content .replace("__SOCK__",
                                               f"wss://{utilities.C5_WEBSOCKET}")
                self.content = content
        return self.content
    def response(self):
        """Get the response to send"""
        return web.Response(
            body=self.get_content(),
            content_type=self.mime,
            charset=self.charset,
            headers={
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                'Cache-Control': 'no-cache',
                # 'Cache-Control': 'max-age=60',
            }
        )

FILE_CACHE = {}

def handle(base=''):
    """Send the file content"""
    async def real_handle(request):
        filename = request.match_info.get('filename', "ccccc.html")
        if base:
            filename = base + '/' + filename
        print(filename)
        if filename not in FILE_CACHE:
            FILE_CACHE[filename] = FileCache(filename)
        return FILE_CACHE[filename].response()
    return real_handle

async def startup(_app):
    print('http serveur running', flush=True)

APP = web.Application()
APP.add_routes([web.get('/', handle()),
                web.get('/{filename}', handle()),
                web.get('/brython/{filename}', handle('brython')),
                ])
APP.on_startup.append(startup)

web.run_app(APP, host=utilities.local_ip(), port=utilities.C5_HTTP,
            ssl_context=utilities.get_certificate(False))
