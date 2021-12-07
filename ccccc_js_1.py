#!/usr/bin/python3
# pylint: disable=invalid-name

"""
Some questions
"""

class CCCCC_JS_1(CCCCC_JS):
    """First exercise"""
    def run_question(self):
        """Affiche le contenu de la zone question"""
        return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche 42
dans le bloc en bas à droite.
        """
    def run_tester(self, _args):
        """Affiche le contenu de la zone buts"""
        self.display('<p>Dans votre code source on devrait trouver :</p>')
        self.check(self.source, [
            ['print', 'Le nom de la fonction «print» pour afficher la valeur'],
            ['print *[(]', 'Une parenthèse ouvrante après le nom de la fonction'],
            ['[(].*42', 'Le nombre que vous devez afficher'],
            ['\n[a-z]* *\\(.*[)]',
             'Une parenthèse fermante après le dernier paramètre de la fonction'],
            ['; *($|\n)', "Un point virgule pour indiquer la fin de l'instruction"],
            ])
        self.display("<p>Ce que vous devez afficher pour passer à l'exercice suivant :</p>")
        self.check(self.execution_result, [['42', 'Le texte 42']])

CCCCC_JS_1()
