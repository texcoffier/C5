"""
Grading Ladder compiler
"""

class Session(Compile): # pylint: disable=undefined-variable,invalid-name
    """MD compiler"""
    default_options = {'language': '', 'extension': 'gl'}

    def run_compiler(self, source):
        """Nothing to do"""
        self.post('compiler', 'ok')
        self.grades = Grades([['', source]])
        with_keys = self.grades.with_keys()
        if with_keys != source:
            self.post('editor', with_keys)
        return source
    def run_executor(self):
        """Execute the compiled code"""
        content = []
        self.grades.get_html(content, '')
        self.post('executor', ' <div class="grading" id="grading">' + ''.join(content) + '</div>')

    def run_tester(self):
        t = ['''
        <style>
        .grade_stats { border-spacing: 0px; }
        .grade_stats TD { border: 1px solid #888; }
        </style>
        <table class="grade_stats">
        <tr><th>Key<th>Label<th>Grades</tr>''']
        for grade in self.grades.content:
            if len(grade.grades):
                if grade.is_competence:
                    competence = ' style="background: #FFF"'
                else:
                    competence = ''
                t.append(
                    '<tr' + competence +'><td>' + grade.key
                    + '<td>' + grade.label
                    + '<td>' + ' '.join(grade.grades)
                    + '</tr>')
        t.append('</table>')
        t.append('Nbr compétences : ' + self.grades.nr_competences + '<br>')
        t.append('Nbr grades : ' + self.grades.nr_grades + '<br>')
        t.append('Max grade : ' + self.grades.max_grade + '<br>')
        self.post('tester', ''.join(t))
        line_nr = 1
        for grade in self.grades.content:
            before = grade.text_before.split('\n')
            line_nr += len(before) - 1
            char_nr = len(before[-1]) + 2
            if len(grade.grades):
                self.post('warning', [line_nr, char_nr])
