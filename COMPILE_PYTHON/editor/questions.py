"""An editor for questionnaries"""

if False: # pylint: disable=using-constant-test
    # pylint: disable=undefined-variable,invalid-name,self-assigning-variable
    Compile = Compile
    Question = Question
    PREAMBLE = PREAMBLE

COURSE_OPTIONS = {
    'title': "Session utilisée uniquement pour éditer les questionnaires",
    'allow_copy_paste': 1,
    'forbid_question_copy': 0,
    'state': 'Ready',
    'checkpoint': 0,
    'expected_students_required': 1, # Do not display to student
    'positions' : {
        'question': [1, 29, 0, 100, '#EFE'],
        'tester': [100, 29, 30, 70, '#EFE'],
        'editor': [30, 54, 0, 100, '#FFF'],
        'compiler': [84, 16, 0, 30, '#EEF'],
        'executor': [84, 16, 30, 70, '#EEF'],
        'time': [80, 20, 98, 2, '#0000'],
        'index': [0, 1, 0, 100, '#0000'],
        'line_numbers': [100, 1, 0, 100, '#EEE'], # Outside the screen by defaut
    }}

PREAMBLE += """
class Question:
    worker = __worker__
    nr_eval = -1
    def __init__(self):
        print(str(self).split('.')[1].split(' ')[0])
        default = self.default_answer()
        if __worker__.nr_eval != Question.nr_eval:
            __worker__.post('question', '<h2>Toutes les questions</h2>')
            Question.nr_eval = __worker__.nr_eval
        content = self.question()
        if default.strip() != '':
            content += '<pre style="background:#FFF">' + html(default) + '</pre>'
        __worker__.post('question', content + '<hr>')
for _key_ in __Question__.prototype:
    if not hasattr(Question, _key_):
        setattr(Question, _key_, __Question__.prototype[_key_])
__Question__.prototype.worker = __worker__

class Session:
    pass
millisecs = __millisecs__
html = __html__
"""
OFFSET = len(PREAMBLE.split('\n')) - 1

def compiler_initial_content(_self):
    """Use less space for title"""
    return "<h2>Compilation</h2>"

def executor_initial_content(_self):
    """Use less space for title"""
    return "<h2>Execution</h2>"

class Q1(Question):
    """Nothing"""
    def question(self): # pylint: disable=no-self-use
        """Redefine bloc titles
        The 'question' is used to have a feedback of defined questions.
        """
        Compile.worker.compiler_initial_content = compiler_initial_content
        Compile.worker.executor_initial_content = executor_initial_content
        return ""
    def append_to_source_code(self):
        """Create an instance of each questions"""
        call = []
        for line in self.worker.source.split('\n'):
            if line.startswith('class ') and '(Question)' in line:
                call.append(line.split(' ')[1].split('(')[0] + '()')
        return '\n'.join(call)
