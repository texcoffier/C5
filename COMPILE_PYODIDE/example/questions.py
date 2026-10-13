# pylint: disable=no-self-use,missing-function-docstring,invalid-name
"""
For regression tests
"""

# Do not copy this for an examination session.
# It is for an always open session.
COURSE_OPTIONS = {
    'title': "Démonstration de l'exécution Python interne au navigateur web",
    'expected_students_required': 1,
    'display_indent': 0,
    'positions': {
        "question":[1,29,0,60,"#EFE"],
        "tester":[1,29,60,40,"#EFE"],
        "editor":[30,40,0,100,"#FFF"],
        "compiler":[100,30,0,30,"#EEF"],
        "executor":[70,30,0,100,"#EEF"],
        "time":[80,20,98,2,"#0000"],
        "index":[0,1,0,100,"#0000"]
    }
}

def TRUE(_):
    return True
class First(Question):
    """La fonction 'print'"""
    def question(self):
        return "Faites afficher «2» au lieu de «1»."
    def default_answer(self):
        return "print(1)"
    def expectations(self):
        def test2(txt):
            return txt == '2\n'
        return [
            ['MSG', "La case indiquera si c'est bon."],
            ['OUT', 'Le chiffre 2 est affiché', test2],
        ]

class Second(Question):
    """Faire une multiplication"""
    def question(self):
        return "Faites afficher le produit de «a» et «b»."
    def default_answer(self):
        return "a = 6\nb = 7\n"
    def expectations(self):
        def test(txt):
            return txt == '42\n'
        def triche(_):
            return '42' not in self.worker.source
        return [
            ['MSG', "La case indiquera si c'est bon."],
            ['OUT', 'Le produit est affiché', test],
            ['OUT', "Vous n'avez pas triché", triche],
        ]

class Third(Question):
    """Corriger une typo"""
    def question(self):
        return "Corrigez le bug dans le programme."
    def default_answer(self):
        return """
nr_espaces = 0
for caractere in "Une phrase"
    if caractere == ' ':
        nr_espaces += 1
print("Il y a", nr_espaces, "espaces.")
"""
    def expectations(self):
        def test(txt):
            return txt == 'Il y a 1 espaces.\n'
        def triche(_):
            return '1 e' not in self.worker.source
        return [
            # ['EXIT', "Première exécution terminée.", TRUE],
            ['MSG', "La case indiquera si c'est bon."],
            ['OUT', 'Le résultat est affiché', test],
            ['OUT', "Vous n'avez pas triché", triche],
        ]

class Fourth(Question):
    """Afficher avec matplotlib"""
    def question(self):
        return "Affichages avec matplotlib."
    def default_answer(self):
        return """import matplotlib.pyplot
import numpy
import c5

def create_sin():
    x = numpy.arange(0.0, 2.0, 0.01)
    y = 1 + numpy.sin(2 * numpy.pi * x)
    fig, repere = matplotlib.pyplot.subplots()
    repere.plot(x, y)
    repere.set(xlabel='X axis', ylabel='Y axis', title='Sinus')
    repere.grid()
    return fig

def create_cercle():
    t = numpy.arange(0.0, 2.0, 0.01)
    x = 1 + numpy.cos(2 * numpy.pi * t)
    y = 1 + numpy.sin(2 * numpy.pi * t)
    fig, repere = matplotlib.pyplot.subplots()
    repere.plot(x, y)
    repere.set(xlabel='X', ylabel='Y', title='Cercle')
    repere.grid()
    return fig

print("Sinus")
c5.display_plot(create_sin())

print("Cercle")
c5.display_plot(create_cercle())
"""
    def expectations(self):
        return [
            ['EXIT', "Exécution terminée.", TRUE],
        ]

class Fifth(Question):
    """Variable global"""
    def question(self):
        return "Mettre la chaîne de caractère 5 dans la variable «a»"
    def default_answer(self):
        return ""

    def expectations(self):
        def a_exists():
            return 'a' in self.worker.pyodide_globals
        def a_contains_5():
            return str(self.worker.pyodide_globals['a'] or '') == '5'
        def a_contains_a_string():
            if self.worker.pyodide_globals['a']:
                return self.worker.pyodide_globals['a'].lower
        return [
            ['CHECK', "La variable global 'a' existe", a_exists],
            ['CHECK', "La variable 'a' contient 5", a_contains_5],
            ['CHECK', "La variable 'a' contient une chaîne de caractères", a_contains_a_string],
            ['EXIT', "Exécution terminée.", TRUE],
        ]

class Sixth(Question):
    """Lecture fichier"""
    def question(self):
        return """Faites les 2 choses suivantes :
        <ul>
        <li> Afficher le contenu to fichier «toto».
        <li> Enregistrer le texte «Au revoir» dans le fichier «titi».
        </ul>"""
    def default_answer(self):
        self.set_options({
            'filetree_in': [['toto', 'Bonjour!']], # Files to send
            'filetree_out': ['titi']               # Files to retrieve
            })
        return """with open('', 'r') as f:
    print(f.read())
  
with open('', 'w') as f:
    f.write('Au revoir')
"""
    def expectations(self):
        def ok1(txt):
            return self.worker.options['filetree_in'][0][1] in txt
        def ok2():
            for filename, _content in self.worker.files:
                if filename == self.worker.options['filetree_out'][0]:
                    return True
        def ok3():
            for filename, content in self.worker.files:
                if filename == self.worker.options['filetree_out'][0] and 'Au revoir' in content:
                    return True
        return [
            ['OUT', 'Le contenu du fichier est bien affiché', ok1],
            ['CHECK', 'Vous avez bien créé le fichier', ok2],
            ['CHECK', 'Il contient le bon texte', ok3],
            ['EXIT', "Exécution terminée.", TRUE],
        ]

class Seventh(Question):
    """Pandas"""
    def question(self):
        return """Afficher le contenu du fichier «toto.csv» ainsi
            que les statistiques le concernant."""
    def default_answer(self):
        self.set_options({
            'filetree_in': [['toto.csv', '''X,Y
1,2
2,3
3,2
''']],
            })
        return """import pandas

# Le fichier lu a été créé par le questionnaire,
# il ne vient pas d'un média.
data = pandas.read_csv('')

print(data)
print(data.describe())
"""
    def expectations(self):
        def ok1():
            return '''   X  Y
0  1  2
1  2  3
2  3  2
         X         Y
count  3.0  3.000000
mean   2.0  2.333333
std    1.0  0.577350
min    1.0  2.000000
25%    1.5  2.000000
50%    2.0  2.000000
75%    2.5  2.500000
max    3.0  3.000000''' in self.worker.execution_result
        return [
            ['CHECK', 'Le contenu du fichier est bien affiché', ok1],
            ['EXIT', "Exécution terminée.", TRUE],
        ]

class Eighth(Question):
    """Reading media"""
    def question(self):
        return """Faites afficher le contenu d'un fichier qui n'existe pas."""
    def default_answer(self):
        return '''
import c5

print("Binary file from another C5 session:")
c5.display_png(await c5.read(
    'chien.png', course='REMOTE=grapic', bytes=True))

print("CSV media from this C5 session:")
print(await c5.read("example.csv"))
'''

    def expectations(self):
        def ok():
            return 'Arrêtez de hacker' in self.worker.execution_result
        return [
            ['CHECK', 'Le contenu du fichier est bien affiché', ok],
            ['EXIT', "Exécution terminée.", TRUE],
        ]

class Last(Question):
    """Testez vos programmes"""
    def question(self):
        return "C'est fini"
    def default_answer(self):
        return "# Taper votre code Python au dessous :\n\n\n\n\n"
