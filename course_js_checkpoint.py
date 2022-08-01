# pylint: disable=no-self-use,missing-function-docstring
"""
Message for session done
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """Donnez votre nom à l'enseignant pour qu'il vous ouvre l'examen"""
    def default_answer(self):
        return """print("Donnez votre nom à l'enseignant pour qu'il vous ouvre l'examen")"""

Compile_JS([Q0()]) # pylint: disable=undefined-variable
