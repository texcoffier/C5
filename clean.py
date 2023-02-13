#!/usr/bin/python3

"""
Clear garbage from regression tests
"""

import os
import glob
import shutil
import ast
import json

print('Cleanup c5.cf')
with open('c5.cf', 'r', encoding='utf-8') as file:
    cf = json.loads(file.read())
for key in ('roots', 'masters', 'authors'):
    cf[key] = [login
                    for login in cf[key]
                    if not login.startswith('Anon_')
                    ]
with open('c5.cf', 'w', encoding='utf-8') as file:
    file.write(json.dumps(cf))

print('Remove tickets: ', end='')
for filename in glob.glob('TICKETS/[1-9]*[0-9]'):
    print('*', end='')
    os.unlink(filename)
print()

print('Remove log dirs: ', end='')
for dirname in glob.glob('COMPILE_*/*/Anon_*'):
    print('*', end='')
    shutil.rmtree(dirname)
print()

print('Clear session configs: ', end='')
for cfname in glob.glob('COMPILE_*/*.cf'):
    with open(cfname, 'r', encoding='utf-8') as file:
        cf = ast.literal_eval(file.read())
    students = cf['active_teacher_room']
    new_students = {
        key: value
        for key, value in students.items()
        if not key.startswith('Anon_')
    }
    if students == new_students:
        continue
    print(cfname, end=' ')
    cf['active_teacher_room'] = new_students
    with open(cfname, 'w', encoding='utf-8') as file:
        file.write(repr(cf))
print()
