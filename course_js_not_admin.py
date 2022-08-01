# pylint: disable=no-self-use,missing-function-docstring
"""
Message for session done
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """Vous n'êtes pas administrateur C5"""
    def default_answer(self):
        return """print("Vous n'êtes pas administrateur C5")"""

Compile_JS([Q0()]) # pylint: disable=undefined-variable
