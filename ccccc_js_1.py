# pylint: disable=no-self-use
"""
Some questions
"""

class Q1(Question):
    """Question 1"""
    def question(self):
        """Affiche le contenu de la zone question"""
        return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche 42
dans le bloc en bas à droite.
"""
    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('<p>Dans votre code source on devrait trouver :</p>')
        self.check(self.worker.source, [
            ['print', 'Le nom de la fonction «print» pour afficher la valeur'],
            ['print *[(]', 'Une parenthèse ouvrante après le nom de la fonction'],
            ['[(].*42', 'Le nombre que vous devez afficher'],
            ['\n[a-z]* *\\(.*[)]',
             'Une parenthèse fermante après le dernier paramètre de la fonction'],
            ['; *($|\n)', "Un point virgule pour indiquer la fin de l'instruction"],
            ])
        self.display("<p>Ce que vous devez afficher pour passer à l'exercice suivant :</p>")
        results = self.check(self.worker.execution_result, [['42', 'Le texte 42']])
        if results[-1] == 'test_ok':
            self.next_question()

class Q2(Question):
    """Question 2"""
    def question(self):
        """Affiche le contenu de la zone question"""
        return """La réponse est *"""

    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('====')
        if '*' in self.worker.source:
            self.next_question()

class Q3(Question):
    """Question 3"""
    def question(self):
        """Affiche le contenu de la zone question"""
        return """blabla 2
        """
    def tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('bingo 2')

    def default_answer(self):
        """La valeur indiquée au départ dans le champ de saisie"""
        return "// Vous connaissez l'histoire\n\n"

CCCCC_JS([Q1(), Q2(), Q3()]) # pylint: disable=undefined-variable
