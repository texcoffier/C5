#!/bin/env python3

"""
Extract all the information about one login
"""

import sys
import os
import subprocess
import glob
import time

def record(name, content):
    name = name.replace('/', '§').replace('.gz', '')
    with open(f'XXX/{name}', 'wb') as file:
        file.write(content)
    return name

TICKETS = {}
class Ticket:
    def __init__(self, fullname, content):
        self.fullname = fullname
        self.name = fullname.split('-')[1]
        self.content = content
        self.ip, self.browser, self.login, self.date, _infos, _more = eval(content)
        self.date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.date))
        TICKETS[self.name] = self

INDEX = open('XXX/index.html', 'w')
def log(txt):
    INDEX.write(txt)

def load_tickets():
    for name in glob.glob('TICKETS/*'):
        with open(name, 'rb') as file:
            Ticket(name.split('/')[1], file.read())

def print_tickets(login):
    log('<h2>TICKETS</h2>')
    tickets = [ticket
         for ticket in TICKETS.values()
         if ticket.login == login
        ]
    tickets.sort(key=lambda t: t.date)
    log('<table><tr><th>Ticket ID<th>Date<th>IP</tr>')
    for t in tickets:
        name = record(t.fullname, t.content)
        log(f'<tr><td><a href="{name}">{t.name}</a><td>{t.date}<td>{t.ip}</tr>')
        TICKETS[t.fullname] = t
    log('<table>')

def load_sessions(login):
    login = login.encode('utf-8')
    for name in glob.glob('COMPILE_*/*/session.cf'):
        with open(name, 'rb') as file:
            content = file.read()
            if login not in content:
                continue
        log(f'<h2>Session {name}</h2>')
        newname = record(name, content)
        log(f'<a href="{newname}">Session full content</a>')
        log('<pre>')
        for line in content.split(b'\n'):
            if login in line:
                log(line.decode('utf-8') + '\n')
        log('</pre>')

        session = name.rsplit('/', 1)[0]
        journal = f'{session}/LOGS/{login.decode("utf-8")}/journal.log'
        if not os.path.exists(journal):
            continue
        with open(journal, 'rb') as file:
            content = file.read()
        newname = record(journal, content)
        log(f'<a href="{newname}">Student journal full content</a>')
        log('<pre>')
        for line in content.split(b'\n'):
            if line.startswith((b'#', b'O')):
                log(line.decode('utf-8') + '\n')
        log('</pre>')

def load_http_logs(login):
    log(f'<h2>http_server Log</h2>')
    login = login.encode('utf-8')
    for name in glob.glob('LOGS/20[0-9][0-9][0-9][0-9][0-9][0-9]-http_server*'):
        if name.endswith('.gz'):
            content = subprocess.run(['zcat', name], stdout=subprocess.PIPE).stdout
        else:
            with open(name, 'rb') as file:
                content = file.read()
        if login not in content:
            continue
        newname = record(name, content)
        log(f'{name} <a href="{newname}">Log full content</a>')
        log('<pre>')
        for line in content.split(b'\n'):
            if login in line:
                line = line.decode('utf-8')
                values = line.split(' ')
                for v in values:
                    if v in TICKETS:
                        ticket = TICKETS[v]
                        log(line.replace(f' {v} ', f' <a href="{ticket.fullname}">{ticket.ip}</a> ') + '\n')
                        break
                else:
                    log(line + '\n')
        log('</pre>')

def load_compile_logs(login):
    log(f'<h2>compile_server Log</h2>')
    login = f"'{login}',".encode('utf-8')
    session_ids = []
    for name in glob.glob('LOGS/20[0-9][0-9][0-9][0-9][0-9][0-9]-compile_server*'):
        if name.endswith('.gz'):
            content = subprocess.run(['zcat', name], stdout=subprocess.PIPE).stdout
        else:
            with open(name, 'rb') as file:
                content = file.read()
        if login not in content:
            continue
        newname = name.replace('/', '§')
        record(newname, content)
        log(f'{name} <a href="{newname}">Log full content</a>')
        log('<pre>')
        for line in content.split(b'\n'):
            cells = line.split(b' ')
            if len(cells) > 4 and cells[4] == login:
                session_ids.append(cells[1])
                ticket = TICKETS[cells[3].strip(b",'").decode('utf-8')]
                log(f'<b>Start session {cells[1].decode("ascii")} for ticket <a href={ticket.fullname}>{ticket.name}</a> {ticket.ip}</b>\n') 
            if len(cells) > 1 and cells[1] in session_ids:
                log(line.decode('utf-8') + '\n')
        log('</pre>')


def main():
    login = sys.argv[1]
    log(f'<h1>Log extraction for «{login}»</h1>')
    load_tickets()
    print_tickets(login)
    load_http_logs(login)
    load_compile_logs(login)

    load_sessions(login)

print("Look at XXX/index.html once the script is done")
main()
