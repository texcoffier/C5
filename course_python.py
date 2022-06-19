# pylint: disable=no-self-use,missing-function-docstring,invalid-name
"""
Demonstration of the system
"""

Question = Question # # pylint: disable=undefined-variable,self-assigning-variable

def canonise(txt):
    return txt.lower().replace(' ', '')

class Q_print(Question):
    """La fonction 'print'"""
    answer = ''
    def question(self):
        self.answer = ["Salut !", "Au revoir", "Bonne nuit"][self.worker.millisecs() % 3]
        return ("Modifiez le contenu de la grande zone blanche juste à droite pour afficher en bas à droite :<pre>"
                + self.answer + "</pre>"
                + "Une fois ce challenge réussi vous passez à la question suivante.")
    def tester(self):
        self.display("La zone en bas à droite contient :<pre>"
                     + self.worker.escape(self.worker.execution_result) + "</pre>")
        if self.answer in self.worker.execution_result:
            self.display('Et elle contient bien le texte demandé !')
            self.next_question()
            return
        self.display('<p>Elle ne contient pas «' + self.answer + "»")
        if canonise(self.answer) in canonise(self.worker.execution_result):
            self.display('<p style="background:#F88">Auriez-vous oublié un espace ou une majuscule ?')
    def default_answer(self):
        return """
# Lisez la consigne indiquée à gauche

print(42)        # Affiche un nombre entier

print(1.5)       # Affiche un nombre flottant

print("Bonjour") # Affiche une chaîne de caractères

# Ce que «print» affiche est dans le bloc en bas à droite

"""

class Q_variable(Question):
    """Les variables"""
    year = 0
    answer = ''
    def question(self):
        return '''
        Faites afficher le produit du contenu de la "variable" «annee»
        et de la "variable" «pi»
        '''
    def tester(self):
        self.display("Votre programme à droite contient bien :")
        self.check(
            self.worker.source,
            [['print', '«print» pour afficher le resultat.'],
             ['[*]', '«*» pour faire la multiplication des deux valeurs.'],
             [r'annee *[*] *pi|pi *[*] *annee', 'Le produit de «annee» et de «pi».'],
            ])
        self.message(self.answer in self.worker.execution_result,
                     'Le bon résultat est affiché.')
        self.message(self.answer not in self.worker.source,
                     "Vous n'avez pas triché")
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        self.year = 2000 + self.worker.millisecs() % 20
        self.answer = str(self.year * 3.14)
        return """
# Comment créer des "variables"

annee = """ + self.year + "      # Nomme «année» la valeur «" + self.year + """»

pi = 3.14          # Nomme «pi» la valeur «3.14»

bonjour = "Hello"  # Nomme «pi» la valeur «Hello»

print("Année=", annee, "π=", pi, "bonjour=", bonjour)

"""

class Q_booleen(Question):
    """Les expressions booléennes"""
    min = max = None
    def question(self):
        return """Modifiez la valeur de «x» pour que
        les trois derniers tests affichent <tt>False</tt>"""
    def tester(self):
        self.message('x' in self.worker.locals(), "La variable «x» existe bien")
        if self.all_tests_are_fine:
            x = self.worker.locals()['x']
        else:
            x = -1
        self.message(x > self.max, "Elle a une valeur correcte")
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        self.min = 10 + self.worker.millisecs() % 80
        self.max = self.min + 10
        return """
minimum = """ + str(self.min) + """
maximum = """ + str(self.min + 10) + """
print("minimum =", minimum)
print("maximum =", maximum)
print("minimum > maximum →", minimum > maximum)
print("minimum < maximum →", minimum < maximum)
print("minimum == maximum →", minimum == maximum)
print("minimum != maximum →", minimum != maximum)
print("not False →", not False)
print("not True →", not True)

x = """ + str(self.min + 5) + """ # milieu de l'intervalle
print()
print("Avec x =", x)
print("x >= minimum →", x >= minimum)
print("\\nEt les 3 derniers :\\n")
print("x <= maximum →", x <= maximum)
print("x >= minimum and x <= maximum →",
       x >= minimum and x <= maximum)
print("not ( x < minimum or x > maximum) →",
       not ( x < minimum or x > maximum) )

"""

class Q_str_add(Question):
    """Addition de chaines de caractères"""
    def question(self):
        return """On peut utiliser l'opérateur «+» pour ajouter deux
        chaines de caractères.
        <p>
        On ne peut pas ajouter une chaîne de caractères et un entier.
        C'est pour cela que le bloc «Exécution» est en rouge.
        <p>
        Corrigez le programme pour qu'il affiche 11."""
    def tester(self):
        self.check(
            self.worker.source,
            [['"1".*"1"', 'Vous utilisez deux chaines de caractères "1"'],
             ['"1" *[+] *"1"', 'Vous additionner deux chaines de caractères "1"'],
            ])
        self.message('11' not in self.worker.source,
                     "Vous n'utilisez pas 11 directement")
        self.message('11' in self.worker.execution_result,
                     "Cela affiche 11")
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """
a = "Hello"
b = "World"
print(a + " " + b)

print("1" + 1)
"""

class Q_import_math(Question):
    """Bibliothèque mathématique"""
    def question(self):
        return """Vous pouvez utiliser des outils créés par d'autres personnes.
        La bibliothèque mathématique est toujours là pour vous aider :
        <pre>import math</pre>
        <p>
        <ul>
        <li> Mettre la racine carré de 0.5 dans la «sqrt»
        <li> Mettre le cosinus de π/4 dans «cos»
        <li> Faites afficher la différence entre les 2
        </ul>
        """
    def tester(self):
        self.check(
            self.worker.source,
            [['\nsqrt *=', 'Enregistrer quelque chose dans «sqrt»'],
             ['math\\.sqrt *\\( *0.5 *\\)', 'Calculer la racine carrée de 0.5'],
             ['\ncos *=', 'Enregistrer quelque chose dans «cos»'],
             ['math\\.pi */ *4', 'Calculer π/4'],
             ['math\\.cos *\\( *math\\.pi */ *4 *\\)', 'Calculer cos(π/4)'],
             ['print *\\( *(sqrt *- *cos|cos *- *sqrt) *\\)', 
              'Affichage de la différence entre «sqrt» et «cos»'],
            ])
        self.message('3.1' not in self.worker.source,
                     "Vous n'utilisez pas 3.14 mais bien π")
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """
import math
print("La valeur de π est :", math.pi)
print("La racine carré de 4 est :", math.sqrt(4))
print("Le cosinus de 0 est :", math.cos(0))

# la racine carré de 0.5 dans «sqrt» :



# le cosinus de π/4 dans «cos» :



# Afficher la différence des valeurs de «sqrt» et «cos» :



"""


class Q_exo1(Question):
    """Surface du disque"""
    def question(self):
        return """Ecrire un programme qui affiche la surface
        d'un disque dont vous aurez choisi le rayon.
        Vous devez :
        <ul>
        <li> enregistrer le rayon du disque dans «rayon»
        <li> enregistrer la surface du disque dans «surface»
        </ul>
        <p>
        La surface est π multiplié par le rayon au carré.
        """
    def tester(self):
        self.check(
            self.worker.source,
            [['\nimport +math *\n', 'Vous importez la bibliothèque mathématique'],
             ['\nrayon *= *[0-9.]+ *\n', 'Vous enregistrez un nombre dans «rayon»'],
             ['\nsurface *=', 'Vous enregistrez dans «surface»'],
             ['math\\.pi', 'Vous utilisez π'],
             ['rayon \\* *rayon', 'Vous calculez le rayon au carré'],
            ])
        rayon = surface = None
        if 'rayon' in self.worker.locals():
            rayon = float(self.worker.locals()['rayon'])
        if 'surface' in self.worker.locals():
            surface = float(self.worker.locals()['surface'])
        self.message(abs(surface - 3.1415*rayon*rayon) < 0.01,
                     "La surface calculée est correcte")
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """# Rien pour vous aider
# Vous pouvez retourner sur les questions précédentes en cliquant
# sur la colonne de nombres qui est tout à gauche.


"""


class QEnd(Question):
    """Félicitation vous êtes arrivé au bout !"""
    def question(self):
        return "Plus de questions"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """
print("Dessinons un rectangle !")

print("Largeur :")
largeur = int(input())

print("Hauteur :")
hauteur = int(input())

print("Caractère :")
char = input()

print("Couleur en hexa (comme F00) :")
couleur = input()

for line in range(hauteur):
    print('<span style="color:#' + couleur + '">'
          + char * largeur
          + '</span>')
"""

Compile_Python([Q_print(), Q_variable(), Q_booleen(), Q_str_add(),  # pylint: disable=undefined-variable
                Q_import_math(), Q_exo1(), QEnd()])
