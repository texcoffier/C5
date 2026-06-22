# Les options suivantes ne sont utilisées qu'à la création de la session.
# Pour les modifier il faut cliquer sur 'Edit' pour éditer les paramètres de session.


COURSE_OPTIONS = {
            'title': 'Test Rust',
            'compiler': 'cargo',
            'state': 'Ready',
            'checkpoint': 0,
            'allow_copy_paste': 1,
            "sequential": 0,
            'positions' : {
                    "question":[1,32,0,50,"#EFE"],
                    "tester":[1,32,51,49,"#EFE"],
                    "editor":[33,37,0,80,"#FFF"],
                    "compiler":[33,67,80,20,"#EEF"],
                    "executor":[70,30,0,80,"#EEF"],
                    "time":[80,20,98,2,"#0000"],
                    "index":[0,1,0,100,"#0000"],
                }
            }

def canonise(txt):
    return txt.lower().replace(' ', '')

# Count the number of 'if' in the "if a != 0.0" block, and return True if the number == 2
def count_if_in_outer_if(source):
    lines = source.split("\n")

    in_block = False
    outer_indent = None
    if_count = 0

    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.trimStart(" "))

        if "if a != 0.0" in stripped:
            in_block = True
            outer_indent = indent
            if_count = 0
            continue

        if in_block:
            # Exit the current block if the indent does not correspond
            if stripped and outer_indent is not None and indent <= outer_indent:
                break

            if stripped.startswith("if "):
                if_count += 1

    return if_count == 2




# useful for check_args
def is_number(x):
    x = x.strip()

    if x == "":
        return False

    # allows numbers, -, .
    allowed = "0123456789.-"

    for c in x:
        if c not in allowed:
            return False
    return True

# took values from racines(...) from 'main' in C5
def check_args(source):
    chunks = source.split("racines(")

    for chunk in chunks:
        part = chunk.split(")")[0]
        values = [x.strip() for x in part.split(",")]

        if len(values) == 3:
            if is_number(values[0]) and is_number(values[1]) and is_number(values[2]):
                return float(values[0]), float(values[1]), float(values[2])

    return None

#calcul racines and put them in an array
def compute_racinesTAB(source):
    vals = check_args(source)
    result = []
    if vals is None:
        return []

    a, b, c = vals

    if a == 0:
        return "pas 2nd degré"

    delta = b * b - 4 * a * c

    if delta > 0:
        sqrt_delta = delta ** 0.5

        x1 = (-b + sqrt_delta) / (2 * a)
        x2 = (-b - sqrt_delta) / (2 * a)
        result.append(x1)
        result.append(x2)
        return result

    elif delta == 0:
        x = -b / (2 * a)
        result.append(x)
        return result

    else:
        return []

# Compare both array to see if they match
def compare_racines(tab1, tab2):
    if len(tab1) != len(tab2):
        return False
    tab1.sort()
    tab2.sort()
    for x, y in zip(tab1, tab2):
        if abs(x - y) > 0.01:
            return False
    return True


class Q1(Question):
    """La fonction 'println!()'"""
    answer = []
    def question(self):
        self.worker.set_options({"allow_copy_paste": True})
        self.answer = ["Bulbizarre", "Salamèche", "Carapuce"]
        return """
        <h3>Introduction à Rust</h3>
        <p>
        Un programme Rust s'écrit dans un fichier avec l'extension <b>.rs</b>.
        Tout programme Rust doit contenir une fonction principale <b>fn main()</b>
        — c'est le point d'entrée du programme, là où l'exécution commence.
        </p>

        <h4>Les macros</h4>
        <p>
        En Rust, une <b>macro</b> est une sorte de "commande spéciale"
        reconnaissable au <b>!</b> à la fin de son nom.
        </p>
        <p>
        Contrairement à une fonction classique, une macro est remplacée
        par du code avant la compilation — c'est le compilateur qui fait
        ce travail. Cela permet des choses qu'une fonction normale ne peut
        pas faire, comme accepter un nombre variable d'arguments.
        </p>
        <p>
        La macro <b>println!</b> permet d'afficher du texte suivi d'un
        retour à la ligne tandis que la macro <b>print!</b> ne fais pas ce retour :
        </p>
        <pre>
fn main() {
    println!("Bonjour !");
    println!("Je m'appelle {}", "Rust");
}</pre>
        <p>
        Les <b>//</b> permettent d'écrire des commentaires — le compilateur les ignore.
        </p>

        <h4>Exercice :</h4>
        <p>
        Modifiez le code à droite pour afficher exactement
        votre pokémon préféré parmi les 3 :
        </p>
        <pre>""" + self.answer[0] + "   " + self.answer[1] + "   " + self.answer[2] + """</pre>
        """
    def tester(self):
        self.display("La zone à droite contient :<pre>"
                     + self.worker.escape(self.worker.execution_result) + "</pre>")
        for a in self.answer:
            if self.worker.execution_result.strip() == a:
                self.display('Et elle contient bien le texte demandé !')
                self.next_question()
                return
        self.display('<p>Elle ne contient pas exactement «'
                    + ", ".join(self.answer) + "»")
        for b in self.answer:
            if canonise(b) in canonise(self.worker.execution_result):
                self.display('<p style="background:#F88">'
                            + 'Auriez-vous mis un caractère en trop ? Un espace en trop ? Ou alors avez-vous oublié une majuscule ?')
                break
    def default_answer(self):
        return """// Une fonction main() est nécessaire pour le bon fonctionnement
// d'un programme Rust
fn main() {
    // println!(...) permet d'afficher ce que l'on veut
    println!("Coucou !");
}
"""

class Q_variables(Question):
    """Les variables et les conditions"""
    age = 0
    def question(self):
        self.age = 15 + millisecs() % 50
        return """
        <h3>Les variables en Rust</h3>
        <p>
        En Rust, on déclare une variable avec le mot-clé <b>let</b> :
        </p>
        <pre>
let age: i32 = 25;            // entier
let pi: f64 = 3.14;           // flottant
let vrai: bool = true;        // booléen
let lettre: char = 'A';       // caractère
let prenom: &str = "Alice";
// chaîne de caractères</pre>
        <p>
        Rust est un langage typé : chaque variable a un type précis.
        Rust peut souvent le deviner seul
        (<a href="https://en.wikipedia.org/wiki/Type_inference">inférence de type</a>),
        mais annoter le type explicitement est une bonne habitude.
        </p>
        <p>
        Si une variable n'est pas utilisée, Rust affiche un warning.
        Pour l'éviter, préfixez son nom d'un <b>_</b> : <code>let _a = 5;</code>
        </p>

        <h4>Les conditions if/else</h4>
        <p>
        En Rust, une condition s'écrit avec <b>if/else</b>, sans parenthèses
        autour de la condition :
        </p>
        <pre>
if date >= 2000 {
    println!("récent");
} else {
    println!("plus ancien");
}</pre>

        <h4>Exercice :</h4>
        <p>
        Déclarez une variable <b>prenom</b> de type <b>&str</b>
        et une variable <b>age</b> de type <b>i32</b> valant <b>""" + str(self.age) + """</b>.
        Affichez-les sur la même ligne avec <b>println!</b> :
        </p>
        <pre>println!("{} {}", prenom, age);</pre>
        <p>
        Ensuite, en utilisant un <b>if/else</b>, affichez <b>"majeur"</b>
        si <b>age</b> est supérieur ou égal à 18, sinon affichez <b>"mineur"</b>.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source

        self.display("La zone en bas à droite contient :<pre>"
                     + self.worker.escape(result) + "</pre>")

        self.check(
            source,
            [
                [r'let _a|let _b|let _vrai|let _caractere',
                 'Les variables exemples ignorées (underscore).'],
                [r"let prenom: &str",
                 "Une variable «prenom» de type &str déclarée."],
                [r"let age: i32",
                 "Une variable «age» de type i32 déclarée."],
                [r'if ',
                 '«if» est utilisé pour la condition.'],
                [r'else',
                 '«else» est utilisé pour le cas contraire.'],
            ])

        # Vérifie que prenom et age apparaissent dans le même println!
        found = False
        for line in source.split('\n'):
            if 'println!' in line and 'prenom' in line and 'age' in line:
                found = True
        self.message(found,
            '«prenom» et «age» affichés ensemble dans un println!.')

        # Vérifie le bon résultat pour le if/else
        expected_word = 'mineur'
        if self.age >= 18:
            expected_word = 'majeur'
        self.message(
            expected_word in result,
            'Le bon mot («majeur» ou «mineur») est affiché selon l\'âge.'
        )

        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """fn main() {
    // Exemples de types en Rust (à ne pas modifier) :
    let _a: i32 = 69;               // Entiers
    let _b: f64 = 3.14;             // Flottants
    let _vrai_ou_faux: bool = true; // Booléens
    let _caractere: char = 'A';     // Caractère

    // À vous : déclarez prenom (&str) et age (i32) ici

    println!("Je suis {} et j'ai {} ans", ???, ???);

    // À vous : ajoutez le if/else ici
}
"""

class Q_variables_mutables(Question):
    """Les variables mutables"""
    answer = 1
    def question(self):
        return """
        <h3>Les variables mutables</h3>
        <p>
        Par défaut en Rust, une variable est <b>immuable</b> — on ne peut pas
        modifier sa valeur après l'avoir déclarée. Si vous essayez, le compilateur
        vous le signale :
        </p>
        <pre>
let x = 5;
x = 10; // ERREUR : cannot assign twice to 
        // immutable variable</pre>
        <p>
        Regardez le panneau <b>Compilation</b> en bas — c'est là que
        Rust vous explique ses erreurs. Ici il dirait quelque chose comme
        <i>"cannot assign twice to immutable variable"</i>.
        </p>
        <p>
        Pour rendre une variable modifiable, on ajoute <b>mut</b> :
        </p>
        <pre>
let mut x = 5;
x = 10; // OK !
x += 1; // OK !</pre>

        <h4>Exercice :</h4>
        <p>
        Modifiez le code pour afficher compteur après qu'il ait été incrémenté de 1.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        if int(result) == answer:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
            return
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """fn main() {
    // Essayez de modifier compteur sans mut... regardez
    // ce que dit le panneau Compilation !
    let compteur = 0;
    compteur += 1;
    println!("???");
}
"""

class Q_Loop_Var_Mutables(Question):
    """La boucle loop"""
    answer = [1,2,3,4,5,6,7,8,9,10]
    def question(self):
        return """
        <h3>La boucle loop</h3>
        <p>
        <b>loop</b> crée une boucle infinie. On en sort avec <b>break</b> :
        </p>
        <pre>
let mut i = 0;
loop {
    i += 1;
    println!("{}", i);
    if i == 3 {
        break; // on sort de la boucle
    }
}</pre>

        <h4>Exercice :</h4>
        <p>
        Modifiez le code à droite pour afficher les nombres de 1 à 10.
        La variable doit afficher les nombres de 1 à 10 uniquement.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        expected = "\n".join(map(str, self.answer))
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        if result == expected:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
            return
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """fn main() {
    let compteur = 0;
    loop {
        compteur += 1;
        println!("???");
        if compteur == 3 {
            break;
        }
    }
}
"""

class Q_tableaux(Question):
    """Les tableaux"""
    answer = [10, 20, 30, 40, 50]
    def question(self):
        return """
        <h3>Les tableaux en Rust</h3>
        <p>
        En Rust, un tableau a une <b>taille fixe</b> définie à la compilation
        et est composé de cases de <b>même type</b>.
        </p>
        <p>
        On le déclare ainsi :
        </p>
        <pre>
let tab: [type; taille] = [valeur1, valeur2, ...];

// Exemples :
let notes: [i32; 3] = [12, 15, 18];
let jours: [&str; 2] = ["Lundi", "Mardi"];</pre>

        <h4>La boucle for</h4>
        <p>
        Pour parcourir un tableau, on utilise une boucle <b>for</b>.
        Avec <b>&</b> on passe une référence du tableau : la fonction le voit mais ne le prend pas, donc le tableau n’est pas perdu après l’appel. :
        </p><pre>
for element in &amp;notes {
    println!("{}", element);
}
        </pre>
        <p>
        Ce code afficherait :
        </p>
        <pre>
12
15
18</pre>

        <h4>Exercice :</h4>
        <p>
        Déclarez un tableau <b>nombres</b> de 5 entiers contenant
        les valeurs 10, 20, 30, 40, 50.
        Affichez chaque élément sur une ligne séparée.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        expected = "\n".join(map(str, self.answer))
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        if result == expected:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """fn main() {
    let nombres: [i32; 5] = [0, 0, 0, 0, 0]; // À modifier
    for element in &nombres {
        println!("???");
    }
}
"""
class Q_INPUT_WHILE(Question):
    """Input et boucle while"""
    def question(self):
        return """
        <h3>Input</h3>
        <p>
        Pour avoir accès aux input/output en Rust, il faut utiliser le module io de la bibliothèque standard.
        Pour lire un input utilisateur il faut donc utiliser <b>std::io::stdin()</b></p>
        <b>.read_line(&mut input);</b> sert à lire jusqu'à ce que l'utilisateur presse la touche Entrée.<br>
        Enfin <b>.expect("Erreur");</b> permet de gérer les potentielles erreurs.</p>
        <pre>
let mut input = String::new();

std::io::stdin()
    .read_line(&mut input)
    .expect("ERREUR");
//Ces lignes permettent d'avoir un input utilisateur</pre>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        if int(result) == 89:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """use std::io;
fn main() {
    let mut input = String::new();

    io::stdin().read_line(&mut input).expect("Erreur");

    prinln!("Tu as écris : {}",input);
}
"""

        
class Q_macros(Question):
    """Introduction aux macros Rust"""
    answer = [10, 20, 30, 40, 50]
    def question(self):
        return """
        <h3>Les macros en Rust</h3>
        <p>
        En Rust, une <b>macro</b> est une sorte de "commande spéciale"
        reconnaissable au <b>!</b> à la fin de son nom.
        </p>
        <p>
        Contrairement à une fonction classique, une macro est remplacée
        par du code avant la compilation — c'est le compilateur qui fait
        ce travail. Cela permet des choses qu'une fonction normale ne peut
        pas faire, comme accepter un nombre variable d'arguments.
        </p>

        <h4>Les macros que vous devrez connâitre dans un premier temps :</h4>
        <ul>
            <li><b>println!</b> — affiche du texte avec un retour à la ligne</li>
            <li><b>print!</b> — affiche du texte sans retour à la ligne</li>
            <li><b>format!</b> — construit une String sans l'afficher</li>
            <li><b>vec!</b> — crée un vecteur (tableau dynamique)</li>
            <li><b>panic!</b> — arrête le programme avec un message d'erreur</li>
        </ul>

        <h4>println! en détail :</h4>
        <pre>
println!("Bonjour");    // texte simple
println!("{}", variable);   // affiche une variable
println!("{} + {} = {}", a, b, a+b);
// plusieurs variables
        </pre>

        <h4>format! :</h4>
        <pre>
let texte = format!("Je suis {} et j'ai {} ans.", prenom, age);
println!("{}", texte);
        </pre>

        <h4>vec! :</h4>
        <pre>
let nombres = vec![1, 2, 3, 4, 5];
// plus souple qu'un tableau fixe
        </pre>
        <p>
        La différence avec un tableau classique <b>[i32; 5]</b> :
        un <b>vec!</b> peut grandir dynamiquement, un tableau a une taille fixe.
        </p>

        <h4>Exercice :</h4>
        <p>
        En utilisant la macro <b>vec!</b>,
        créez un tableau dynamique contenant les valeurs 10, 20, 30, 40, 50
        et affichez chaque élément sur une ligne séparée.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        expected = "\n".join(map(str, self.answer))
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        self.message(
            'let mut nombres = vec![]' in self.worker.source,
            '«nombres» est un tableau dynamique vide et mutable.'
        )
        if result == expected:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """fn main() {
// vec! crée un tableau dynamique
    let mut nombres = ???;
    let mut compteur = 10;
    loop {
        // push() ajoute un élément à la fin du tableau
        nombres.push();
        println!("{}", compteur);
        if compteur == 50 {
            break;
        }
    }
}
"""

class Q_if_else(Question):
    """If/else et rappel boucles"""
    answer = ''
    def question(self):
        return """
        <h3>Les conditions et les boucles</h3>
        <p>
        En Rust, une condition s'écrit avec <b>if/else</b> :
        </p>
        <pre>
if x > 0 {
    println!("positif");
} else {
    println!("négatif ou nul");
}
        </pre>
        <p>
        Pas de parenthèses autour de la condition — c'est propre au Rust.
        </p>

        <h4>Rappel des boucles vues :</h4>
        <ul>
            <li><b>loop</b> — boucle infinie, on sort avec <b>break</b></li>
            <li><b>for x in &tableau</b> — parcourt un tableau</li>
            <li><b>while condition</b> — tourne tant que la condition est vraie</li>
        </ul>

        <h4>Exercice :</h4>
        <p>
        Déclarez une variable <b>nombre</b> avec la valeur de votre choix.
        Affichez <b>"positif"</b> si elle est supérieure à 0,
        <b>"négatif"</b> si elle est inférieure à 0,
        et <b>"nul"</b> si elle est égale à 0.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        self.check(
            self.worker.source,
            [
                [r'if ',
                 '«if» est utilisé pour la condition.'],
                [r'else',
                 '«else» est utilisé pour le cas contraire.'],
            ])
        self.message(
            result in ('positif', 'négatif', 'nul'),
            'Le bon résultat est affiché.'
        )
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """fn main() {
    let nombre = 0; // changez cette valeur
    if ??? {
        println!("???");
    } else if ??? {
        println!("???");
    } else {
        println!("???");
    }
}
"""

class Q_fonctions(Question):
    """Les fonctions"""
    def question(self):
        return """
        <h3>Les fonctions en Rust</h3>
        <p>
        En Rust, une fonction se déclare avec <b>fn</b> :
        </p>
        <pre>
fn addition(a: i32, b: i32) -> i32 {
    a + b  // retour implicite : pas de ; ni de return
}

fn main() {
    let resultat = addition(3, 5);
    println!("{}", resultat);
}
        </pre>
        <p>
        Points clés :
        <ul>
            <li>Les paramètres sont <b>typés</b></li>
            <li>Le type de retour s'écrit après <b>-></b></li>
            <li>La dernière expression sans <b>;</b> est la valeur retournée</li>
            <li>Si la fonction ne retourne rien, on omet le <b>-></b></li>
        </ul>
        </p>

        <h4>Rappel : le while</h4>
        <pre>
let mut i = 0;
while i < 5 {
    println!("{}", i);
    i += 1;
}
        </pre>

        <h4>Exercice :</h4>
        <p>
        Créez une fonction <b>compter</b> qui prend un entier <b>max</b>
        en paramètre et affiche tous les nombres de 1 jusqu'à <b>max</b>
        en utilisant un <b>while</b>.
        Appelez cette fonction depuis le <b>main</b> avec la valeur <b>5</b>.
        </p>
        """
    answer = '\n'.join(map(str, range(1, 6)))
    def tester(self):
        result = self.worker.execution_result.strip()
        expected = self.answer
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        self.message(
            'fn compter' in self.worker.source,
            'Une fonction «compter» est déclarée.'
        )
        self.message(
            'fn compter(max: i32)' in self.worker.source,
            'La fonction prend bien un paramètre «max» de type i32.'
        )
        self.message(
            'while ' in self.worker.source,
            '«while» est utilisé dans la fonction.'
        )
        self.message(
            'compter(5)' in self.worker.source,
            'La fonction est appelée avec la valeur 5 depuis le main().'
        )
        if result == expected:
            self.display("Et elle contient bien le texte demandé !")
            self.next_question()
        else:
            self.display("Elle ne contient pas le texte demandé.")
    def default_answer(self):
        return """fn compter(max: i32) {
    let mut i = 1;
    while ??? {
        println!("???");
        i += 1;
    }
}

fn main() {
    compter(???);
}
"""

class Q_POLYNOME(Question):
    """Racines d'un polynôme du 2nd degré"""
    a = 0
    b = 0
    c = 0
    answer = ''
    def question(self):
        return """
            <h3>Racines d'un polynôme du 2nd degré</h3>
            <p>
                Un polynôme du 2nd degré s'écrit : <b>ax² + bx + c = 0</b>
            </p>
            <p>
                Pour trouver ses racines, on calcule le <b>discriminant</b> :
                <pre>
delta = b² - 4ac
                </pre>
                <ul>
                    <li>Si <b>delta > 0</b> → deux racines réelles :
                        <pre>x1 = (-b + sqrt(delta)) / (2a)
x2 = (-b - sqrt(delta)) / (2a)
                        </pre>
                    </li>
                    <li>Si <b>delta == 0</b> → une racine réelle :
                        <pre>x = -b / (2a)</pre>
                    </li>
                    <li>Si <b>delta &lt; 0</b> → pas de racine réelle</li>
                </ul>
            </p>
            <p>
                Il y a aussi un cas particulier : si <b>a == 0</b>, ce n'est plus
                un polynôme du 2nd degré !
            </p>

            <h4>Exercice :</h4>
            <p>
                Écrivez une fonction <b>racines</b> qui prend <b>a</b>, <b>b</b>, <b>c</b>
                en paramètres (f64) et affiche les racines du polynôme.
                Appelez-la depuis le <b>main</b> avec a=<b>{}</b>, b=<b>{}</b>, c=<b>{}</b>.
            </p>
        """
    def tester(self):
        #extract racines from the C5 result
        def extract_racines(result):
            vals = []
            for line in result.split('\n'):
                line = line.strip()
                if '=' in line:
                    parts = line.split('=')
                    val = parts[1].strip()
                    ok = True
                    for c in val:
                        if c not in "0123456789.-":
                            ok = False
                    if ok and len(val) > 0:
                        vals.append(float(val))
            return vals

        result = self.worker.execution_result
        if result is None:
            result = ""
        result = str(result)
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        # Some tests to compare the results from both result
        racines = compute_racinesTAB(source)
        self.display("Racines calculées : " + str(racines))
        self.display("a,b,c = " + str(check_args(source)))
        extracted = extract_racines(self.worker.execution_result)
        self.display("EXTRACTED = " + JSON.stringify(extracted))

        self.message(   #1. "fn racines" exists
            "fn racines" in source,
            "Une fonction « racines » est déclarée."
        )
        self.message(   #2. case a != 0.0 handled
            "a != 0" in source or "a != 0.0" in source,
            "Le cas « a != 0 » est bien traité."
        )
        self.message(   #3. Is there 2 IF in the "a != 0.0" block ?
            count_if_in_outer_if(source),   # Function created at the beginning of the file
            "Il y a 2 if imbriqués dans le bloc de a != 0.0."
        )
        expected = compute_racinesTAB(self.worker.source)
        extracted = extract_racines(self.worker.execution_result)
        self.message(   #4. Is the result correct
            compare_racines(expected, extracted),
            'Les bonnes racines sont affichées.'
        )

        if self.all_tests_are_fine:
            self.next_question()

    def default_answer(self):
        return """fn racines(a: f64, b: f64, c: f64) {
    if a != 0.0 {
        let delta = b * b - 4.0 * a * c;

        if delta >= 0.0 {
            if delta > 0.0 {
                // deux racines
                let x1 = (-b + delta.sqrt()) / (2.0 * a);
                let x2 = (-b - delta.sqrt()) / (2.0 * a);
                println!("x1 = {}", x1);
                println!("x2 = {}", x2);
            } else {
                // delta == 0
                let x = -b / (2.0 * a);
                println!("x = {}", x);
            }
        } else {
            println!("Pas de racine réelle");
        }
    } else {
        println!("a est nul, ce n'est pas un polynôme du 2nd degré");
    }
}

fn main() {
    racines(0.0, 0.0, 0.0);
}
"""

###############################################################################################################################

class Q_carre(Question):
    """La fonction carré"""
    n = 0
    answer = 0
    def question(self):
        return """
        <h3>Exercice : la fonction carré</h3>
        <p>
        Créez une fonction <b>carre</b> qui prend un entier <b>n</b> en
        paramètre et retourne son carré (<b>n * n</b>).
        </p>
        <p>
        Créez également une fonction <b>main</b> qui appelle <b>carre</b>
        avec la valeur <b>{}</b> et affiche le résultat avec <b>println!</b>.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source

        def extract_result(result):
            return int(result.strip())

        def Test_Carre(nombre):
            return nombre*nombre

        def check_carre_arg(source):
            chunks = source.split("carre(")

            for chunk in chunks[1:]:
                part = chunk.split(")", 1)[0].strip()

                if is_number(part):
                    return int(part)

            return None


        def has_carre_signature(source):
            source_lower = source.lower()   # Function name
            if 'fn carre' not in source.lower():
                return False
            parts = source_lower.split('fn carre')
            if len(parts) < 2:
                return False
            after = parts[1].strip()
            if not after.startswith('('):   # 1st parenthesis
                return False
            after = after[1:]
            paren_parts = after.split(')')  # parameter type
            if len(paren_parts) < 2:
                return False
            param_part = paren_parts[0]
            rest = paren_parts[1]
            colon_parts = param_part.split(':')
            if len(colon_parts) < 2:
                return False
            param_type = colon_parts[1].strip()
            if param_type != 'i32':
                return False
            brace_parts = rest.split('{')   # return type
            rest_before_brace = brace_parts[0]
            if '->' not in rest_before_brace or 'i32' not in rest_before_brace:
                return False
            return True

        def has_main_signature(source):
            if 'fn main' not in source:     # Nom de la fonction
                return False
            parts = source.split('fn main')
            if len(parts) < 2:
                return False
            after = parts[1].strip()
            if not after.startswith('()'):  # No args between the parenthesis
                return False
            return True



        # UNFINISHED
        # Problèmes sur le check du main:
        #     Je veux 2 cas acceptés :
        #         1 - println!(...,carre(X));
        #         2 - une variable contient le carre(X) et ensuite on affiche cette variable
        #     Cas non acceptés :
        #         - println!(un truc écrit dans le main)
        #         - println!(une variable qui n'a aucun rapport)
        #         - pas de println! dans le main
        #         - pas de carre(X) dans le main
        #         - autre cas non True

        def calls_carre_in_main(source):
            source_lower = str(source).lower()
            if 'fn main' not in source: # Check main
                self.display("sortie 4")
                return False
            main = source_lower.split('fn main')[1]

            if "carre(" not in main:    # carre( and println! in 'main'
                self.display("sortie 2")
                return False
            if "println!" not in main:
                self.display("sortie 3")
                return False

            # take the variable name    # Not working
            var_name = None
            if "carre(" in main:
                before = main.split("carre(", 1)[0]

                if "let" in before:
                    let_part = before.split("let")[-1]

                    var_name = let_part.split("=")[0].strip()
                    var_name = var_name.replace("mut", "").strip()
                    var_name = var_name.split(":")[0].strip()
                    self.display("variable = "+var_name)

            # 4. analyser chaque println!
            for part in main.split("println!")[1:]:
                self.display("part =" + part)
                start = part.find("(")
                end = part.find(")")

                if start == -1 or end == -1 or end < start:
                    continue

                args = part[start+1:end]

                # CAS 1 : carre in println!()
                if "carre(" in args:
                    self.display("Ca marche 1")
                    return True

                # CAS 2 : variable linked with carre()
                if var_name and var_name in args:
                    self.display("Ca marche 2")
                    return True
            self.display("sortie 4")
            return False

        self.message(   #NOT DONE YET
            calls_carre_in_main(source),
            'Le résultat de «carre» est affiché dans le main.'
        )



        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        self.message(   #DONE
            has_carre_signature(self.worker.source),
            'La fonction «carre» a un paramètre i32 et retourne un i32.'
        )
        self.message(   #DONE
            has_main_signature(source),
            'Une fonction «main()» a été créée.'
        )

        self.display("NBinC5= "+str(check_carre_arg(source)))
        self.display("Calcul interne= " + str(Test_Carre(check_carre_arg(source))))
        self.display("result extrait= " + str(extract_result(result)))
        arg = check_carre_arg(source)
        resultC5 = extract_result(result)
        self.message(   #DONE
            Test_Carre(arg) == resultC5,
            "Le bon résultat est affiché."
        )

    def default_answer(self):
        self.n = 2
        self.answer = self.n * self.n
        return """// Créez votre fonction carre ainsi que
// votre fonction main ici
"""

class Q_End(Question):
    """Félicitation vous êtes arrivé au bout !"""
    def question(self):
        return "Plus de questions, vous êtes libre d'essayer ce que vous souhaitez !"
    def tester(self):
        self.display('FINI !')
    def default_answer(self):
        return """fn main(){

}
"""