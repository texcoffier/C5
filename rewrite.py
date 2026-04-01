#!/bin/env python3

"""
The argument:
  * A question filename as: COMPILE_REMOTE/template/questions.js

Generate :
  * COMPILE_REMOTE/template/questions.loads             # The list of used file
  * COMPILE_REMOTE/template/questions+.js               # The source to compile for student
  * COMPILE_REMOTE/template/questions+GRADING.js        # + Grading ladder
  * COMPILE_REMOTE/template/questions+ANSWER.js         # + Answers
  * COMPILE_REMOTE/template/questions+ANSWER+GRADING.js # + Grading ladder + Answers
"""

import sys
import re
import collections
import json
import os

class Rewriter:
    def __init__(self, filename_js):
        """Creating this instance creates all the files"""
        self.js = filename_js
        assert self.js.endswith('/questions.js')

        self.src = self.js.replace('questions.js', 'SRC/')

        with open(self.js, 'r', encoding='utf-8') as file:
            self.lines = file.readlines()

        self.analyse()
        self.generate_files()
        self.generated_index_of_loaded_files()
        self.report()

    def analyse(self):
        """Parse the javascript file to find all LOAD_..."""
        self.replacements = []
        self.errors = collections.defaultdict(list)
        self.questions = {}

        # Search LOAD in the Javascript file
        for i, line in enumerate(self.lines):
            name = re.findall(r'^var ([a-zA-Z_0-9]*) = \(ՐՏ_[0-9]+ = function \1\(\) {', line)
            if name:
                question = name[0]
                self.questions[question] = collections.defaultdict(list)
                continue
            load = re.findall(
                r'''(LOAD_(QUESTION|DEFAULT|GRADING|ANSWER) *\( *(["'])([^"']*)\3 *\))''',
                line)
            if load:
                full, action, _, filename = load[0]
                self.questions[question][action].append(filename)
                if '/' in filename or '..' in filename:
                    self.errors['Illegal filename'].append(filename)
                    replace = ''
                elif not os.path.exists(self.src + filename):
                    self.errors['File does not exists'].append(filename)
                    replace = ''
                else:
                    with open(self.src + filename, 'r', encoding='utf-8') as file:
                        replace = file.read()
                self.replacements.append((i, action, full, json.dumps(replace)))

    def generate_files(self):
        """Generated all the files even if not needed"""
        for filename in ('+', '+ANSWER', '+GRADING', '+ANSWER+GRADING'):
            new_content = list(self.lines)
            for i, action, full, replace in self.replacements:
                if action in filename or action in ('QUESTION', 'DEFAULT'):
                    new_content[i] = new_content[i].replace(full, replace)
                else:
                    new_content[i] = new_content[i].replace(full, "''")
            with open(self.js[:-3] + filename + '.js', 'w', encoding='utf-8') as file:
                file.write(''.join(new_content))

    def generated_index_of_loaded_files(self):
        """questions.loads contains JSON:
            {
              "QuestionName": { "QUESTION": ["quest_vers_A", ""quest_vers_B"],
                                "ANSWER": ["answer"],
                                "GRADING": ["grading"],
                                "DEFAULT": ["def_A", "def_B", "def_C"]
                              }
              ...
            } 
        """
        loads = self.js[:-3] + '.loads'
        try:
            os.rename(loads, loads + '~')
        except FileNotFoundError:
            pass
        with open(loads, 'w', encoding='utf-8') as file:
            file.write(json.dumps(self.questions))

    def report(self):
        """The work done"""
        for k, v in self.errors.items():
            print(f'{k}: {" ".join(sorted(set(v)))}')
        for q, v in self.questions.items():
            print(f'{q}: ' + ' '.join(sorted(set(sum(v.values(), [])))))

Rewriter(sys.argv[1])
