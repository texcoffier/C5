"""Play with files"""

COURSE_OPTIONS = {
    'automatic_compilation': 0,
}

class Q1(Question): # pylint: disable=undefined-variable
    """Play with files"""
    def question(self):
        self.set_options({
            'filetree_in': [['a', 'Content of «a»'], ['A/a', 'Content of «A/a»']],
            'filetree_out': ['a', 'A/a', 'c']
            })
        return """File management.
        <ul>
        <li>Display «a» content.
        <li>Display «A/a» content.
        <li>Append «+» to «a» file.
        <li>Create a file named «c».
        </ul>
        """
    def tester(self):
        self.display('<p>The execution:</p>')
        self.check(
            self.worker.execution_result,
            [['Content of «a»', 'Displays «a» content.'],
             ['Content of «A/a»', 'Displays «A/a» content.'],
            ])
        a_ok = False
        c_ok = False
        for filename, content in self.worker.files:
            if filename == 'a' and '+' in content:
                a_ok = True
            if filename == 'c':
                c_ok = True
        self.message(a_ok, "«+» has been added to «a» file.")
        self.message(c_ok, "«c» file has been created.")
        return
    def default_answer(self):
        return """#include <stdio.h>

int main(void) {
    char buffer[999];
    FILE *f;
    
    f = fopen("a", "r");
    fgets(buffer, sizeof(buffer), f);
    printf("a=«%s»\\n", buffer);
    fclose(f);

    f = fopen("A/a", "r");
    fgets(buffer, sizeof(buffer), f);
    printf("A/a=«%s»\\n", buffer);
    fclose(f);
    
    f = fopen("a", "a");
    fprintf(f, "+\\n");
    fclose(f);
    printf("Append done\\n");

    fclose(fopen("c", "w"));
    printf("Create done\\n");
  
    return 0;
}
"""