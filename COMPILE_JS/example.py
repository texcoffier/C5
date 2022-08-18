# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class Q0(Question): # pylint: disable=undefined-variable
    """Question 0"""
    def question(self):
        return """La réponse est : «print(1)»"""
    def tester(self):
        self.display(
            "Pour le moment la zone en bas à droite contient :<pre>"
            + self.worker.escape(self.worker.execution_result) + """</pre>""")
        self.check(self.worker.execution_result,
                   [
                       ['^ *1 *\n$', "Contient 1"],
                   ])
        if self.all_tests_are_fine:
            self.next_question()
            return
    def default_answer(self):
        return """print(2);"""

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return "Plus de questions"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return ""

# Session([Q0(), QEnd()]) # pylint: disable=undefined-variable
