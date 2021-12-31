# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return "Plus de questions"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """
def distance_au_carre(x1, y1, x2, y2):
    x1 -= x2
    y1 -= y2
    return x1*x1 + y1*y1

texte = ''
for y in range(20):
    for x in range(30):
        if distance_au_carre(x, y, 10, 10) < 90:
            texte += '*'
        else:
            texte += ' '
    texte += '\\n'
print(texte)
"""

Compile_Python([QEnd()]) # pylint: disable=undefined-variable
