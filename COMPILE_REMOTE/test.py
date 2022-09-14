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
            'positions' : {
                'question': [1, 28, 0, 30, '#EFE'],
                'tester': [1, 28, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [70, 30, 0, 30, '#EEF'],
                'executor': [70, 30, 30, 70, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                'reset_button': [68, 2, 0, 2, '#0000'],
                'save_button': [66, 2, 0, 2, '#0000'],
                'local_button': [64, 2, 0, 2, '#0000'],
                'stop_button': [61, 2, 0, 2, '#0000'],
                'line_numbers': [29, 1, 0, 100, '#EEE'],
                }
            })
        return """Plus de questions.
        <p>Test de coloriage syntaxique dans la question :
        <pre style="margin:0px;padding:0px"><code class="language-cpp">#define a A
const int a = 5 ;
const char *b = "P" ;</code></pre>
        <img style="display: none" src="data:x" onerror="hljs.highlightAll()">
        """
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
