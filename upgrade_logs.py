#!/usr/bin/python3

"""
Convert all logs from version 1 to new logs of version 2
"""

import os
import ast
import json
import glob
import collections
import common
import utilities
import http_server

# Should retrieve EXIT value?
#          self.log(("EXIT", return_value))

def get_answers_old(course, user, compiled=False): # pylint: disable=too-many-branches,too-many-locals
    """Get question answers.
       The types are:
         * 0 : saved source
         * 1 : source passing the test
         * 2 : compilation (if compiled is True)
         * 3 : snapshot (5 seconds before examination end)
    Returns 'answers' and 'blurs'
    answers is a dict from question to a list of [source, type, timestamp, tag]
    """
    answers = collections.defaultdict(list)
    blurs = collections.defaultdict(int)
    try:
        with open(f'{course}/{user}/http_server.log', encoding='utf-8') as file:
            question = 0
            for line in file: # pylint: disable=too-many-nested-blocks
                line = line.strip()
                if not line:
                    continue
                seconds = 0
                for cell in json.loads(line):
                    if isinstance(cell, list):
                        what = cell[0]
                        if what == 'answer':
                            answers[cell[1]].append((cell[2], 1, seconds, ''))
                        elif what == 'save':
                            answers[cell[1]].append((cell[2], 0, seconds, ''))
                        elif what == 'snapshot':
                            answers[cell[1]].append((cell[2], 3, seconds, ''))
                        elif what == 'question':
                            question = cell[1]
                        elif what == 'tag':
                            timestamp = cell[2]
                            tag = cell[3]
                            if timestamp:
                                for i, saved in enumerate(answers[cell[1]]):
                                    if saved[2] == timestamp:
                                        answers[cell[1]][i] = (saved[0], saved[1], saved[2], tag)
                            else:
                                item = answers[cell[1]][-1]
                                answers[cell[1]][-1] = (item[0], item[1], item[2], tag)
                    elif isinstance(cell, str):
                        if cell == 'Blur':
                            blurs[question] += 1
                    else:
                        seconds += cell
    except IOError:
        return {}, {}

    if compiled:
        try:
            with open(f'{course}/{user}/compile_server.log', encoding='utf-8') as file:
                for line in file:
                    if "('COMPILE'," in line:
                        line = ast.literal_eval(line)
                        answers[int(line[2][1][1])].append((line[2][1][6], 2, int(line[0]), ''))
        except (IndexError, FileNotFoundError):
            pass
        for value in answers.values():
            value.sort(key=lambda x: x[2]) # Sort by timestamp
    return answers, blurs


def get_comments(course, user):
    """
    Analyse comments.log
    """
    all_comments = {}
    try:
        for infos in open(f'{course}/{user}/comments.log', 'r', encoding='utf-8'):
            if not infos:
                continue
            timestamp, login, question, version, line, comment = json.loads(infos)
            if question not in all_comments:
                all_comments[question] = {}
            if version not in all_comments[question]:
                all_comments[question][version] = {}
            all_comments[question][version][line] = (timestamp, login, comment)
            # ANSWERS[question][1] = version # Want to see the commented version
    except OSError:
        return {}
    return all_comments

def get_answers(course, user):
    """
    Merge http_server.log and compile_server.log for a student
    """
    compilations = []
    try:
        with open(f'{course}/{user}/compile_server.log', encoding='utf-8') as file:
            for line in file:
                if "('COMPILE'," in line:
                    compile_line = ast.literal_eval(line)
                if "('ERRORS'," in line:
                    error_line = ast.literal_eval(line)
                    compilations.append((
                        int(error_line[0]),    # Timestamp
                        compile_line[2][1][1], # Question
                        error_line[2],         # ERRORS #errors #warnings
                        compile_line[2][1][6]  # Source
                        ))
    except FileNotFoundError:
        pass

    journal = common.Journal()

    def append(value, delta_t=10):
        #print("*****", len(journal.content), repr(value[:30]))
        if seconds - int(journal.timestamp) >= delta_t:
            journal.append(f'T{seconds}')
        journal.append(value)
        #print(">>>>>", len(journal.content), repr(value[:30]))

    def diff(content):
        for insert, pos, value in common.compute_diffs(journal.content, content):
            line_number = max(0, journal.content[:pos].count('\n') - 5)
            append(f'L{line_number}')
            append(f'P{pos}')
            if insert:
                value = common.protect_crlf(value)
                append(f'I{value}')
            else:
                append(f'D{value}')
        if content != journal.content:
            journal.dump()
            print(repr(content))
            print(repr(journal.content))
            raise ValueError('bug1')

    def next_compile():
        try:
            (next_compile.timestamp, next_compile.question,
             (_, next_compile.errors, next_compile.warnings), next_compile.source) = next(compiles)
        except: # pylint: disable=bare-except
            next_compile.timestamp = 1e50


    compiles = iter(compilations)
    next_compile()
    last_version = collections.defaultdict(lambda: [None, None, None, None])
    tag_number = 1
    with open(f'{course}/{user}/http_server.log', encoding='utf-8') as file:
        for line in file: # pylint: disable=too-many-nested-blocks
            line = line.strip()
            if not line:
                continue
            seconds = 0
            for cell in json.loads(line):
                if seconds > next_compile.timestamp and journal.question >= 0:
                    # Insert a compilation before
                    if journal.question != next_compile.question:
                        append(f'Q{next_compile.question}')
                        # print('BAD QUESTION')
                    if next_compile.source != journal.content:
                        journal.append(f'T{next_compile.timestamp}')
                        next_compile.timestamp = 1e50
                        diff(next_compile.source)
                        journal.append(f'c{100*next_compile.errors+next_compile.warnings}')
                        last_version[journal.question][2] = (len(journal.lines), journal.content)
                    next_compile()
                if isinstance(cell, list):
                    what = cell[0]
                    if what in ('answer', 'save', 'snapshot'):
                        version_id = {'answer': 2, 'save': 0, 'snapshot': 3}[what]
                        diff(cell[2])
                        append(f'S{what}')
                        if what == 'answer':
                            append('g')
                        else:
                            append(f't{tag_number}')
                            tag_number += 1
                        last_version[journal.question][version_id] = (
                            len(journal.lines), journal.content)
                    elif what == 'question':
                        question = int(cell[1])
                        if journal.question != question:
                            if question in journal.questions:
                                append(f'G{journal.questions[question].head}')
                            else:
                                append(f'Q{cell[1]}')
                    elif what == 'tag':
                        timestamp = cell[2]
                        tag = cell[3]
                        try:
                            i = journal.lines.index(f'T{timestamp}')
                            for j in range(i+1, len(journal.lines)):
                                if journal.lines[j].startswith('G'):
                                    k = int(journal.lines[j][1:])
                                    if k > i:
                                        journal.lines[j] = f'G{k+1}'
                            journal.lines.insert(i+1, f't{tag}')
                            journal = common.Journal('\n'.join(journal.lines) + '\n')
                        except ValueError:
                            print(f'Unknown timestamp {cell}')
                    elif what == 'checkpoint_in':
                        append(f'O{user} {cell[1]}')
                elif isinstance(cell, str):
                    if cell in ('Focus', 'Blur'):
                        append(cell[0], delta_t=0)
                else:
                    seconds += cell

    all_comments = get_comments(course, user)
    for question_id, versions in last_version.items():
        if question_id not in all_comments:
            continue
        for version_id in (3, 2, 1, 0):
            if version_id not in all_comments[question_id]:
                continue
            comments = all_comments[question_id][version_id].items()
            if not comments:
                continue
            if not versions[version_id]:
                continue
            line_number, content = versions[version_id]
            journal.append(f'G{line_number}')
            lines = content.split('\n')
            for line_number, (timestamp, login, comment) in comments:
                if line_number >= len(lines):
                    line_number = len(lines) - 1
                start = len('\n'.join(lines[:line_number])) + 1
                end = start + max(len(lines[line_number]), 1)
                comment_lines = comment.split('\n')
                height = len(comment_lines)
                width = 0
                for i in comment_lines:
                    if len(i) > width:
                        if len(i) > 44:
                            width = 44
                            height += 1
                        else:
                            width = len(i)
                comment = common.protect_crlf(comment)
                journal.append(f'T{timestamp}')
                width = width*0.6 + 1
                height += 0.4
                journal.append(f'b+{login} {start} {end} 0 30 {width:.1f} {height} {comment}')


    return journal.lines


def main():
    before = 0
    after = 0
    sessions = {}
    filenames = glob.glob('*/*/LOGS/*/http_server.log')
    # filenames = glob.glob('COMPILE_REMOTE/LIFAPI_2024_Seq1_TPNote1/LOGS/*/http_server.log')
    # filenames = ['COMPILE_REMOTE/LIFAPR_2024_TPnoteMardi/LOGS/p2102953/http_server.log']
    for filename in filenames:
        size_in = os.path.getsize(filename)
        try:
            size_in += os.path.getsize(filename.replace('/http_', '/compile_'))
        except FileNotFoundError:
            pass

        print(filename, end=' ')
        compile_name, session_name, _, user, _ = filename.split('/')
        session = f'{compile_name}/{session_name}'
        if session not in sessions:
            sessions[session] = utilities.CourseConfig(session)
        course = f'{session}/LOGS'
        lines = get_answers(course, user)
        infos = sessions[session].active_teacher_room.get(user, None)
        if infos and infos.bonus_time:
            lines.append(f'#bonus_time {infos.bonus_time} 0')
        lines = get_answers(course, user)
        size_out = len('\n'.join(lines))

        with open(f'{course}/{user}/journal.log', 'w', encoding='utf-8') as file:
            file.write('\n'.join(lines) + '\n')
        olds1, olds2 = get_answers_old(course, user, compiled=True)
        news1, news2 = http_server.get_answers(course, user, compiled=True)

        print(f'{size_in} → {size_out} {len(olds1)}/{len(olds2)} → {len(news1)}/{len(news2)}')

        if size_out > 0.9 * size_in and size_in > 10000:
            print('*'*999)
        before += size_in
        after += size_out

        if olds1 != news1 and news1:
            for k, value in olds1.items():
                print("  OLD", k, value)
            for k, value in news1.items():
                print("  NEW", k, value)
        if olds2 != news2 and news2:
            print(olds2)
            print(news2)

    print(before, after, before/after)

main()
