"""
For regression tests and demo
"""

COURSE_OPTIONS = {'expected_students': 'nobody'} # Hide to students

class Q1(Question): # pylint: disable=undefined-variable
    """Get a single random"""
    def question(self):
        t = []
        if self.question_yet_solved():
            t.append("<p>Reset question: ")
            t.append(self.new_round_button())
        t.append("<p>Your program must display: <tt id=\"test_answer\">")
        t.append(str(self.random()))
        t.append("</tt>")
        return ''.join(t)
    def tester(self):
        r = "'" + str(self.random()) + "'"
        if r in self.worker.execution_result:
            self.next_question()
    def default_answer(self):
        return '''#include <iostream>
            using namespace std;
            int main() {
            cout << "'NUMBER'" << endl;
            } // ''' + str(self.random())

class Q2(Question): # pylint: disable=undefined-variable
    """Check that random_version() does not returns twice the same"""
    def question(self):
        t = []
        if self.question_yet_solved():
            t.append("<p>Reset question: ")
            t.append(self.new_round_button())
        t.append("<p>Your program must display: <tt id=\"test_answer\">")
        t.append(str(self.random_version(2)))
        t.append("</tt>")
        return ''.join(t)
    def tester(self):
        r = "'" + str(self.random_version(2)) + "'"
        if r in self.worker.execution_result:
            self.next_question()
    def default_answer(self):
        return '''#include <iostream>
            using namespace std;
            int main() {
            cout << "'NUMBER'" << endl;
            } // ''' + str(self.random_version(2))
