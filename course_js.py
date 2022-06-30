# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """Ce bloc contient l'objectif que vous devez atteindre
        pour passer à la question suivante.
        <p>
        Votre progression est affichée dans la barre de gauche.
        <p>
        Modifiez le programme dans le bloc blanc à droite pour qu'il affiche
        dans le bloc bleu «Exécution» en bas à droite :
        <pre>Je suis un texte super long</pre>"""
    def tester(self):
        if "Je suis un texte super long" in self.worker.execution_result:
            self.display("Vous affichez le bon message !")
            self.next_question()
            return
        self.display(
            """Cette zone vous donne des indices pour répondre.
            <p>
            Pour le moment la zone en bas à droite contient :<pre>"""
            + self.worker.escape(self.worker.execution_result) + """</pre>
            au lieu de : <pre>Je suis un texte super long</pre>
            Vous devez remplacer 'court' par 'long' dans la zone blanche
            à droite.
            """)
    def default_answer(self):
        return """
// Lisez la consigne indiquée à gauche.

// Le programme que vous devez modifier :

print("Je suis un texte super court");

"""

class Q1(Question): # pylint: disable=undefined-variable
    """Question 1"""
    answer = None
    def question(self):
        self.answer = str(self.worker.millisecs() % 100)
        return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche """ + self.answer + """
dans le bloc en bas à droite.
"""
    def tester(self):
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
        self.check(self.worker.execution_result,
                   [[self.answer, 'Le texte ' + self.answer]])
        if self.worker.execution_result == self.answer + '\n':
            self.next_question()

class Q2(Question): # pylint: disable=undefined-variable
    """Question 2"""
    def question(self):
        return """
        Modifiez la fonction «carre»
        pour quelle retourne le carré du nombre passé en paramètre"""

    def append_to_source_code(self):
        return "return carre"

    def tester(self):
        self.message(self.worker.execution_returns,
                     "La fonction 'carre' est correctement définie")
        self.message('*' in self.worker.source,
                     "Le programme contient un '*' pour calculer le carré.")
        all_fine = True
        i = -2
        while i != 2.5:
            fine = self.worker.execution_returns and self.worker.execution_returns(i) == i*i
            all_fine = all_fine and fine
            self.message(fine, 'carre(' + i + ') → ' + i*i)
            i += 0.5
        if all_fine:
            self.next_question()

    def default_answer(self):
        return """function carre(x)
{
    return x ;
}

print(carre(3))
"""
class Q3(Question): # pylint: disable=undefined-variable
    """Question 3"""
    good = '''0 0
1 1
2 4
3 9
4 16
5 25
6 36
7 49
8 64
9 81
10 100
'''
    def question(self):
        return ("Faites afficher les carrés de 0 à 10 en faisant une boucle :<pre>"
                + self.good + "</pre>")

    def tester(self):
        self.check(self.worker.source, [
            ['function carre\\(', "une fonction 'carre'"],
            ['for *\\(.*;.*;.*\\)', "une boucle 'for(...;...,...)'"],
            ["print\\(", "un 'print' pour afficher le résultat"],
        ])
        good = True
        for digit in "23456789":
            if digit in self.worker.source:
                good = False
        self.message(good, "ne doit pas contenir les chiffres 2 à 9")

        fine = self.worker.execution_result == self.good
        self.message(fine, "affiche le bon résultat.")
        self.display("<p>Votre programme fait : "
                     + str(len(self.worker.source.strip().split('\n'))) + ' lignes.')

        if fine and good:
            self.next_question()

    def default_answer(self):
        return self.worker.source


class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return "Plus de questions"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return ""

Compile_JS([Q0(), Q1(), Q2(), Q3(), QEnd()]) # pylint: disable=undefined-variable
