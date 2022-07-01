# pylint: disable=no-self-use,missing-function-docstring
"""
Message for session done
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """La session d'exercice ou d'examen n'a pas commencé"""
    def default_answer(self):
        return """print("La session d'exercice ou d'examen n'a pas commencé")"""

Compile_JS([Q0()]) # pylint: disable=undefined-variable
