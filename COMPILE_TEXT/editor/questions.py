"""An editor for questionnary media"""

COURSE_OPTIONS = {
    'title': "Session utilisée uniquement pour éditer des media de type textes",
    'allow_copy_paste': 1,
    'forbid_question_copy': 0,
    'state': 'Ready',
    'checkpoint': 0,
    'expected_students': 'nobody', # Do not display to student
    'automatic_compilation': 1,
    'positions' : {
        'question': [1, 29, 0, 20, '#EFE'],
        'tester': [1, 29, 20, 100, '#EFE'],
        'editor': [30, 70, 0, 100, '#FFF'],
        'compiler': [100, 16, 0, 30, '#EEF'],
        'executor': [100, 16, 30, 70, '#EEF'],
        'time': [100, 20, 98, 2, '#0000'],
        'index': [0, 1, 0, 100, '#0000'],
    }}

class Q1(Question):
    """Nothing"""
    def question(self): # pylint: disable=no-self-use
        """User help
        """
        infos = self.worker.options['REAL_COURSE']
        return ("Save to compile the new session version."
            + '<ul>'
            + "<li> Session: " + infos.split(':')[0]
            + "<li> File: " + infos.split(':')[1]
            + '</ul>')

    def tester(self):
        self.display(
            len(self.worker.source) + ' characters' + '<br>'
            + len(self.worker.source.split(RegExp('[^a-zA-Z0-9]+'))) + ' words<br>'
            + len(self.worker.source.split('\n')) + ' lines'
        )
