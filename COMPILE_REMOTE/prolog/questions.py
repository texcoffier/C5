# pylint: disable=no-self-use,missing-function-docstring
"""
Prolog compiler
"""

COURSE_OPTIONS = {
    'compiler': 'prolog',
    'extension': 'pl',
    'language': 'prolog',
    'title': "Démonstrateur d'exécution Prolog sur le serveur",
    'state': 'Ready',
    'checkpoint': 0,
    'allow_copy_paste': 1,
    'expected_students_required': 0, # Do display to all students
    'automatic_compilation': 0,
    'compile_options': ['-Wall', '-pedantic'],
    'allowed': ['brk'],
    'positions' : {
        "question"    :[  1, 28,  0,  30, "#EFE"],
        "tester"      :[  1, 28, 30,  70, "#EFE"],
        "editor"      :[ 30, 40,  0, 100, "#FFF"],
        "compiler"    :[100, 30,  0,  30, "#EEF"],
        "executor"    :[ 70, 30,  0, 100, "#EEF"],
        "index"       :[  0,  1,  0, 100, "#0000"],
        }
}

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return """Texte de la question.
        <p>Pour enlever cette zone il faut éditer la session.
        """
    def tester(self):
        self.display('''Pas de bug à atteindre.
        <p>Pour enlever cette zone il faut éditer la session.''')
    def default_answer(self):
        return """
likes(a, b).
likes(b, a).

likes(a, c).
likes(c, a).

likes(a, d).
likes(a, e).
likes(d, e).
likes(e, d).

likes(a, "string").
likes("string", a).

friends(X, Y) :- likes(X, Y), likes(Y, X).


%% friends(X, Y)
%% friends(a, X)
%% friends("string", X)

"""

