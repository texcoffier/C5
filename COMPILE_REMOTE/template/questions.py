class Q1(Question):
    def question(self):
        if self.version() == 'a':
            return LOAD_QUESTION("1-A-question.html")
        return LOAD_QUESTION("1-B-question.html")

    def default_answer(self):
        if self.version() == 'a':
            return LOAD_DEFAULT("1-A-default.txt")
        return LOAD_DEFAULT("1-B-default.txt")

    def grading_ladder(self):
        if self.version() == 'a':
            return LOAD_GRADING("1-A-grading.gl")
        return LOAD_GRADING("1-B-grading.gl")

    def expected_answer(self):
        if self.version() == 'a':
            return LOAD_ANSWER("1-A-answer.txt")
        return LOAD_ANSWER("1-B-answer.txt")

class Q2(Question):
    def question(self):
        if self.version() == 'a':
            return LOAD_QUESTION("2-A-question.html")
        return LOAD_QUESTION("2-B-question.html")

    def default_answer(self):
        if self.version() == 'a':
            return LOAD_DEFAULT("2-A-default.txt")
        return LOAD_DEFAULT("2-B-default.txt")

    def grading_ladder(self):
        if self.version() == 'a':
            return LOAD_GRADING("2-A-grading.gl")
        return LOAD_GRADING("2-B-grading.gl")

    def expected_answer(self):
        if self.version() == 'a':
            return LOAD_ANSWER("2-A-answer.txt")
        return LOAD_ANSWER("2-B-answer.txt")

class Q3(Question):
    def question(self):
        if self.version() == 'a':
            return LOAD_QUESTION("3-A-question.html")
        return LOAD_QUESTION("3-B-question.html")

    def default_answer(self):
        if self.version() == 'a':
            return LOAD_DEFAULT("3-A-default.txt")
        return LOAD_DEFAULT("3-B-default.txt")

    def grading_ladder(self):
        if self.version() == 'a':
            return LOAD_GRADING("3-A-grading.gl")
        return LOAD_GRADING("3-B-grading.gl")

    def expected_answer(self):
        if self.version() == 'a':
            return LOAD_ANSWER("3-A-answer.txt")
        return LOAD_ANSWER("3-B-answer.txt")

class Q4(Question):
    def question(self):
        if self.version() == 'a':
            return LOAD_QUESTION("4-A-question.html")
        return LOAD_QUESTION("4-B-question.html")

    def default_answer(self):
        if self.version() == 'a':
            return LOAD_DEFAULT("4-A-default.txt")
        return LOAD_DEFAULT("4-B-default.txt")

    def grading_ladder(self):
        if self.version() == 'a':
            return LOAD_GRADING("4-A-grading.gl")
        return LOAD_GRADING("4-B-grading.gl")

    def expected_answer(self):
        if self.version() == 'a':
            return LOAD_ANSWER("4-A-answer.txt")
        return LOAD_ANSWER("4-B-answer.txt")
