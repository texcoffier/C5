# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of Racket remote
"""

COURSE_OPTIONS = {
            'automatic_compilation': False,
            'compiler': 'racket',
            'language': 'lisp',
            'allow_copy_paste': True,
            'positions' : {
                'question': [1, 28, 0, 30, '#EFE'],
                'tester': [1, 28, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [100, 30, 0, 30, '#EEF'],
                'executor': [70, 30, 0, 100, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                'reset_button': [68, 2, 0, 2, '#0000'],
                'save_button': [66, 2, 0, 2, '#0000'],
                'local_button': [64, 2, 0, 2, '#0000'],
                'stop_button': [61, 2, 0, 2, '#0000'],
                'line_numbers': [29, 1, 0, 100, '#EEE'],
                }
            }

class Q1(Question):
    def question(self):
        return self.__doc__
    def tester(self):
        self.display("N'hésitez pas à modifier ce programme")
    def default_answer(self):
        return r"""
"Addition"
(+ 6 7)
"Création de la fonction retournant le carré"
(define (sqr x) (* x x))
(sqr 5)
"Création paire pointée"
(cons 1 2)
"Appel fonction invalide"
(cons 1 2 3)
"Récursion infinie"
(define (bad) (bad))
(bad)
"""