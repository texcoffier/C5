# pylint: disable=no-self-use
"""
Some questions
"""

class Q1(Question): # pylint: disable=undefined-variable
    """Question 1"""
    answer = None
    def question(self):
        """Affiche le contenu de la zone question"""
        self.answer = '42'
        return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche """ + self.answer + """
dans le bloc en bas à droite.
"""
    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('<p>Dans votre code source on devrait trouver :</p>')
        self.check(self.worker.source, [
            ['print', 'Le nom de la fonction «print» pour afficher la valeur'],
            ['print *[(]', 'Une parenthèse ouvrante après le nom de la fonction'],
            ['[(].*' + self.answer, 'Le nombre que vous devez afficher'],
            ['\n[a-z]* *\\(.*[)]',
             'Une parenthèse fermante après le dernier paramètre de la fonction'],
            ['; *($|\n)', "Un point virgule pour indiquer la fin de l'instruction"],
            ])
        self.display("<p>Ce que vous devez afficher pour passer à l'exercice suivant :</p>")
        results = self.check(self.worker.execution_result,
                             [[self.answer, 'Le texte ' + self.answer]])
        if results[-1] == 'test_ok':
            self.next_question()

class Q2(Question): # pylint: disable=undefined-variable
    """Question 2"""
    def question(self):
        """Affiche le contenu de la zone question"""
        return """La réponse est *"""

    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('====')
        if '*' in self.worker.source:
            self.next_question()

class Q3(Question): # pylint: disable=undefined-variable
    """Question 3"""
    answer = None
    def question(self):
        """Affiche le contenu de la zone question"""
        self.answer = str(self.worker.millisecs() % 100) # pylint: disable=undefined-variable
        return """La réponse à cette question est """ + self.answer
    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        if self.answer in self.worker.source:
            self.next_question()
        else:
            self.display('Je ne trouve pas ' + self.answer + " dans votre réponse")

    def default_answer(self):
        """La valeur indiquée au départ dans le champ de saisie"""
        return "// Vous connaissez l'histoire\n\n"

class Q4(Question): # pylint: disable=undefined-variable
    """Question 3"""
    def question(self):
        """Affiche le contenu de la zone question"""
        return "Plus de questions"
    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('FINI !')

    def default_answer(self):
        """La valeur indiquée au départ dans le champ de saisie"""
        return ""

Compile_JS([Q1(), Q2(), Q3(), Q4()]) # pylint: disable=undefined-variable
