# pylint: disable=no-self-use,missing-function-docstring
"""
Coq compiler
"""

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

