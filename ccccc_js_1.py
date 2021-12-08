#!/usr/bin/python3

"""
Some questions
"""

def question1(_worker):
    """Affiche le contenu de la zone question"""
    return """Pour afficher quelque chose, on tape :
<pre>
print(la_chose_a_afficher) ;
</pre>

<p>
Saisissez dans le zone blanche le programme qui affiche 42
dans le bloc en bas à droite.
"""

def tester1(worker, _args):
    """Affiche le contenu de la zone buts"""
    worker.display('<p>Dans votre code source on devrait trouver :</p>')
    worker.check(worker.source, [
        ['print', 'Le nom de la fonction «print» pour afficher la valeur'],
        ['print *[(]', 'Une parenthèse ouvrante après le nom de la fonction'],
        ['[(].*42', 'Le nombre que vous devez afficher'],
        ['\n[a-z]* *\\(.*[)]', 'Une parenthèse fermante après le dernier paramètre de la fonction'],
        ['; *($|\n)', "Un point virgule pour indiquer la fin de l'instruction"],
        ])
    worker.display("<p>Ce que vous devez afficher pour passer à l'exercice suivant :</p>")
    results = worker.check(worker.execution_result, [['42', 'Le texte 42']])
    if results[-1] == 'test_ok':
        worker.current_question += 1

def question2(_worker):
    """Affiche le contenu de la zone question"""
    return """La réponse est *"""
def tester2(worker, _args):
    """Affiche le contenu de la zone buts"""
    worker.display('====')
    if '*' in worker.source:
        worker.current_question += 1

def question3(_worker):
    """Affiche le contenu de la zone question"""
    return """blabla 2
    """
def tester3(worker, _args):
    """Affiche le contenu de la zone buts"""
    worker.display('bingo 2')

CCCCC_JS([question1, question2, question3], [tester1, tester2, tester3]) # pylint: disable=undefined-variable
