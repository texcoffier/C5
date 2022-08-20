# pylint: disable=no-self-use,missing-function-docstring
"""
Ne rien changer après le début de l'examen car cela casse tout.
(Á part des typos dans les textes).
"""

# Le nombre DU indique la qualité des messages du compilateur
# D =
#   0: bon numéro de ligne
#   1: bon numéro de ligne, mais difficile à trouver dans la ligne
#   2: mauvais numéro de ligne
# U =
#   0: message limpide
#   9: message incompréhensible

ERRORS = [
    """5 Bon endroit mais message faux
using namespace std
#include <iostream>
int main()
{
    cout << "Bonjour\\n";
}
""",
    """0
using namespace std;
#include <iostream>
int main()
{
    cout << "Bonjour\\n"
}
""",
    """5 Méthode non trouvable
using namespace std;
#include <iostream>

int main()
{
    cout >> "Bonjour\\n";
}
""",
    """3 warning: character constant too long for its type
using namespace std;
#include <iostream>

int main()
{
    cout << 'Bonjour\\n';
}
""",
    """5 Méthode non trouvable
using namespace std;
#include <iostream>

int main()
{
    cin << "Bonjour\\n";
}
""",
    """9 Message qui n'aide pas
using namespace std;
#include <iostream>

int main()
(
    cout << "Bonjour\\n";
)
""",
    """10
using namespace std;
#include <iostream>

int main() { cout << "Bonjour\\n" }
""",
    """13
using namespace std;
#include <iostream>

int main() { cout << 'Bonjour\\n'; }
""",
    """17
using namespace std;
#include <iostream>

int maine() { cout << "Bonjour\\n"; }
""",
    """7
using namespace std;
#include <iostream>

int maine()
{
    cout << "Bonjour\\n";
}
""",
    """3
using namespace std;
#include <iostream>;

int main() { cout << "Bonjour\\n"; }
""",
    """3
using namespace std;
#include <iostream>

int main() ( cout << "Bonjour\\n"; )
""",
    """9
using name space std;
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
""",
    """7
use namespace std;
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
""",
    """7
using namespace <std>;
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
""",
    """0a
using namespace std;
#include iostream

int main()
{
    cout << "Bonjour\\n";
}
""",
    """2
using namespace "std";
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
""",
    """0
using namespace std;
#include 'iostream'

int main()
{
    cout << "Bonjour\\n";
}
""",
    """4
using namespace std;
#include <iostream>

int main
{
    cout << "Bonjour\\n";
}
""",
    """0
using namespace std;
#include <iostream>

Int main()
{
    cout << "Bonjour\\n";
}
""",
    """25
using namespace std;
#include <iostream>

int main();
{
    cout << "Bonjour\\n";
}
""",
    """0
using namespace std:
#include <iostream>

int main()
{
    cout << "Bonjour\\n";
}
""",
    """0
using namespace std;
#include <iostream>

int main()
{
    cout << "Bonjour\\n":
}
""",
    """100
using namespace std
;
#include <iostream>
int
main
(
)
{
cout
<
<
"Bonjour\\n"
;
}
""",
    """100
using namespace std;
#include<iostream>
int main(){cout<<'Bonjour\\n';}
""",
    """100
using namespace std;
#include<iostream>
int main(){cout«"Bonjour\\n";}
""",
    """100
using namespace std;
#include <iostream>

int main()
{
    cout << "Bonjour\\n" ;
}
""",
]

def create(source):
    """Create a fix error question"""
    class FixErr(Question): # pylint: disable=undefined-variable
        """Fix error class"""
        def question(self):
            return "Corrigez l'erreur dans le programme."
        def tester(self):
            if self.worker.execution_result.split('\n')[0] == 'Bonjour':
                if self.worker.nr_errors == 0 and self.worker.nr_warnings == 0:
                    self.next_question()
        def default_answer(self):
            return source
    return FixErr()

class End(Question): # pylint: disable=undefined-variable
    """Bravo!"""
    def question(self):
        return "Bravo, vous êtes arrivé au bout !"
    def default_answer(self):
        return '// Bravo, vous êtes arrivé au bout !'
    def tester(self):
        self.display("Passer à la suite du cours !")

def init():
    """Calcule la liste des questions"""
    sources = []
    for i, source in enumerate(ERRORS):
        lines = source.split('\n')
        sources.append([1000 + int(lines[0].split(' ')[0]) + i/1000, '\n'.join(lines[1:])])

    sources.sort()
    questions = []
    for i, source in enumerate(sources):
        questions.append(create(source[1]))
        questions[-1].__doc__ = "Erreur N°" + str(i+1)
    questions.append(End())
    return questions

Session(init()) # pylint: disable=undefined-variable
