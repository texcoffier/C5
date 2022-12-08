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
import re
import traceback
import html
import urllib.request
from aiohttp import web
from aiohttp.abc import AbstractAccessLogger
import utilities

# To make casauth work we should not use a proxy
for i in ('http_proxy', 'https_proxy'):
    if i in os.environ:
        del os.environ[i]

COMPILERS = [i[8:-3].upper()
             for i in os.listdir('.')
             if i.startswith('compile_')
             and i.endswith('.py')
             and i != 'compile_server.py'
             ]

def response(content, content_type="text/html", charset='utf-8', cache=False):
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
    file_cache = {}
    cache = False

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
                self.cache = len(content) > 200000 # checkpoint.js must no yet be cached
                if self.charset is not None:
                    content = content.decode(self.charset)
                self.content = content
        return self.content
    def response(self, content=''):
        """Get the response to send"""
        return response(
            content or self.get_content(),
            content_type=self.mime,
            charset=self.charset,
            cache=self.cache
        )
    @classmethod
    def get(cls, filename):
        """Get or create File object"""
        if filename not in cls.file_cache:
            cls.file_cache[filename] = File(filename)
        return cls.file_cache[filename]

def filter_last_answer(answers):
    """Return the last answer of each status"""
    last = [None, None, None, None]
    for source_answer_time in answers:
        last[source_answer_time[1]] = source_answer_time
    return last

async def editor(session, is_admin, course, login, grading=0, author=0):
    """Return the editor page.
       'saved' : see 'get_answer' comment.
    """
    versions = {}
    stop = ''
    if author and is_admin:
        with open(course.dirname + '.py', 'r', encoding='utf-8') as file:
            source = file.read()
        answers = {'0': [source, 0, 0]}
        course = utilities.CourseConfig.get('COMPILE_PYTHON/editor')
    else:
        answers, _blurs = get_answers(course.dirname, login, compiled = grading)
        if grading:
            # The last save or ok or compiled or snapshot
            for key, value in answers.items():
                last = filter_last_answer(value)
                answers[key] = max(last, key=lambda x: x[2] if x else 0) # Last time
                versions[key] = last
        else:
            # The last save
            for key, value in answers.items():
                good = 0
                for _source, answer, _time in value:
                    if answer == 0:
                        value[-1][1] = good
                    elif answer == 1:
                        good = 1 # Correct answer even if changed after
                answers[key] = value[-1] # Only the last answer
        if course:
            stop = course.get_stop(login)
    if grading:
        notation = f"NOTATION = {json.dumps(course.notation)};"
        infos = await utilities.LDAP.infos(login)
        title = infos['sn'].upper() + ' ' + infos['fn'].title()
    else:
        notation = 'NOTATION = "";'
        infos = session.infos
        title = course.course.split('=', 1)[1]
        last = ''
    return File.get('ccccc.html').response(
        session.header() + f'''
        <title>{title}</title>
        <link rel="stylesheet" href="/HIGHLIGHT/{course.theme}.css?ticket={session.ticket}">
        <link rel="stylesheet" href="/ccccc.css?ticket={session.ticket}">
        <script src="/HIGHLIGHT/highlight.js?ticket={session.ticket}"></script>
        <script>
            GRADING = {grading};{notation}
            STUDENT = "{login}";
            COURSE = "{course.course}";
            SOCK = "wss://{utilities.C5_WEBSOCKET}";
            ADMIN = "{int(is_admin)}";
            STOP = "{stop}";
            VERSIONS = {json.dumps(versions)};
            CP = {course.config['copy_paste']};
            SAVE_UNLOCK = {int(course.config['save_unlock'])};
            SEQUENTIAL = {int(course.config['sequential'])};
            COLORING = {int(course.config['coloring'])};
            INFOS = {infos};
            CHECKPOINT = {course.checkpoint};
            ANSWERS = {json.dumps(answers)};
            WHERE = {json.dumps(course.active_teacher_room.get(login,(False,'?','?,0,0',0,0,0,'ip',0,'')))};
        </script>
        <script src="/ccccc.js?ticket={session.ticket}"></script>''')


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
                status = course.status(login, session.client_ip)
                is_admin = session.is_grader(course)
                if not is_admin:
                    if status == 'done':
                        return session.message('done')
                    if status == 'pending':
                        return session.message('pending')
                    if status == 'checkpoint':
                        return session.message('checkpoint')
                return await editor(session, is_admin, course, session.login)
            if '=' in filename:
                course = utilities.CourseConfig.get(utilities.get_course(filename))
                filename = course.filename.replace('.cf', '.js')
                status = course.status(login, session.client_ip)
                if not session.is_grader(course) and not status.startswith('running'):
                    return session.message('done')
        return File.get(filename).response()
    return real_handle

# https://pundit.univ-lyon1.fr:4201/grade/REMOTE=LIFAPI_Seq1TPnotep/p2100091
async def grade(request):
    """Display the grading page"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_grader(course)
    if not is_grader:
        return response("Vous n'êtes pas autorisé à noter.")
    return await editor(session, True, course, request.match_info['login'], grading=1)

async def log(request):
    """Log user actions"""
    session = await utilities.Session.get(request)
    post = await request.post()
    course = utilities.CourseConfig.get(utilities.get_course(post['course']))
    if not course.running(session.login, session.client_ip):
        return response(
            """<!DOCTYPE html>
            <script>
            alert("Ce que vous faites n'est plus enregistré :\n"
                  + "  * L'examen est terminé\n"
                  + "  * ou bien votre adresse IP a changé !\n"
                  + "Contactez l'enseignant."
                 )
            </script>""")
    data = urllib.request.unquote(post['line'])
    # Must do sanity check on logged data
    try:
        parsed_data = json.loads(data)
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

    if course.course == 'PYTHON=editor':
        source = None
        for item in parsed_data:
            if isinstance(item, list) and item[0] == 'save':
                source = item[2]
        if source:
            if not session.is_admin(session.edit):
                return response('<script>alert("Vous n\'avez pas le droit !")</script>')
            os.rename(session.edit.dirname + '.py', session.edit.dirname + '.py~')
            os.rename(session.edit.dirname + '.js', session.edit.dirname + '.js~')
            with open(session.edit.dirname + '.py', 'w', encoding="utf-8") as file:
                file.write(source)
            with os.popen(f'make {session.edit.dirname + ".js"} 2>&1', 'r') as file:
                errors = file.read()
            if 'ERROR' in errors:
                os.rename(session.edit.dirname + '.py~', session.edit.dirname + '.py')
                os.rename(session.edit.dirname + '.js~', session.edit.dirname + '.js')
            return response(f'''<!DOCTYPE html>
            <script>
            window.parent.ccccc.record_done();
            alert({json.dumps(errors)})
            </script>
            ''')

    return response("<!DOCTYPE html>\n<script>window.parent.ccccc.record_done()</script>")

async def record_grade(request):
    """Log a grade"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_course_grader(course)
    if not is_grader:
        return response("Vous n'êtes pas autorisé à noter.")
    post = await request.post()
    login = post['student']
    if not os.path.exists(f'{course.dirname}/{login}'):
        return response("Hacker?")
    grade_file = f'{course.dirname}/{login}/grades.log'
    if 'grade' in post:
        with open(grade_file, "a") as file:
            file.write(json.dumps([int(time.time()), session.login, post['grade'], post['value']]) + '\n')
    if os.path.exists(grade_file):
        with open(grade_file, "r") as file:
            grades = file.read()
            grading = {}
            for line in grades.split('\n'):
                if line:
                    line = json.loads(line)
                    if line[3]:
                        grading[line[2]] = float(line[3])
                    else:
                        grading.pop(line[2], None)
            course.active_teacher_room[login][8] = [sum(grading.values()), len(grading)]
    else:
        grades = ''
    return response(f"<!DOCTYPE html>\n<script>window.parent.ccccc.update_grading({json.dumps(grades)})</script>")

async def record_comment(request):
    """Log a comment"""
    session, course = await get_teacher_login_and_course(request)
    is_grader = session.is_course_grader(course)
    if not is_grader:
        return response("Vous n'êtes pas autorisé à noter.")
    post = await request.post()
    login = post['student']
    if not os.path.exists(f'{course.dirname}/{login}'):
        return response("Hacker?")
    comment_file = f'{course.dirname}/{login}/comments.log'
    if 'comment' in post:
        with open(comment_file, "a") as file:
            file.write(json.dumps([int(time.time()), session.login, int(post['question']),
                                   int(post['version']), int(post['line']), post['comment']]) + '\n')
    if os.path.exists(comment_file):
        with open(comment_file, "r") as file:
            comments = file.read()
    else:
        comments = ''
    return response(f"<!DOCTYPE html>\n<script>window.parent.ccccc.update_comments({json.dumps(comments)})</script>")

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
    if utilities.C5_VALIDATE:
        app['load_student_infos'] = asyncio.create_task(load_student_infos())
    print("DATE HOUR STATUS TIME METHOD(POST/GET) TICKET/URL")

async def get_author_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    if not session.is_author():
        raise session.message('not_author', exception=True)
    return session

async def get_admin_login(request):
    """Get the admin login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    if not session.is_admin():
        raise session.message('not_admin', exception=True)
    return session

async def get_root_login(request):
    """Get the root login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    if not session.is_root():
        raise session.message('not_root', exception=True)
    return session

async def get_teacher_login_and_course(request, allow=None):
    """Get the teacher login or redirect to home page if it isn't one"""
    session = await utilities.Session.get(request)
    course = utilities.CourseConfig.get(utilities.get_course(request.match_info['course']))
    if session.is_student() and allow != session.login and not session.is_proctor(course):
        raise session.message('not_teacher', exception=True)
    return session, course

async def adm_course(request):
    """Course details page for administrators"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
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

            with open(f'{course.dirname}/{user}/grades.log') as file:
                student['grades'] = file.read()
        except IOError:
            pass

    return response(
        session.header() + f"""
            <script>
            STUDENTS = {json.dumps(students)};
            COURSE = '{course.course}';
            </script>
            <script src="/adm_course.js?ticket={session.ticket}"></script>
            """)

async def adm_config(request): # pylint: disable=too-many-branches
    """Course details page for administrators"""
    session, config = await get_teacher_login_and_course(request)
    if not session.is_admin(config):
        raise session.message('not_author', exception=True)
    course = config.course
    action = request.match_info['action']
    value = request.match_info.get('value', '')
    if value == 'now':
        value = time.strftime('%Y-%m-%d %H:%M:%S')
    if action == 'stop':
        try:
            if len(value) != 19:
                value += ' '
            time.strptime(value, '%Y-%m-%d %H:%M:%S')
            config.set_parameter('stop', value)
            feedback = f"«{course}» Stop date updated to «{value}»"
        except ValueError:
            feedback = f"«{course}» Stop date invalid: «{value}»!"
    elif action == 'start':
        try:
            if len(value) != 19:
                value += ' '
            time.strptime(value, '%Y-%m-%d %H:%M:%S')
            config.set_parameter('start', value)
            feedback = f"«{course}» Start date updated to «{value}»"
        except ValueError:
            feedback = f"«{course}» Start date invalid: «{value}»!"
    elif action == 'tt':
        config.set_parameter('tt', value)
        feedback = f"«{course}» TT list updated with «{value}»"
    elif action == 'admins':
        config.set_parameter('admins', value)
        feedback = f"«{course}» Admins list updated with «{value}»"
    elif action == 'graders':
        config.set_parameter('graders', value)
        feedback = f"«{course}» Graders list updated with «{value}»"
    elif action == 'proctors':
        config.set_parameter('proctors', value)
        feedback = f"«{course}» Proctors list updated with «{value}»"
    elif action == 'theme':
        if os.path.exists(f'HIGHLIGHT/{value}.css'):
            config.set_parameter('theme', value)
            feedback = f"«{course}» Highlight theme updated to «{value}»"
        else:
            feedback = f"«{course}» Highlight theme «{value}» does not exists!"
    elif action == 'copy_paste':
        config.set_parameter('copy_paste', value)
        feedback = f"«{course}» Copy Paste «{'not' if value == '0' else ''} allowed»"
    elif action == 'coloring':
        config.set_parameter('coloring', value)
        feedback = f"«{course}» Syntax coloring: «{value != '0'}»"
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
    elif action == 'notation':
        config.set_parameter('notation', value)
        feedback = f"«{course}» Notation set to {value[:100]}"
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
        return response(f"«{course}» moved to Trash directory. Now close this page!")
    elif action == 'rename':
        value = value.replace('.py', '')
        new_dirname = f'COMPILE_{config.compiler}/{value}'
        if '.' in value or '/' in value or '-' in value:
            return response(f"«{value}» invalid name because it contains /, ., -!")
        for extension in ('', '.cf', '.py', '.js'):
            if os.path.exists(f'{new_dirname}{extension}'):
                return response(f"«{value}» exists!")
        for extension in ('', '.cf', '.py', '.js'):
            if os.path.exists(config.dirname + extension):
                os.rename(config.dirname + extension, f'{new_dirname}{extension}')
        del utilities.CourseConfig.configs[config.dirname] # Delete old
        utilities.CourseConfig.get(new_dirname) # Full reload of new (safer than updating)
        return response(f"«{course}» Renamed as «{config.compiler}={value}». Now close this page!")

    return response(
        f'update_course_config({json.dumps(config.config)}, {json.dumps(feedback)})',
        content_type='application/javascript')

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
    _session = await get_root_login(request)
    action = request.match_info['action']
    value = request.match_info['value']
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
            utilities.CONFIG.set_value(action, text_to_dict(value))
            more = f"IPs per room updated to<pre>{value}</pre>"
        except ValueError:
            more = "Invalid syntax!"
    elif action == 'disabled':
        try:
            utilities.CONFIG.set_value(action, text_to_dict(value))
            more = f"Disabled updated to<pre>{value}</pre>"
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
    elif action == 'eval':
        try:
            result = repr(eval(value)) # pylint: disable=eval-used
        except: # pylint: disable=bare-except
            result = traceback.format_exc()
        more = '<b>' + html.escape(value) + '</b><pre>' + html.escape(result) + '</pre>'
    else:
        more = "You are a hacker!"
    return await adm_root(request, more)

async def adm_root(request, more=''):
    """Home page for roots"""
    if more:
        if more.endswith('!'):
            more = '<div id="more" style="background: #F88">' + more + '</div>'
        else:
            more = '<div id="more">' + more + '</div>'

    session = await get_root_login(request)
    return response(
        session.header((), more)
        + f'<script src="/adm_root.js?ticket={session.ticket}"></script>')

async def adm_get(request):
    """Get a file or a ZIP"""
    _session = await get_admin_login(request)
    filename = request.match_info['filename']
    if '/.' in filename:
        content = 'Hacker'
    else:
        if filename.endswith('.zip'):
            stream = web.StreamResponse()
            stream.content_type = 'application/zip'
            await stream.prepare(request)
            course = filename[:-4]
            process = await asyncio.create_subprocess_exec(
                'zip', '-r', '-', course, course + '.py', course + '.cf',
                stdout=asyncio.subprocess.PIPE,
                )
            data = 'Go!'
            while data:
                data = await process.stdout.read(64 * 1024)
                await stream.write(data)
            return stream
        with open(filename, 'r') as file:
            content = file.read()
    return response(content, content_type='text/plain')

def get_answers(course, user, compiled=False):
    """Get question answers.
       The types are:
         * 0 : saved source
         * 1 : source passing the test
         * 2 : compilation (if compiled is True)
         * 3 : snapshot (5 seconds before examination end)
    Returns 'answers' and 'blurs'
    answers is a dict from question to a list of [source, type, timestamp]
    """
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
                            elif what == 'save':
                                answers[cell[1]].append([cell[2], 0, seconds])
                            elif what == 'snapshot':
                                answers[cell[1]].append([cell[2], 3, seconds])
                            elif what == 'question':
                                question = cell[1]
                        elif isinstance(cell, str):
                            if cell == 'Blur':
                                blurs[question] += 1
                        else:
                            seconds += cell
    except IOError:
        return {}, {}

    if compiled:
        try:
            with open(f'{course}/{user}/compile_server.log') as file:
                for line in file:
                    if "('COMPILE'," in line:
                        line = ast.literal_eval(line)
                        answers[line[2][1][1]].append([line[2][1][6], 2, line[0]])
        except (IndexError, FileNotFoundError):
            pass
        for value in answers.values():
            value.sort(key=lambda x: x[2]) # Sort by timestamp
    return answers, blurs

def question_source(config, comment, where, user, question, answers, blurs):
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
        source, _what, timestamp = infos
        if timestamp < current:
            continue
        if last_source == source:
            continue
        last_source = source
        current = timestamp
        content.append(f"""
{comment} ------------------------------------------------------------------
{comment} {time.ctime(timestamp)} : {what}
{comment} ------------------------------------------------------------------

{source}
""")

    return ''.join(content)

async def adm_answers(request):
    """Get students answers"""
    _session = await get_admin_login(request)
    course = request.match_info['course']
    assert '/.' not in course and course.endswith('.zip')
    course = utilities.get_course(course[:-4])
    config = utilities.CourseConfig(course)
    fildes, filename = tempfile.mkstemp()
    if config.compiler == 'SQL':
        comment = '-- '
        extension = 'sql'
    elif config.compiler == 'PYTHON':
        comment = '# '
        extension = 'py'
    elif config.compiler in ('REMOTE', 'CPP'):
        comment = '//'
        extension = 'cpp'
    elif config.compiler == 'JS':
        comment = '//'
        extension = 'js'
    else:
        comment = '// '
        extension = config.compiler
    try:
        zipper = zipfile.ZipFile(os.fdopen(fildes, "wb"), mode="w")
        for user in sorted(os.listdir(course)):
            await asyncio.sleep(0)
            answers, blurs = get_answers(course, user, compiled=True)
            infos = config.active_teacher_room.get(user)
            building, pos_x, pos_y, version = ((infos[2] or '?') + ',?,?,?').split(',')[:4]
            version = version.upper()
            where = f'Surveillant: {infos[1]}, {building} {pos_x}×{pos_y}, Version: {version}'
            if answers:
                zipper.writestr(
                    f'{course}/{user}#answers.{extension}',
                    ''.join(
                        question_source(config, comment, where, user, question, answers[question], blurs)
                        for question in answers
                    ))
        zipper.close()
        with open(filename, 'rb') as file:
            data = file.read()
    finally:
        os.unlink(filename)
        del zipper

    return response(data, content_type='application/zip')

async def update_file(request, session, compiler, replace):
    """Update questionnary on disc if allowed"""
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
        return f"«{src_filename}» invalid name (/)!"
    if replace and replace != src_filename:
        return f"«{src_filename}» is not equal to «{replace}»!"
    compiler_py = 'compile_' + compiler.lower() + '.py'
    if not os.path.exists(compiler_py):
        return f"«{src_filename}» use a not defined compiler: «{compiler_py}»!"

    dst_filename = f'COMPILE_{compiler}/{replace or src_filename}'
    if not replace and os.path.exists(dst_filename):
        return f"«{dst_filename}» file exists!"

    # All seems fine

    with open(dst_filename, "wb") as file:
        file.write(filehandle.file.read())

    process = await asyncio.create_subprocess_exec("make", dst_filename[:-3] + '.js')
    await process.wait()
    if replace:
        return f"«{src_filename}» replace «{dst_filename}» file"

    config = utilities.CourseConfig.get(dst_filename[:-3])
    config.set_parameter('creator', session.login)
    config.set_parameter('stop', '2000-01-01 00:00:01')
    return f"Course «{src_filename}» added into «{dst_filename}» file"


async def upload_course(request):
    """Add a new course"""
    session = await utilities.Session.get(request)
    error = None
    compiler = request.match_info['compiler']
    replace = request.match_info['course']
    if replace == '_new_':
        replace = False
    if replace:
        course = utilities.CourseConfig.get(f'COMPILE_{compiler.upper()}/{replace}')
        if not session.is_admin(course):
            error = "Session change is not allowed!"
        replace += '.py'
    else:
        if not session.is_author():
            error = "Session adding is not allowed!"
    if not error:
        error = await update_file(request, session, compiler, replace)
    if '!' not in error and not replace:
        raise web.HTTPFound(f'https://{utilities.C5_URL}/checkpoint/*?ticket={session.ticket}')
    if '!' in error:
        style = 'background:#FAA;'
    else:
        style = ''
    return response('<style>BODY {margin:0px;font-family:sans-serif;}</style>'
        + '<div style="height:100%;' + style + '">'
        + error + '</div>')

async def config_reload(request):
    """For regression tests"""
    _session = await utilities.Session.get(request)
    utilities.CONFIG.load()
    return response('done')

def tipped(logins):
    """The best way to display truncated text"""
    logins = re.split('[ \t\n]+', logins.strip())
    if not logins:
        return '<td class="names"><div></div>'
    if len(logins) == 1:
        return '<td class="clipped names"><div>' + logins[0] + '</div>'
    return '<td class="tipped names"><div>' + ' '.join(logins) + '</div>'

def checkpoint_line(session, course, content):
    """A line in the checkpoint table"""
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
    status = course.status('')
    content.append(f'''
    <tr style="{'background:#AFA;' if course.highlight else ''}
               {'opacity:0.3;' if course.disabled else ''}
    ">
    <td class="clipped course"><div>{course.course.split('=')[1]}</div>
    <td class="clipped compiler"><div>{course.course.split('=')[0].title()}</div>
    <td>{len(course.active_teacher_room) or ''}
    <td>{len(waiting) if course.checkpoint else ''}
    <td>{len(with_me) or ''}
    <td style="white-space: nowrap">{course.start if course.start > "2001" else ""}
    <td style="white-space: nowrap">{course.stop if course.stop < "2100" else ""}
    <td {'style="background:#8F8"'
            if course.start > "2001"
            and course.stop < "2100"
            and status.startswith('running')
            else ''}
    >{'Exam' if course.checkpoint else ''}
    <td> {
        f'<a target="_blank" href="/adm/session/{course.course}?ticket={session.ticket}">Edit</a>'
        if session.is_admin(course) else ''
    }
    <td> {
        f'<a target="_blank" href="/={course.course}?ticket={session.ticket}">Try</a>'
        if status.startswith('running') or session.is_grader(course)
        else ''
    }
    <td> {
        f'<a target="_blank" href="/checkpoint/{course.course}?ticket={session.ticket}">Place</a>'
        if session.is_proctor(course) else ''
    }
    <td class="clipped names"><div>{course.creator}</div>
    {tipped(course.config['admins'])}
    {tipped(course.config['graders'])}
    {tipped(course.config['proctors'])}
    </tr>''')

def checkpoint_table(session, courses, test, content, done):
    """A checkpoint table"""
    for course in courses:
        if test(course):
            if course not in done:
                checkpoint_line(session, course, content)
                done.add(course)

async def checkpoint_list(request):
    """Liste all checkpoints"""
    session = await utilities.Session.get(request)
    titles = '''<tr><th>Session<th>Comp<br>iler<th>Stud<br>ents<th>Wait<br>ing<th>With<br>me
        <th>Start date<th>Stop date<th>Exam<th>Edit<th>Try<th>Waiting<br>Room
        <th>Creator<th>Admins<th>Graders<th>Proctors</tr>'''
    content = [
        session.header(),
        '''
        <title>SESSIONS</title>
        <style>
        BODY { font-family: sans-serif }
        TABLE { border-spacing: 0px; border: 1px solid #AAA }
        TABLE TD, TABLE TH { border: 1px solid #AAA ; padding: 2px }
        TABLE TD.course DIV { width: 11em; }
        TABLE TD.compiler DIV { width: 3em; }
        TABLE TD.clipped DIV { overflow: hidden }
        TABLE TR:hover TD.clipped:first-child DIV,
        TABLE TD.clipped:hover DIV
                 { background: #FF0; overflow: visible; position: absolute;
                                         width: auto; padding-right: 1em }
        TR:hover TD {
            border-bottom: 3px solid #000 ;
            padding-bottom: 0px;
            border-top: 3px solid #000 ;
            padding-top: 0px;
            }
        TD { vertical-align: top }
        TD.names DIV { width: 6em ; }
        TD.tipped DIV { white-space: nowrap; overflow: hidden }
        TD.tipped:hover DIV { background: #FFE ; overflow: visible; position: absolute;
                              white-space: normal; margin-left: 3em; border: 1px solid #880;
                              margin-top: -1em; width: 10em; padding: 0.5em; }
        TD.tipped:hover { background: #FF0 }
        TH.header { background: #55F; color: #FFF }
        TH { background: #EEF }
        A { text-decoration: none }
        FORM { display: inline-block }
        FORM INPUT { display: none }
        FORM SPAN { border: 1px outset #888; border-radius: 0.5em; background: #EEE; padding: 0.2em }
        FORM SPAN:hover { border: 1px inset #888; background: #DDD }
        </style>
        <table>''']
    def hide_header():
        if '<th>' in content[-1]:
            content.pop()
            content[-1] = content[-1].replace('<th', '<th style="color:#AAF"')
    def add_header(label):
        hide_header()
        content.append(f'<tr><th class="header" colspan="{titles.count("th")}">{label}</tr>')
        content.append(titles)
    utilities.CourseConfig.load_all_configs()
    now = time.time()
    courses = [
        course
        for course in sorted(utilities.CourseConfig.configs.values(),
            key=lambda i: i.course.split('=')[::-1])
        if session.is_proctor(course) or course.status('').startswith('running')
        ]
    done = set()
    # add_header("Sessions I created")
    # checkpoint_table(session, courses,
    #     lambda course: course.creator == session.login,
    #     content, done)
    # add_header("Sessions I am allowed to modify")
    # checkpoint_table(session, courses,
    #     lambda course: session.is_course_admin(course),
    #     content, done)
    # add_header("Sessions of examination running or not yet started")
    # checkpoint_table(session, courses,
    #     lambda course: now < course.stop_tt_timestamp and course.checkpoint,
    #     content, done)
    add_header("Sessions not yet started")
    checkpoint_table(session, courses,
        lambda course: now < course.start_timestamp,
        content, done)
    add_header("Sessions running")
    checkpoint_table(session, courses,
        lambda course: course.start_timestamp <= now <= course.stop_tt_timestamp,
        content, done)
    add_header("Sessions done")
    checkpoint_table(session, courses,
        lambda course: now > course.stop_tt_timestamp,
        content, done)
    hide_header()
    content.append('</table>')
    if session.is_author():
        content.append('''
        <script>
        function change(t)
        {
            var s = document.createElement('SCRIPT');
            s.src = '/config/disable/' + t.value + '?ticket=' + TICKET;
            document.body.appendChild(s);
        }
        </script>
        <p>Disable all the sessions with a name (without the compiler) matching this regular expression:
        <input onchange="change(this)" value="''')
        content.append(utilities.CONFIG.config['disabled'].get(session.login, ''))
        content.append('">')
        content.append("<p>Download a Python file to add a new session for the compiler: ")
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

    return response(''.join(content))

async def checkpoint(request):
    """Display the students waiting checkpoint"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
    return response(
        session.header() + f'''
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
        ''')

async def update_browser_data(course):
    """Send update values"""
    return response(
        f'''
        STUDENTS = {json.dumps(await course.get_students())};
        MESSAGES = {json.dumps(course.messages)};
        CONFIG.computers = {json.dumps(utilities.CONFIG.computers)};
        ''',
        content_type='application/javascript')

async def update_browser(request):
    """Send update values"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
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
    if allow is None and not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
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
    if session.is_student() and not session.is_proctor(course):
        return response('''<script>document.body.innerHTML = "C'est fini."</script>''')
    return await update_browser_data(course)

async def checkpoint_bonus(request):
    """Set student time bonus"""
    student = request.match_info['student']
    bonus = request.match_info['bonus']
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
    seconds = int(time.time())
    old = course.active_teacher_room[student]
    old[7] = int(bonus)
    utilities.student_log(course.dirname, student, f'[{seconds},["time bonus",{bonus},"{session.login}"]]\n')
    course.record()
    return await update_browser_data(course)

async def home(request):
    """Test the user rights to display the good home page"""
    session = await utilities.Session.get(request)
    if session.is_root():
        return await adm_root(request)
    if not session.is_student():
        return await checkpoint_list(request)
    # Student
    utilities.CourseConfig.load_all_configs()
    now = time.time()
    content = [session.header()]
    for course_name, course in sorted(utilities.CourseConfig.configs.items()):
        if now > course.stop_tt_timestamp:
            continue # No more running
        if now < course.start_timestamp and not course.highlight:
            continue # Not started nor highlighted
        if course.disabled:
            continue
        if course.highlight:
            style = ' style="background: #8F8"'
        else:
            style = ''
        content.append(
            f'<li> <a href="/={course.course}?ticket={session.ticket}"{style}>{course_name}</a>')

    return response(''.join(content))

async def checkpoint_buildings(request):
    """Building list"""
    _ = await utilities.Session.get(request)
    buildings = {}
    for filename in os.listdir('BUILDINGS'):
        with open('BUILDINGS/' + filename) as file:
            buildings[filename] = file.read()
    return response(
        f'BUILDINGS = {json.dumps(buildings)};',
        content_type='application/javascript')

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
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
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

    return response(
        f'''spy({json.dumps(answers)},
               {json.dumps(student)},
               {json.dumps(await utilities.LDAP.infos(student))})''',
        content_type='application/javascript')

async def checkpoint_message(request):
    """The last answer from the student"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_proctor(course):
        raise session.message('not_proctor', exception=True)
    course.messages.append([session.login, int(time.time()), request.match_info['message']])
    course.set_parameter('messages', course.messages)
    return response(
        f'''MESSAGES.push({json.dumps(course.messages[-1])});ROOM.update_messages()''',
        content_type='application/javascript')

async def course_config(request):
    """The last answer from the student"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_admin(course):
        raise session.message('not_admin', exception=True)
    return response(
        f'update_course_config({json.dumps(course.config)})',
        content_type='application/javascript')

async def adm_session(request):
    """Session configuration for administrators"""
    session, course = await get_teacher_login_and_course(request)
    if not session.is_admin(course):
        raise session.message('not_admin', exception=True)

    return response(
        session.header()
        + f'<script>COURSE = {json.dumps(course.course)};</script>'
        + f'<script src="/adm_session.js?ticket={session.ticket}"></script>')

async def adm_editor(request):
    """Session questions editor"""
    session, course = await get_teacher_login_and_course(request)
    is_admin = session.is_admin(course)
    if not is_admin:
        return response("Vous n'êtes pas autorisé à modifier les questions.")
    session.edit = course # XXX If server is restarted, this attribute is lost
    return await editor(session, is_admin, course, session.login, author=1)

async def config_disable(request):
    """Session questions editor"""
    session = await utilities.Session.get(request)
    if session.is_student():
        raise session.message('not_teacher', exception=True)
    disabled = utilities.CONFIG.config['disabled']
    value = request.match_info['value']
    if value:
        disabled[session.login] = value
    elif session.login in disabled:
        del disabled[session.login]
    else:
        return response('', content_type='application/javascript') # No change
    utilities.CONFIG.set_value('disabled', disabled)
    return response('window.location.reload()', content_type='application/javascript')

APP = web.Application()
APP.add_routes([web.get('/', home),
                web.get('/{filename}', handle()),
                web.get('/node_modules/{filename:.*}', handle('node_modules')),
                web.get('/HIGHLIGHT/{filename:.*}', handle('HIGHLIGHT')),
                web.get('/adm/get/{filename:.*}', adm_get),
                web.get('/adm/answers/{course:.*}', adm_answers),
                web.get('/adm/root', adm_root),
                web.get('/adm/session/{course}', adm_session), # Edit page
                web.get('/adm/session/{course}/{action}/{value}', adm_config),
                web.get('/adm/session/{course}/{action}/', adm_config),
                web.get('/adm/course/{course}', adm_course),
                web.get('/adm/editor/{course}', adm_editor),
                web.get('/adm/c5/{action}/{value}', adm_c5),
                web.get('/config/reload', config_reload),
                web.get('/config/disable/{value}', config_disable),
                web.get('/course_config/{course}', course_config),
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
                web.get('/grade/{course}/{login}', grade),
                web.post('/upload_course/{compiler}/{course}', upload_course),
                web.post('/log', log),
                web.post('/record_grade/{course}', record_grade),
                web.post('/record_comment/{course}', record_comment),
                ])
APP.on_startup.append(startup)
logging.basicConfig(level=logging.DEBUG)

class AccessLogger(AbstractAccessLogger): # pylint: disable=too-few-public-methods
    """Logger for aiohttp"""
    def log(self, request, response, run_time): # pylint: disable=arguments-differ
        path = request.path.replace('\n', '\\n')
        session = utilities.Session.session_cache.get(request.query_string.replace('ticket=', ''), None)
        if session:
            login = session.login
        else:
            login = ''
        print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {response.status} "
              f"{run_time:5.3f} {request.method[0]} "
              f"{request.query_string.replace('ticket=ST-', '').split('-')[0]} "
              f"{login} "
              f"{path}",
              flush=True)

web.run_app(APP, host=utilities.C5_IP, port=utilities.C5_HTTP,
            access_log_format="%t %s %D %r", access_log_class=AccessLogger,
            ssl_context=utilities.get_certificate(False))
