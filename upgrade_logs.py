#!/usr/bin/python3

import os
import ast
import json
import glob
import common
import http_server

"""
        _course, _question, compiler, compile_options, ld_options, allowed, source = data
        self.compiler = compiler
        self.log(("COMPILE", data))


        self.log(("ERRORS", stderr.count(': error:'), stderr.count(': warning:')))

            self.log(("EXIT", return_value))
"""

def get_answers_old(course:str, user:str, compiled:bool=False) -> Tuple[Answers, Blurs] : # pylint: disable=too-many-branches,too-many-locals
    """Get question answers.
       The types are:
         * 0 : saved source
         * 1 : source passing the test
         * 2 : compilation (if compiled is True)
         * 3 : snapshot (5 seconds before examination end)
    Returns 'answers' and 'blurs'
    answers is a dict from question to a list of [source, type, timestamp, tag]
    """
    answers:Answers = collections.defaultdict(list)
    blurs:Dict[int,int] = collections.defaultdict(int)
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

    def Append(value, dt=10):
        #print("*****", len(journal.content), repr(value[:30]))
        if seconds - int(journal.timestamp) >= dt:
            journal.append(f'T{seconds}')
        journal.append(value)
        #print(">>>>>", len(journal.content), repr(value[:30]))

    def Diff(content):
        for insert, pos, value in common.compute_diffs(journal.content, content):
            Append(f'P{pos}')
            if insert:
                value = value.replace("\n", "\0")
                Append(f'I{value}')
            else:
                Append(f'D{value}')
        if content != journal.content:
            journal.dump()
            print(repr(content))
            print(repr(journal.content))
            bug1

    def Next():
        try:
            Next.timestamp, Next.question, (_, Next.errors, Next.warnings), Next.source = next(compiles)
        except:
            Next.timestamp = 1e50


    compiles = iter(compilations)
    Next()
    with open(f'{course}/{user}/http_server.log', encoding='utf-8') as file:
        for line in file: # pylint: disable=too-many-nested-blocks
            line = line.strip()
            if not line:
                continue
            seconds = 0
            for cell in json.loads(line):
                if seconds > Next.timestamp and journal.question >= 0:
                    # Insert a compîlation before
                    if journal.question != Next.question:
                        print('BAD QUESTION', seconds, Next.timestamp, journal.question, Next.question)
                    elif Next.source != journal.content:
                        journal.append(f'T{Next.timestamp}')
                        Next.timestamp = 1e50
                        Diff(Next.source)
                        journal.append(f'c{100*Next.errors+Next.warnings}')
                    Next()
                if isinstance(cell, list):
                    what = cell[0]
                    if what in ('answer', 'save', 'snapshot'):
                        Diff(cell[2])
                        Append(f'S{what}', dt=0) # Timestamp needed for tagging
                    elif what == 'question':
                        question = int(cell[1])
                        if journal.question != question:
                            if question in journal.questions:
                                Append(f'G{journal.questions[question].head}')
                            else:
                                Append(f'Q{cell[1]}')
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
                            journal = common.Journal('\n'.join(journal.lines))
                        except ValueError:
                            print(f'Unknown timestamp {cell}')
                    elif what == 'checkpoint_in':
                        Append(f'O{user} {cell[1]}')
                elif isinstance(cell, str):
                    if cell in ('Focus', 'Blur'):
                        Append(cell[0], dt=0)
                else:
                    seconds += cell
    return journal.lines


def main():
    before = 0
    after = 0
    #filenames = ['COMPILE_REMOTE/LIFAPI_TD07/LOGS/p2303050/http_server.log']
    filenames = glob.glob('*/*/LOGS/*/http_server.log')
    for filename in filenames:
        size_in = os.path.getsize(filename)
        try:
            size_in += os.path.getsize(filename.replace('/http_', '/compile_'))
        except FileNotFoundError:
            pass

        if size_in > 4000:
            continue

        print(filename, end=' ')
        s, d, _, user, _ = filename.split('/')
        course = f'{s}/{d}/LOGS'
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
            for k, v in olds1.items():
                print("  OLD", k, v)
            for k, v in news1.items():
                print("  NEW", k, v)
        if olds2 != news2 and news2:
            print(olds2)
            print(news2)


    print(before, after, before/after)

main()