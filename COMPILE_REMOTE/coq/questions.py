# pylint: disable=no-self-use,missing-function-docstring
"""
Pour tester le compilateur Coq.

A déployer dans COMPILE_REMOTE car la compilation
est faite dans le serveur.
"""

COURSE_OPTIONS = {
    'positions' :
        {
            # Mettre 100 dans X% pour cacher le bloc
            # Bloc           X%  W% Y%  H% Color
            "question"    :[  1, 28, 0, 30,"#EFE"],
            "tester"      :[  1, 28,30, 70,"#EFE"],
            "editor"      :[ 30, 40, 0,100,"#FFF"],
            "compiler"    :[100, 30, 0, 30,"#EEF"], # Caché car pas de compilation
            "executor"    :[ 70, 30, 0,100,"#EEF"],
            "time"        :[ 80, 20,98,  2,"#0000"],
            "index"       :[  0,  1, 0,100,"#0000"],
            "line_numbers":[ 29,  1, 0,100,"#EEE"]
        },
    'compiler': 'coqc',
    'language': 'coq',
    'extension': 'v',
    'allow_copy_paste': 1,
    'display_indent': 0,
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
Definition carre (n:nat) := n * n.
Definition somme_carres (a b:nat) := carre a + carre b.
Check somme_carres.
"""