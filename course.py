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
    def tester(self, _args):
        if "Je suis un texte super long" in self.worker.execution_result:
            self.display("Vous affichez le bon message !")
            self.next_question()
            return
        self.display("""Cette zone vous donne des indices pour répondre.
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
    def tester(self, _args):
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
        self.answer = str(self.worker.millisecs() % 100) # pylint: disable=undefined-variable
        return """La réponse à cette question est """ + self.answer
    def tester(self, _args):
        if self.answer in self.worker.source:
            self.next_question()
        else:
            self.display('Je ne trouve pas ' + self.answer + " dans votre réponse")

    def default_answer(self):
        return "// Vous connaissez l'histoire\n\n"

class Q4(Question): # pylint: disable=undefined-variable
    """Question 3"""
    def question(self):
        return "Plus de questions"
    def tester(self, _args):
        self.display('FINI !')

    def default_answer(self):
        return ""

Compile_JS([Q0(), Q1(), Q2(), Q3(), Q4()]) # pylint: disable=undefined-variable
