# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

COURSE_OPTIONS = {
    'positions': {
        'question': [1, 29, 0, 30, '#EFE'],
        'tester': [1, 29, 30, 70, '#EFE'],
        'editor': [30, 40, 0, 80, '#FFF'],
        'compiler': [30, 70, 80, 20, '#EEF'],
        'executor': [70, 30, 0, 80, '#EEF'],
        'time': [80, 20, 98, 2, '#0000'],
        'index': [0, 1, 0, 100, '#0000'],
        'save_button': [66, 2, 0, 2, '#0000'],
        'reset_button': [68, 2, 0, 2, '#0000'],
        'local_button': [100, 2, 0, 2, '#0000'],
        'line_numbers': [100, 1, 0, 100, '#EEE'], # Outside the screen by defaut
        }
    }

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        batiment, coord_x, coord_y = self.placement()
        version = self.version()
        return ("<p>Récupération des informations concernant la place de l'étudiant dans la salle."
                + "<br>Surveillant :" + self.teacher()
                + "<br>Bâtiment : " + batiment
                + "<br>Poste X : " + coord_x
                + "<br>Poste Y : " + coord_y
                + "<br>Version sujet : " + version
                )
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """/*
No 'struct', 'class' nor 'reference'
*/

using namespace std;

#include <iostream>
#include <math.h>

#define SQUARE(X) ((X)*(X))

int distance(int *x1, int *y1, int *x2, int *y2) {
    return sqrt(SQUARE(*x1 - *x2) + SQUARE(*y1 - *y2));
}

int main() {
    int x1=15, y1=15, x, y;
    const int rayon = 10 ;

    for(y=0; y < 30; y++) {
        for(x=0; x < 30; x++)
            cout << (distance(&x1, &y1, &x, &y) < rayon ? '*' : ' ');
        cout << '\\n';
    }
    return 0;
}
"""

# Session([QEnd()]) # pylint: disable=undefined-variable
