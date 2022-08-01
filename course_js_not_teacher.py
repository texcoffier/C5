# pylint: disable=no-self-use,missing-function-docstring
"""
Message for session done
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """Vous ne surveillez pas cet examen"""
    def default_answer(self):
        return """print("Vous ne surveillez pas cet examen")"""

Compile_JS([Q0()]) # pylint: disable=undefined-variable
