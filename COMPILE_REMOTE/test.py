# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        self.set_options({
            'automatic_compilation': False,
            'compile_options': ['-Wall', '-pedantic'],
            'allowed': ['brk'],
            })
        return "Plus de questions"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """
using namespace std;

#include <iostream>
#include <math.h>

#define SQUARE(X) ((X)*(X))

int distance(int *x1, int *y1, int *x2, int *y2) {
    return sqrt(SQUARE(*x1 - *x2) + SQUARE(*y1 - *y2));
}

const int LARGEUR = 40;
const int HAUTEUR = 20;

int main() {
    int x1=LARGEUR/2, y1=HAUTEUR/2, x, y, rayon;
    char symbol[999];

    // fopen("/etc/passwd", "r"); // Is forbiden by sand box

    cout << "Saisir le rayon entier (8 par exemple) :\\n";
    cin >> rayon;
    cout << "Saisir un symbole :\\n";
    cin >> symbol;

    for(y=0; y < HAUTEUR; y++) {
        for(x=0; x < LARGEUR; x++)
            cout << (distance(&x1, &y1, &x, &y) < rayon ? symbol : "·");
        cout << '\\n';
    }
    return 0;
}
"""

# Session([QEnd()]) # pylint: disable=undefined-variable
