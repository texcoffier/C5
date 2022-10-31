

COURSE_OPTIONS = {'positions' : {
    'question': [1, 46, 0, 30, '#EFE'],
    'tester': [1, 46, 30, 70, '#EFE'],
    'editor': [50, 50, 0, 100, '#FFF'],
    'compiler': [100, 30, 0, 30, '#EEF'],
    'executor': [100, 30, 30, 70, '#EEF'],
    'time': [80, 20, 98, 2, '#0000'],
    'index': [0, 1, 0, 100, '#0000'],
    'reset_button': [47, 2, 0, 2, '#0000'],
    'save_button': [47, 2, 4, 2, '#0000'],
    'local_button': [47, 2, 8, 2, '#0000'],
    'stop_button': [47, 2, 12, 2, '#0000'],
    'line_numbers': [49, 1, 0, 100, '#EEE'], # Outside the screen by defaut
    }}


class Q1(Question):
    """42"""
    def question(self):
        return "42 est la réponse, quelle est la question ?"
    def tester(self):
        self.check(self.worker.source, [
            ['univers', 'Contient «univers»'],
            ['vie', 'Contient «vie»']
        ])
        if self.all_tests_are_fine:
            self.next_question()

    def default_answer(self):
        return ""

class Q2(Question):
    def question(self):
        return "C'est fini"
    def tester(self):
        return
    def default_answer(self):
        return "Bravo !"