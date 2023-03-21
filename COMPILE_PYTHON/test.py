class First(Question):
    def question(self):
        return "Faites afficher «2» au lieu de «1»."
    def default_answer(self):
        return "print(1)"
    def tester(self):
        if self.worker.execution_result == '2\n':
            self.next_question()
            return
        self.display("«2» n'est pas affiché")

class Second(Question):
    def question(self):
        return "Faites afficher le produit de «a» et «b»."
    def default_answer(self):
        return "a = 6\nb = 7\n"
    def tester(self):
        if '42' in self.worker.source:
            self.display("Vous ne devez pas faire «print(42)»")
            return
        if self.worker.execution_result == '42\n':
            self.next_question()
            return
        self.display("«42» n'est pas affiché")

class Third(Question):
    def question(self):
        return "Corrigez le bug dans le programme."
    def default_answer(self):
        return """
nr_espaces = 0
for caractere in "Une phrase"
    if caractere == ' ':
        nr_espaces += 1
print("Il y a", nr_espaces, "espaces.")
"""    
    def tester(self):
        if self.worker.execution_result == 'Il y a 1 espaces.\n':
            self.next_question()
            return
