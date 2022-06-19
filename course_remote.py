# pylint: disable=no-self-use,missing-function-docstring
"""
Demonstration of the system
"""

class QEnd(Question): # pylint: disable=undefined-variable
    """Question Finale"""
    def question(self):
        return "Plus de questions"
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
    int x1=15, y1=15, x, y, rayon;

    cout << "Saisir le rayon :";
    cin >> rayon;

    for(y=0; y < 30; y++) {
        for(x=0; x < 30; x++)
            cout << (distance(&x1, &y1, &x, &y) < rayon ? '*' : ' ');
        cout << '\\n';
    }
    return 0;
}
"""

Compile_remote([QEnd()]) # pylint: disable=undefined-variable
