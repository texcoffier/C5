#!/usr/bin/python3

"""Global statistics creation and display.

Need to add counting of I D S T ...

If launched with a session list has: COMPILE_REMOTE/*
It will display the histogram of median compile time between 2 compilation.

"""

# pylint: disable=invalid-name,multiple-statements,eval-used

import os
import sys
import collections
import json
import utilities

PAUSE_TIME = 10*60 # 10 minutes

class Stat:
    first_interaction = 1e100
    last_interaction = 0
    nr_compile_without_error = nr_compile_with_error = 0
    work_time = timestamp = 0
    last_compile = 0
    time_between_compile_stddev = None

    def __init__(self):
        self.question_dict = collections.defaultdict(int) # Nr questions see
        self.allow_edit_dict = collections.defaultdict(int) # Nr forbiden actions while compiling
        self.sessions = []
        self.grade = {}
        self.time_between_compile = []

    def parse(self, line):
        if line.startswith('T'):
            timestamp = int(line[1:])
            if timestamp - self.last_interaction < PAUSE_TIME:
                self.work_time += timestamp - self.last_interaction
                self.last_interaction = timestamp
            else:
                self.sessions.append(timestamp)
            if timestamp < self.first_interaction:
                self.first_interaction = timestamp
            self.work_time += timestamp - self.last_interaction
            self.last_interaction = timestamp
        elif line.startswith('c'):
            if self.last_compile:
                delta = self.last_interaction - self.last_compile
                self.time_between_compile.append(delta)
            self.last_compile = self.last_interaction
            if line.startswith('c0'):
                self.nr_compile_without_error += 1
            else:
                self.nr_compile_with_error += 1

    def parse_grade(self, line_txt):
        line = eval(line_txt)
        self.grade[line[2]] = line[3]

    def finalize(self):
        self.question_dict = dict(self.question_dict)
        self.allow_edit_dict = dict(self.allow_edit_dict)
        self.nr_sessions = len(self.sessions)
        if self.nr_sessions:
            self.sessions_last = self.sessions[-1]
            self.sessions_average = sum(self.sessions) / len(self.sessions)
            self.sessions_median = self.sessions[len(self.sessions) // 2]
        else:
            self.sessions_last = self.sessions_average = self.sessions_median = -1

        if self.grade:
            grade = []
            for i in self.grade.values():
                try:
                    grade.append(float(i))
                except ValueError:
                    pass
            self.grade = sum(grade)
        else:
            del self.grade
        if self.time_between_compile:
            self.time_between_compile.sort()
            self.time_between_compile = self.time_between_compile[len(self.time_between_compile)//2]
    def __repr__(self):
        return repr(self.__dict__)

def compile_stats(courses, create=True) -> None:
    """Create a resume for each session stats"""
    full = {}
    for session in courses:
        resume_file = f'{session.dir_session}/session.stats'
        if (os.path.exists(resume_file)
            and os.path.getmtime(resume_file) > os.path.getmtime(session.file_cf) - 86400):
            print(f'{session.dir_session} is yet up to date (may be 1 day late)')
            with open(resume_file, 'r', encoding='utf-8') as file:
                full[session.dir_session] = eval(file.read())
            continue
        if not os.path.exists(session.dir_log):
            continue
        print(session.dir_session, end=' ')
        students = collections.defaultdict(Stat)
        for student in os.listdir(session.dir_log):
            print(student, end=' ', flush=True)
            stat = students[student]
            if os.path.exists(session.dir_log + '/' + student + '/journal.log'):
                with open(session.dir_log + '/' + student + '/journal.log', 'r',
                        encoding='utf-8', newline='\n') as file:
                    for line in file:
                        stat.parse(line)
            if os.path.exists(session.dir_log + '/' + student + '/grades.log'):
                with open(session.dir_log + '/' + student + '/grades.log', 'r',
                        encoding='utf-8') as file:
                    for line in file:
                        stat.parse_grade(line)
        grades = []
        for student in students.values():
            student.finalize()
            if hasattr(student, 'grade'):
                grades.append(student.grade)
        print(grades)
        if grades:
            maximum_grade = max(grades)
            if maximum_grade:
                for student in students.values():
                    if hasattr(student, 'grade'):
                        student.grade /= maximum_grade

        content = repr(dict(students))
        with open(resume_file, 'w', encoding='utf-8') as file:
            file.write(content)
        full[session.dir_session] = eval(content)
        print()
    if create:
        with open('xxx-full-stats.js', 'w', encoding='utf-8') as file:
            file.write(f'{json.dumps(full)}')
        print(f"xxx-full-stats.js : {os.path.getsize('xxx-full-stats.js')} bytes")

def main():
    sessions = [
        utilities.CourseConfig.get(i)
        for i in sys.argv[1:]
        ]
    compile_stats(sessions, create=False)
    histo = [0] * 30
    size = 5
    for session in sessions:
        try:
            with open(session.dir_session + '/session.stats', 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            continue
        content = eval(content)
        for student in content.values():
            nr = student.get('nr_compile_without_error',0) + student.get('nr_compile_with_error', 0)
            if nr < 10:
                continue
            tbc = student['time_between_compile'] // size
            if tbc < len(histo):
                histo[tbc] += 1
    print('Number of seconds between 2 compiles (median for session with >10 compiles).')
    print('The number of «*» indicates the number of students with this median time.')
    nrmax = max(histo)
    for delta, nbr in enumerate(histo):
        print(f'{delta*size:3}-{delta*(size+1):<3} {"*"*int(80*nbr/nrmax)}')



if __name__ == '__main__':
    main()
