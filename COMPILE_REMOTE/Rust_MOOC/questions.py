# Les options suivantes ne sont utilisées qu'à la création de la session.
# Pour les modifier il faut cliquer sur 'Edit' pour éditer les paramètres de session.

COURSE_OPTIONS = {
            'title': 'Test Rust',
            'compiler': 'cargo',
            'state': 'Ready',
            'checkpoint': 0,
            "forbid_question_copy": 0,
            'allow_copy_paste': 1,
            "sequential": 0,
            'allowed': [
                "execve", "brk", "mmap", "access", "openat", "fstat", "close", "read", "pread64",
                "arch_prctl", "set_tid_address", "set_robust_list", "rseq", "mprotect", "prlimit64",
                "getrandom", "munmap", "poll", "rt_sigaction", "lseek", "sched_getaffinity", "sigaltstack",
                "gettid", "exit_group", "rt_sigprocmask", "clone3"
            ],
            'positions' : {
                "question":[1,32,0,50,"#EFE"],
                "tester":[1,32,51,49,"#EFE"],
                "editor":[33,37,0,70,"#FFF"],
                "compiler":[33,67,70,30,"#EEF"],
                "executor":[70,30,0,70,"#EEF"],
                "time":[80,20,98,2,"#0000"],
                "index":[0,1,0,100,"#0000"]
                }
            }


def canonise(txt):
    return txt.lower().replace(' ', '')

def canoniseNotLower(txt):
    txt = str(txt)
    return txt.replace(' ', '')

def canoniseALLNotLower(txt):
    if txt is None :
        return None
    txt = str(txt)
    while ' ' in txt or '\n' in txt:
        txt = txt.replace(' ', '')
        txt = txt.replace('\n','')
    return txt

def canoniseALL(txt):
    return canoniseALLNotLower(txt.lower())


# Extract the '{}' block associated with a given search text
def extract_block(txt, start, open_char='{', close_char='}'):
    """
    Extrait le contenu entre l'accolade ouvrante (ou open_char) à l'index 'start' et sa
    fermante correspondante (close_char) (gère l'imbrication par comptage de profondeur).

    Précondition : txt[start] doit être open_char, sinon le comportement
    est indéfini (peut renvoyer un résultat tronqué ou incorrect).

    LIMITATIONS CONNUES :
    - Ne gère PAS les accolades à l'intérieur de chaînes de caractères
      ou de commentaires. Exemple qui casse la fonction :
          fn f() { let s = "}"; }
      → le '}' dans la chaîne est compté comme une vraie fermeture.
    - Si le bloc n'est jamais fermé (pas assez de close_char), retourne
      '' plutôt que de signaler l'erreur.

    Exemples :
        extract_block("{ a { b } c }", 0)        -> " a { b } c "
        extract_block("fn f() { x } g()", 7)      -> " x "
        extract_block("{ unclosed", 0)             -> ''  (bloc non fermé)
        extract_block('{ "}" }', 0)                -> ' "'  (FAUX : cassé par la chaîne)
    """
    depth = 0
    i = start
    block_start = -1
    while i < len(txt):
        if txt[i] == open_char:
            if depth == 0:
                block_start = i + 1
            depth += 1
        elif txt[i] == close_char:
            depth -= 1
            if depth == 0:
                return txt[block_start:i]
        i += 1
    return ''

# Extract the '{}' block whose opening brace is at 'start', matching nested braces
# (also stop the repetition I had multiple times in the file)
def extract_struct(source, search_text, block_start="{", block_end="}"):
    if source is None:
        return ""
    idx = source.find(search_text)
    if idx == -1:
        return ""

    idx = source.find(block_start, idx)
    if idx == -1:
        return ""

    return extract_block(source, idx, block_start, block_end)


# useful for check_args

def is_number(x):
    x.match(RegExp('[-+]?[0-9]+([.][0-9]*)?'))

# def is_number(x):
#     x = x.strip()

#     if x == "":
#         return False

#     # allows numbers, -, .
#     allowed = "0123456789.-"

#     for c in x:
#         if c not in allowed:
#             return False
#     return True

# took values from racines(...) from 'main' in C5
# This returns the 3 values ​​from the first valid call to 'racines'.
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

    if a == 0.0:
        return "pas 2nd degré"

    delta = b * b - 4 * a * c

    if delta > 0:
        sqrt_delta = delta ** 0.5

        x1 = (-b + sqrt_delta) / (2 * a)
        x2 = (-b - sqrt_delta) / (2 * a)
        result.append(x1)
        result.append(x2)

    elif delta == 0:
        x = -b / (2 * a)
        result.append(x)
    return result


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


class Q_Hello_World(Question):
    """Hello World et prise en main de C5"""
    def question(self):
        return """
        <h3>Bienvenue sur C5 !</h3>
        <p>
        Bienvenue dans cet environnement pour apprendre le langage Rust.
        Avant de commencer, prenons un instant pour découvrir l'interface.
        L'écran est divisé en plusieurs zones :
        </p>
        <ul>
            <li><b>Question</b> (ici, en haut à gauche) : c'est ici que se trouvent
                le cours et les exercices à réaliser. C'est votre fil conducteur.</li>
            <li><b>Les objectifs à atteindre</b> (en bas à gauche) : cette section indique les différentes étapes à accomplir. Au fur et à mesure de votre progression, vous pourrez vérifier que chaque objectif est bien validé.</li>
            <li><b>Code source</b> (au centre) : c'est votre éditeur, où vous
                écrivez le code Rust demandé par chaque exercice.</li>
            <li><b>Compilation</b> (en bas) : affiche le résultat de la compilation de
                votre code — les éventuelles erreurs ou warnings y apparaissent.</li>
            <li><b>Exécution</b> (à droite) : affiche ce que votre programme produit une
                fois compilé avec succès (ce qui est affiché par <b>println!</b>
                par exemple).</li>

        </ul>
        <p>
        En Rust, un programme <b>exécutable</b> doit obligatoirement contenir une fonction
        <b>main</b> : c'est son point d'entrée, la première fonction lancée au démarrage.
        On voit ici que la zone <b>Compilation</b> est rouge : le compilateur affiche
        «<i>consider adding a `main` function</i>», expliquant justement qu'il manque cette
        fonction 'main' dans le code source actuel. Vous notez que quand on arrive sur une question,
        le code est automatiquement compilé et exécuté si la compilation a réussi.
        </p>
        <p>
        <i>Remarque :</i> Ce n'est pas le cas pour une <b>bibliothèque</b>, destinée à être utilisée par
        d'autres programmes plutôt qu'exécutée directement : elle n'a pas de <b>main</b>,
        elle expose simplement des fonctions, structs et types utilisables par le code
        qui l'importe. Dans ce cours, on ne travaille que sur des programmes exécutables,
        donc <b>main</b> sera toujours nécessaire.
        </p>
        <p>
        Les « <b>//</b> » permettent d'écrire des commentaires — le compilateur les ignore.
        </p>

        <h4>Prise en main de C5</h4>
        <p>
        Tout ce que vous tapez avec C5 est enregistré, mais pour être capable
        de retrouver le code dans un état donné, par exemple pour chaque exercice d'une question ou quand
        la question est terminée, on peut sauvegarder le code en cliquant sur <b>l'enveloppe</b>.
        C5 va vous demander de donner un nom (un TAG) qui représente l'état de
        cette sauvegarde. Ça peut être «exo1 fini» ou «fonction XXX terminée» voire «Amélioration
        présentation» : l'objectif est que vous soyez capable de retrouver cet état du code si besoin.
        </p>
        <p>
        Plus tard lorsque vous souhaiterez revenir au code initial, vous avez une petite box nommée
        <b>Retourner sur</b> avec le code initial et les éventuelles sauvegardes que vous aurez réalisé.
        Si vous voulez retrouver un moment particulier de ce que vous avez tapé
        mais qui n'est pas dans la sauvegarde, il suffit de cliquer sur <b>l'arbre</b>
        à gauche de «Code source». Un graphe apparaît : vous voyez les suppressions et
        ajouts de caractères, et les endroits des sauvegardes. Il vous reste à chercher
        l'endroit qui vous intéresse.
        </p>
        <p>
        Notez que la dernière version du code est chargée à chaque connexion
        à une session de C5. Vous pouvez passer à une autre question en cliquant dessus (en haut à
        gauche de la zone Question) si elle est sur fond jaune (le fond passe en
        vert quand la question a été correctement répondue).
        </p>

        <p>
        <b>Attention</b> ! Lorsque vous exécutez le programme (<b>F9</b>) et que tous les critères de la
        question sont validés, vous passerez <b>automatiquement</b> à la question suivante.
        Prenez donc le temps de bien lire les explications et les remarques affichées.
        </p>
        <h3>Votre premier programme</h3>
        <p>
        Après avoir recopié le morceau de code ci-dessous dans le code source, compilez-le (<b>F9</b>).
        S'il n'y a pas d'erreur de compilation, vous pourrez directement observer
        le résultat de son exécution avec « Hello World » écrit dans la zone d'exécution.
        Félicitations, votre premier programme Rust fonctionne correctement !
        </p>
        <pre>
fn main() {
    println!("Hello World");
}</pre>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        nb_space = 0
        too_many_spaces = False
        for char in result:
            if char == ' ': # if space in result
                nb_space += 1
                if nb_space >= 2 :
                    too_many_spaces = True

        self.message(
            result == 'Hello World',
            "Le programme affiche bien «Hello World»."
        )
        if self.all_tests_are_fine and not too_many_spaces:
            self.next_question()
            return
        else:
            self.display('<p style="background:#F88">' + "Copiez le texte exact demandé dans l'énoncé.")
            return
    def default_answer(self):
        return """// Copiez ici !
"""


class Q_println(Question):
    """La fonction 'println!()'"""
    answer = []
    def question(self):
        self.nb_version = 4
        self.version = self.random_version(4)
        self.worker.set_options({"allow_copy_paste": True})
        self.answer = [["Bulbizarre", "Salamèche", "Carapuce"],
                       ["Bleu", "Jaune", "Rouge"],
                       ["Paris", "Lyon", "Marseille"],
                       ["Paris", "Tokyo", "New-York"]
                    ]
        question = """
        <h3>Introduction à Rust</h3>
        <p>
        Un programme Rust s'écrit normalement dans un fichier avec l'extension
        <b>.rs</b> (c'est par exemple ce que vous aurez si vous cliquez sur 💾)
        Comme vu dans la question précédente, tout programme Rust doit contenir
        une fonction principale <b>fn main()</b> — c'est le point d'entrée du
        programme, là où l'exécution commence. Sans ça vous aurez un message d'erreur à la compilation vous demandant d'ajouter une fonction main au fichier source.
        </p>

        <h4>Les macros</h4>
        <p>
        En Rust, une <b>macro</b> est une sorte de "commande spéciale"
        reconnaissable au <b>« ! »</b> à la fin de son nom.
        </p>
        <p>
        Contrairement à une fonction classique, une macro est remplacée
        par du code avant la compilation — c'est le compilateur qui fait
        ce travail. Cela permet des choses qu'une fonction normale ne peut
        pas faire, comme accepter un nombre variable de paramètres (aussi appelés arguments).
        </p>
        <p>
        La macro <b>println!</b> permet d'afficher du texte suivi d'un
        retour à la ligne tandis que la macro <b>print!</b> ne fait pas ce retour :
        </p>
        <pre>
fn main() {
    println!("Bonjour !");
}</pre>
        <p>
        On verra en détail les variables à la question suivante, mais notons ici que
        pour afficher le contenu de variables, il faut mettre pour chaque
        variable « {} » dans la chaîne de caractères à l'endroit où le contenu
        est affiché, et donner dans l'ordre les variables correspondantes
        derrière la « , ». On dit que les variables sont les arguments de
        <b>println!</b> (on verra ça en parlant des fonctions). On a 2 exemples ci-dessous :
        dans le premier on passe une chaîne de caractères, puis dans le second on passe
        une valeur entière en arguments de <b>println!</b> :
        </p>
        <pre>
println!("Je m'appelle {}", "Rust");
let nb: i32 = 25;
println!("Il y a {} fleurs", nb);</pre>
"""
        Exercice = [
        """<h4>Exercice :</h4>
        <p>
        Cette question a plusieurs <b>versions alternatives</b>, que vous pouvez voir uniquement si vous avez su répondre correctement. Vous y accéderez en cliquant sur un bouton qui apparaîtra dans Les buts que vous devez atteindre. Lorsqu'il n'y en aura plus à disposition vous serez averti.
        </p>
        <p>
        Écrivez un programme principal affichant uniquement
        votre pokémon préféré parmi les 3 :
        </p>
        <pre>""" + self.answer[0][0] + "   " + self.answer[0][1] + "   " + self.answer[0][2] + """</pre>
        """
        ,
        """<h4>Exercice :</h4>
        <p>
        Cette question a plusieurs <b>versions alternatives</b>, que vous pouvez voir uniquement si vous avez su répondre correctement. Vous y accéderez en cliquant sur un bouton qui apparaîtra dans Les buts que vous devez atteindre. Lorsqu'il n'y en aura plus à disposition vous serez averti.
        </p>
        <p>
        Écrivez un programme principal affichant uniquement
        votre couleur préférée parmi les 3 :
        </p>
        <pre>""" + self.answer[1][0] + "   " + self.answer[1][1] + "   " + self.answer[1][2] + """</pre>
        """
        ,
        """<h4>Exercice :</h4>
        <p>
        Cette question a plusieurs <b>versions alternatives</b>, que vous pouvez voir uniquement si vous avez su répondre correctement. Vous y accéderez en cliquant sur un bouton qui apparaîtra dans Les buts que vous devez atteindre. Lorsqu'il n'y en aura plus à disposition vous serez averti.
        </p>
        <p>
        Écrivez un programme principal affichant uniquement
        votre ville préférée parmi les 3 :
        </p>
        <pre>""" + self.answer[2][0] + "   " + self.answer[2][1] + "   " + self.answer[2][2] + """</pre>
        """
        ,
        """<h4>Exercice :</h4>
        <p>
        Cette question a plusieurs <b>versions alternatives</b>, que vous pouvez voir uniquement si vous avez su répondre correctement. Vous y accéderez en cliquant sur un bouton qui apparaîtra dans Les buts que vous devez atteindre. Lorsqu'il n'y en aura plus à disposition vous serez averti.
        </p>
        <p>
        Écrivez un programme principal affichant la ville ayant la plus grande superficie parmi :
        </p>
        <pre>""" + self.answer[3][0] + "   " + self.answer[3][1] + "   " + self.answer[3][2] + """</pre>
        """
        ]
        question += Exercice[self.version]
        return question
    def tester(self):
        source = self.worker.source
        result = self.worker.execution_result
        self.display("La zone à droite contient :<pre>"
                     + self.worker.escape(result) + "</pre>")
        if source.strip() == '':
            self.display("Vous n'avez encore rien écrit. Le message d'erreur est totalement normal. A vous de répondre à la question !")
            return
        is_there_space = False
        for char in result:
            if char == ' ': # if space in result
                is_there_space = True
                self.display('<p style="background:#F88">' + 'Enlevez les espaces !')
                return

        for a in self.answer[self.version]:

            if self.version == 3:   # Special version when you need to have the good answer
                if 'Tokyo' == canoniseALLNotLower(result):
                    self.display('<p style="background:#8F8">' + "C'est bien la bonne réponse !")
                    if self.round >= 3 :
                        self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                        self.next_question()
                        return
                    else :
                        self.display(self.new_round_button('Essayer une alternative'))
                        self.next_question()
                        return
                elif 'Paris' == canoniseALLNotLower(result) or 'New-York' == canoniseALLNotLower(result):
                    self.display('<p style="background:#FDB">' + "C'est faux !")
                    return
                else:
                    self.display('<p style="background:#F88">' + "Ce n'est pas une réponse proposée...")
                    return

            if result.strip() == a and not is_there_space : # Other versions
                self.display('<p style="background:#8F8">' + 'Et elle contient bien le texte demandé !')
                if self.round >= 3 :
                    self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                    self.next_question()
                    return
                else :
                    self.display(self.new_round_button('Essayer une alternative'))
                    self.next_question()
                    return

        for b in self.answer[self.version]:
            if canonise(b) in canonise(result):
                self.display('<p style="background:#FDB">'
                            + 'Auriez-vous mis un caractère en trop ? Ou alors avez-vous un problème de majuscule ?')
                return
        self.display('<p style="background:#F88">' + 'Elle ne contient pas exactement : «'+self.answer[self.version][0]+'», «'+self.answer[self.version][1]+'» ou «'+self.answer[self.version][2]+"»")
    def default_answer(self):
        return """
"""


class Q_variables(Question):
    """Les variables"""
    def question(self):
        return """
        <h3>Les variables</h3>
        <p>
        En Rust, on déclare une variable avec le mot-clé <b>let</b> :
        </p>
        <pre>
let age: i32 = 25;            // entier
let pi: f64 = 3.14;           // flottant
let vrai: bool = true;        // booléen
let lettre: char = 'A';       // caractère
let prenom: &str = "Alice";   // ch. de caractères</pre>
        <p>
        Rust est un langage typé : chaque variable a un type précis.
        Rust peut le deviner seul
        (<a href="https://fr.wikipedia.org/wiki/Inf%C3%A9rence_de_types">inférence de type</a>),
        mais annoter le type explicitement est une bonne habitude.
        </p>
        <p>
        Si une variable n'est pas utilisée, Rust affiche un warning
        comme c'est le cas si vous regardez le résultat de la compilation du
        code source donné.
        Pour l'éviter, préfixez le nom de la variable concernée par un <b>« _ »</b>
        ce qui nous donne : <code>let _a = 5;</code>
        </p>

        <h4>Afficher un booléen</h4>
        <p>
        Un booléen peut être affiché directement avec <b>println!</b>, qu'il s'agisse
        d'une valeur littérale, du résultat d'une comparaison, ou d'une comparaison
        impliquant une variable :
        </p>
        <pre>
println!("{}", true);   // booléen littéral
println!("{}", 10 > 5); // comparaison

// comparaison avec variable
let texte = "Bonjour";
println!("{}", texte == "Bonsoir");</pre>

        <p>
        Attention : Rust interdit de comparer directement un <b>entier</b> et un
        <b>flottant</b>, même si la valeur semble équivalente. Il faut convertir
        explicitement l'un vers le type de l'autre avec <b>as</b> :
        </p>
        <pre>
let entier = 5;
let reel = 5.0;
println!("{}", entier == reel);        // ❌
println!("{}", entier as f64 == reel); // ✅</pre>
        <p>
        Vous pouvez d'ailleurs voir qu'ici les types des variables sont devinés par Rust.
        </p>
        <h4>Exercice :</h4>
        <p>
        Déclarez une variable <b>prenom</b> de type <b>&amp;str</b>
        et une variable <b>age</b> de type <b>i32</b>.
        Affichez les avec <b>println!</b>.
        Enfin vous afficherez le résultat de la comparaison entre la variable <b>age</b> et du nombre 18.
        Vous devrez avoir false ou true d'affiché.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result
        source = self.worker.source
        self.display("La zone en bas à droite contient :<pre>"
                     + self.worker.escape(result) + "</pre>")


        self.display("Il y a un soucis ici. Il faut que nr_warnings/nr_errors correspondes au nombre de warnings/errors de la sortie compilation, hors ici les valeurs resteront à 0 tout le temps. Je peux faire marcher ça en créeant un self.compile_result=message dans le fichier compile_remote.py mais Thierry m'a demandé d'utiliser les variables nr_warnings/nr_errors---------------------------------------------------------------")
        self.display("nr_warnings = "+ self.worker.nr_warnings)
        self.display("nr_errors = "+ self.worker.nr_errors)
        # self.display("compile_result = " + str(self.worker.compile_result))

        self.message(
            self.worker.nr_warnings == 0 and self.worker.nr_errors == 0,
            "Il ne reste aucun warning dû à la non-utilisation de certaines variables."
        )
        self.message(
            "let prenom:&str" in source or "let prenom : &str" in source or
            "let prenom: &str" in source or "let prenom :&str" in source,
            "Une variable «prenom» de type &amp;str déclarée."
        )
        self.message(
            "let age:i32" in source or "let age : i32" in source or
            "let age: i32" in source or "let age :i32" in source,
            "Une variable «age» de type <b>i32</b> déclarée."
        )

        main_struct = extract_struct(source, "fn main()")
        println_struct = extract_struct(main_struct, "println!(", '(', ')')

        # 'prenom' and 'age' appear in the same 'println!'
        found = False
        if ',prenom' in canoniseALLNotLower(println_struct) and ',age' in canoniseALLNotLower(println_struct) :
            found = True
        self.message(
            found,
            '«prenom» et «age» affichés ensemble dans un println!.'
        )
        self.message(
            'println!("{}",age==18)' in canoniseALLNotLower(source) or 'print!("{}",age==18)' in canoniseALLNotLower(source) or 'println!("{}",age<=18)' in canoniseALLNotLower(source) or 'print!("{}",age<=18)' in canoniseALLNotLower(source) or 'println!("{}",age>=18)' in canoniseALLNotLower(source) or 'print!("{}",age>=18)' in canoniseALLNotLower(source) or 'println!("{}",age>18)' in canoniseALLNotLower(source) or 'print!("{}",age>18)' in canoniseALLNotLower(source) or'println!("{}",age<18)' in canoniseALLNotLower(source) or 'print!("{}",age<18)' in canoniseALLNotLower(source) or 'println!("{}",age!=18)' in canoniseALLNotLower(source) or 'print!("{}",age!=18)' in canoniseALLNotLower(source),
            "Affichez le résultat de la comparaison entre la variable 'age' que vous avez initialisé et '18'"
        )

        if self.all_tests_are_fine :
            self.next_question()
            return

    def default_answer(self):
        return """fn main() {
    //  (préfixez la variable) :
    let caractere: char = 'A';  // Caractère

    // À vous : déclarez prenom (&str) et age (i32) ici
    // et affichez les.
}
"""

def TestQ4(version,number):
    if version == 1:
        if number >=30:
            return "canicule"
        elif number >=20:
            return "agréable"
        else:
            return "frais"
    if version == 2:
        if number >= 18:
            return "félicitations"
        elif number >=16:
            return "très bien"
        elif number >=14:
            return "bien"
        elif number >=12:
            return "assez bien"
        elif number >=10:
            return "sans mention"
        else:
            return "raté"

def RechercheVar(source, mot_a_chercher):
    """
    Cherche une ligne d'une typo similaire à : 'let mot_a_chercher: type = valeur;'
    et retourne la valeur entière affectée.
    Retourne None si non trouvée ou si la valeur n'est pas un entier.
    """
    for line in source.split('\n'):
        if mot_a_chercher in line and '=' in line:
            try:
                valeur = line.split('=')[1].strip().replace(';', '')
                return int(valeur)
            except:
                pass
    return None

class Q_Condition(Question):
    """Les conditions if/else"""
    def question(self):
        self.nb_version = 3
        self.version = self.random_version(3)
        question = """
        <h3>Les conditions if/else</h3>
        <p>
        En Rust, une structure conditionnelle s'écrit avec <b>if/else</b>, sans parenthèses
        obligatoires autour de l'expression testée (contrairement à d'autres langages comme le C).
        L'expression testée après <b>if</b> doit obligatoirement être de type <b>bool</b>
        (<b>true</b> ou <b>false</b>). Contrairement à certains langages, Rust n'accepte
        pas un entier ou une chaîne à la place d'un booléen.
        </p>
        <pre>
if date >= 2000 {
    println!("récent");
} else {
    println!("plus ancien");
}</pre>
        <p>
        Pour tester des conditions en Rust, on utilise les opérateurs de comparaison suivants :
        </p>
        <ul>
            <li><b>==</b> : égal à</li>
            <li><b>!=</b> : différent de</li>
            <li><b>&gt;</b> : strictement supérieur à</li>
            <li><b>&lt;</b> : strictement inférieur à</li>
            <li><b>&gt;=</b> : supérieur ou égal à</li>
            <li><b>&lt;=</b> : inférieur ou égal à</li>
        </ul>

        <h4>Enchaîner plusieurs conditions avec else if</h4>
        <p>
        On peut tester plusieurs conditions successives avec <b>else if</b> :
        </p>
        <pre>
if date >= 2020 {
    println!("très récent");
} else if date >= 2000 {
    println!("récent");
} else {
    println!("plus ancien");
}</pre>
        <p>
        Rust évalue les conditions dans l'ordre et exécute uniquement le premier bloc
        dont la condition est vraie. Le <b>else</b> final (facultatif) s'exécute si
        aucune condition n'est vérifiée.
        </p>
"""
        Exercice = [
        """
        <h4>Exercice :</h4>
        <p>
        Initialisez un entier <b>moyenne</b> à 15.<br>
        Avec <b>if/else</b>, affichez <b>"accepté"</b> si <b>moyenne</b> est supérieure
        à 10, sinon affichez <b>"redouble"</b>.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Initialisez un entier <b>temperature</b> avec la valeur de votre choix. Puis
        en utilisant <b>if/else if</else/b> affichez :
        </p>
        <ul>
            <li>30 ou plus → <b>"canicule"</b></li>
            <li>20 ou plus → <b>"agréable"</b></li>
            <li>sinon → <b>"frais"</b></li>
        </ul>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Initialisez un entier <b>moyenne</b> avec la valeur de votre choix. Puis
        en utilisant <b>if/else if/else</b>, affichez la mention correspondante :
        </p>
        <ul>
            <li>18 ou plus → <b>"félicitations"</b></li>
            <li>16 ou plus → <b>"très bien"</b></li>
            <li>14 ou plus → <b>"bien"</b></li>
            <li>12 ou plus → <b>"assez bien"</b></li>
            <li>10 ou plus → <b>"sans mention"</b></li>
            <li>en dessous de 10 → <b>"raté"</b></li>
        </ul>
        """
        ]
        question += Exercice[self.version]
        return question
    def tester(self):
        result = self.worker.execution_result
        source = self.worker.source
        self.display("La zone en bas à droite contient :<pre>"
                     + self.worker.escape(result) + "</pre>")

        main_struct = extract_struct(source,"fn main()")

        if self.version == 0 :

            self.message(
                'letmoyenne:i32=15;' in canoniseALLNotLower(main_struct),
                "Une moyenne a bien été initialisée à 15."
            )
            self.message(
                'ifmoyenne>=10{' in canoniseALLNotLower(main_struct),
                "Une condition «if moyenne >= 10» est présente."
            )
            self.message(
                'else{' in canoniseALLNotLower(main_struct),
                "On utilise bien else pour vérifier les autres cas"
            )
            self.message(
                canoniseALLNotLower(result) == 'accepté',
                "Le résultat doit être <b>'accepté'</b>."
            )

        if self.version == 1 :

            self.message(
                'lettemperature:i32=' in canoniseALLNotLower(main_struct),
                "La température a bien été initialisée en tant qu'entier."
            )
            self.message(
                'iftemperature>=30{' in canoniseALLNotLower(main_struct),
                "Une condition «if temperature >= 30» est présente."
            )
            self.message(
                'elseiftemperature>=20{' in canoniseALLNotLower(main_struct),
                "Une condition «else if temperature >= 20» est présente."
            )
            self.message(
                'else{' in canoniseALLNotLower(main_struct),
                "On utilise bien else pour vérifier les autres cas"
            )
            number = RechercheVar(source,"temperature")
            self.message(
                canoniseALLNotLower(result)==TestQ4(self.version,number),
                "On a le résultat attendu !"
            )

        if self.version == 2 :

            self.message(
                'letmoyenne:i32=' in canoniseALLNotLower(main_struct),
                "Une moyenne a bien été initialisée en tant qu'entier."
            )
            self.message(
                'ifmoyenne>=18{' in canoniseALLNotLower(main_struct),
                "Une condition «if moyenne >= 18» est présente."
            )
            self.message(
                'elseifmoyenne>=16{' in canoniseALLNotLower(main_struct),
                "Une condition «elif moyenne >= 16» est présente."
            )
            self.message(
                'elseifmoyenne>=14{' in canoniseALLNotLower(main_struct),
                "Une condition «elif moyenne >= 14» est présente."
            )
            self.message(
                'elseifmoyenne>=12{' in canoniseALLNotLower(main_struct),
                "Une condition «elif moyenne >= 12» est présente."
            )
            self.message(
                'elseifmoyenne>=10{' in canoniseALLNotLower(main_struct),
                "Une condition «elif moyenne >= 10» est présente."
            )
            self.message(
                'else{' in canoniseALLNotLower(main_struct),
                "On utilise bien else pour vérifier les autres cas"
            )
            number = RechercheVar(source,"moyenne")
            self.message(
                canoniseALLNotLower(result)==TestQ4(self.version,number),
                "On a le résultat attendu !"
            )

        if self.all_tests_are_fine:
            self.display('<p style="background:#8F8">' + "Vous avez bien respectés les conditions.")
            if self.round>=2 :
                self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                self.next_question()
                return
            else :
                self.next_question()
                self.display(self.new_round_button('Essayer une alternative'))
                return

    def default_answer(self):
        return """fn main(){

}
"""


class Q_variables_mutables(Question):
    """Les variables mutables"""
    def question(self):
        return """
        <h3>Les variables mutables</h3>
        <p>
        Par défaut en Rust, une variable est <b>immuable</b> : on ne peut pas
        modifier sa valeur après l'avoir déclarée. Si vous essayez, le compilateur
        vous le signale :
        </p>
        <pre>
let x = 5;
x = 10; // ERREUR : cannot assign twice to
        // immutable variable</pre>
        <p>
        L'erreur de l'exemple ci-dessus signifie que la variable <b>x</b> a déjà reçu une valeur (<b>5</b>)
        lors de sa déclaration, et que Rust refuse de lui en attribuer une nouvelle
        (<b>10</b>) car elle est <b>immuable</b> par défaut. Pour autoriser cette
        modification, il faudrait la déclarer avec <b>mut</b> :
        <code>let mut x = 5;</code>
        </p>
        <pre>
let mut x = 5;
x = 10; // OK !
x += 1; // OK !</pre>
        <p>
        Notez que même dans l'exemple ci-dessus, vous aurez un warning vous expliquant que vous n'avez jamais utilisé la déclaration initiale de la variable. Pour ne pas avoir ce warning il faut que la mutabilité ait un vrai sens d'utilisation, pas comme dans l'exemple précédent. Cependant cela vous permet de mieux comprendre le principe de mutabilité des variables avec cet aperçu.
        </p>

        <h4>Exercice :</h4>
        <p>
        Déclarez une variable <b>reponse</b>. Ce sera un booléen initialisé de base à <b>false</b>. Affichez ce booléen et ensuite vous modifierez ce booléen en le passant à <b>true</b>. Il est possible que vous ayez l'erreur indiquée dans le cours. Dans ce cas cela signifie que la variable que vous avez initialisée n'est pas une variable modifiable. Rendez la donc modifiable. Une fois la variable affecté à <b>true</b>, vous l'afficherez de la même manière qu'avant afin de bien montrer que la modification de la variable a bien été acceptée.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        reponse_init = False
        count_print = 0
        print_reponse = False
        for line in source.split('\n'):
            if 'let' in line and 'reponse:bool=false;' in canoniseALLNotLower(line):
                reponse_init = True
            if 'print' in line and """!("{}",reponse)""" in canoniseALLNotLower(line):
                print_reponse = True
                count_print += 1
        self.message(
            reponse_init,
            "reponse» est bien initialisée."
        )
        self.message(
            'letmutreponse:bool=false;' in canoniseALLNotLower(source),
            "«reponse» est une variable mutable (modifiable)."
        )
        self.message(
            print_reponse,
            "Vous affichez la variable «reponse» une première fois."
        )
        self.message(
            'reponse=true;' in canoniseALLNotLower(source),
            "Vous affectez bien la variable à «true»"
        )
        self.message(
            count_print == 2,
            "Vous affichez la variable «reponse» une seconde fois."
        )
        if self.all_tests_are_fine:
            if canoniseALLNotLower(result) == "falsetrue":
                self.display('<p style="background:#8F8">' + "Parfait, vous semblez avoir compris le principe de mutabilité. Retenez le bien, vous l'utiliserez très souvent !")
                self.next_question()
                return
            else:
                self.display('<p style="background:#F88">' + "Ce n'est pas l'affichage attendu !")
                return
    def default_answer(self):
        return """fn main() {

}
"""


class Q_Fonctions(Question):
    """Les fonctions"""
    def question(self):
        self.nb_version = 3
        self.version = self.random_version(3)
        question = """
        <h3>Les fonctions en Rust</h3>
        <p>
        Une fonction se déclare avec <b>fn</b>, suivi de son nom, des arguments
        entre parenthèses, et éventuellement du type de retour après <b>-></b> de la façon suivante :
        </p>
        <pre>
fn nom_fn(par1: Type1, par2: Type2) -> TypeRetour {
    // corps de la fonction
}</pre>

        <h4>Les paramètres</h4>
        <p>
        Chaque paramètre doit obligatoirement être <b>typé</b> — contrairement
        aux variables avec <b>let</b>, Rust ne peut pas deviner le type d'un argument :
        </p>
        <pre>
fn addition(a: i32, b: i32) -> TypeRetour {
    // corps de la fonction
}</pre>
        <p>
        On peut avoir autant d'argument qu'on veut, séparés par des virgules,
        et même aucun argument du tout.
        </p>
        <pre>
fn aucun_argument() -> TypeRetour {
    // corps de la fonction
}

fn plusieurs_arguments(a: i32, b: f64, c: char) -> TypeRetour {
    // corps de la fonction
}</pre>

        <h4>Le type de retour</h4>
        <p>
        Le type de retour s'écrit après <b>-></b>, juste avant l'accolade ouvrante.
        </p>
        <pre>
fn carre(x: i32) -> i32 { // retourne un i32
    // corps de la fonction
}</pre>

        <p>
        On peut aussi n'avoir aucun retour souhaité, dans ce cas on omet complètement le <b>-></b> comme dans cette fonction :
        <pre>
fn affiche(x: i32) { // ne retourne rien, pas de ->
    // corps de la fonction
}</pre>

        <h4>Return vs retour implicite</h4>
        <p>
        Rust a deux façons de retourner une valeur. La plus intuitive si vous avez déjà touché à d'autres langages de programmation est l'utilisation du mot clé <b>return</b>. Il permet de sortir de la fonction <b>immédiatement</b>,
        utile dans un <b>if</b> ou une boucle pour sortir avant la fin.
        </p>
        <pre>
fn carre(x: i32) -> i32 {
    return x * x;   // => on retourne x²
}</pre>
        <p>
        Le <b>retour implicite</b> est simple d'utilisation : si La <b>dernière expression</b> du bloc n'a pas de point-virgule, elle est automatiquement retournée :
        </p>
        <pre>
fn carre(x: i32) -> i32 {
    x * x   // pas de ';' => on retourne x²
}</pre>
        <p>
        On peut aussi utiliser les deux dans le même bloc de fonction :
        </p>
        <pre>
fn valeur_absolue(x: i32) -> i32 {
    if x < 0 {
        return -x;  // sortie immédiate
    }
    x   // retour implicite si on arrive ici
}</pre>
        <p>
        Attention : ajouter un '<b>;</b>' après la dernière expression change
        son sens. Avec un '<b>;</b>', ce n'est plus une expression mais une
        <b>instruction</b>, qui ne retourne rien (<b>()</b>) :
        </p>
        <pre>
fn carre(x: i32) -> i32 {
    x * x;
// erreur ... : la fonction ne retourne rien alors
// qu'elle doit retourner un i32.
}</pre>

        <h4>Appeler une fonction</h4>
        <p>
        On appelle une fonction par son nom suivi des arguments entre parenthèses,
        dans le même ordre que les paramètres déclarés :
        </p>
        <pre>
fn addition(x: i32, y: i32) -> i32 {
    x + y
}

fn main() {
    let resultat = addition(3, 5);
    println!("{}", resultat); // affiche 8
}</pre><br>
"""
        Exercice = [
        """
        <h4>Exercice :</h4>
        <p>
        Écrivez une fonction <b>multiplication</b> qui prend deux arguments
        <b>a</b> et <b>b</b> de type <b>i32</b>, et retourne leur produit
        (en utilisant le retour implicite, sans <b>return</b>).
        Appelez cette fonction dans <b>main</b> avec les valeurs 6 et 7,
        puis affichez le résultat avec <b>println!</b>.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Créez une fonction <b>afficher</b> qui prend un caractère <b>car</b>
        en argument. La fonction devra afficher <b>Car</b>.
        Appelez cette fonction depuis le <b>main</b> avec le caractère <b>'O'</b>.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Faites une fonction <b>est_pair</b> qui prend un entier '<b>nb</b>' en argument et renvoie un booléen.
        Cette fonction regarde si 'nb modulo 2 est nul'. Elle renvoie «true» si tel est le cas et «false» sinon.
        Appelez cette fonction dans <b>main</b> avec le chiffre <b>7</b> puis afficher son résultat. Vous devrez voir «false» affiché.
        </p>
        """
        ]

        question += Exercice[self.version]
        return question

    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        if self.version == 0:
            block_mult = extract_struct(source, "fn multiplication(", '(', ')')

            self.message(
                'fnmultiplication(' in canoniseALL(source),
                "Une fonction «multiplication» est déclarée."
            )
            self.message(
                'a:i32,b:i32' in canoniseALL(block_mult),
                "Les arguments 'a' et 'b' sont de type i32."
            )
            self.message(
                ')->i32' in canoniseALL(source),
                "La fonction retourne bien un i32."
            )
            # Vérifie qu'il n'y a pas de 'return' (retour implicite attendu)
            found_return = False
            for line in source.split('\n'):
                if 'fn multiplication' in line:
                    body_mult = extract_struct(source,"fn multiplication(")
                    if 'return' in body_mult:
                        found_return = True

            self.message(
                not found_return,
                "Le retour implicite est utilisé (pas de «return»)."
            )
            self.message(
                'multiplication(6, 7)' in source or 'multiplication(6,7)' in source,
                "La fonction est appelée avec 6 et 7."
            )
            self.message(
                result.strip() == '42',
                "Le résultat affiché est correct (42)."
            )

        if self.version == 1:
            main_struct = extract_struct(source,"fn main()")

            self.message(
                'fn afficher(' in source,
                'Une fonction <b>afficher</b> est déclarée.'
            )
            self.message(
                'fn afficher(car: char)' in source or 'fn afficher (car: char)' in source or
                'fn afficher(car : char)' in source or 'fn afficher (car : char)' in source,
                "La fonction prend bien un paramètre '<b>car</b>' de type <b>char</b>."
            )
            self.message(
                "afficher('O')" in canoniseALLNotLower(main_struct),
                "La fonction est appelée avec le caractère 'O' depuis le main()."
            )

        if self.version == 2:
            est_pair_struct = extract_struct(source, "fn est_pair(")
            main_struct = extract_struct(source, "fn main()")
            self.display(est_pair_struct)
            self.message(
                "return" not in canoniseALLNotLower(est_pair_struct),
                "Aucun return n'est utilisé dans la fonction 'est_pair(...)', on fait bien un retour implicite."
            )
            self.message(
                "if" in canoniseALLNotLower(est_pair_struct) and "else" in canoniseALLNotLower(est_pair_struct),
                "if/else sont bien utilisés dans la fonction 'est_pair(...)'"
            )
            self.message(
                "ifnb%2==0" in canoniseALLNotLower(est_pair_struct),
                "Le test de parité '<b>nb % 2 == 0</b>' est utilisé"
            )
            self.message(
                'est_pair(7)' in canoniseALLNotLower(main_struct),
                "'est_pair(...)' est appelé avec le chiffre 7 en argument"
            )
            expected="false"
            self.message(
                expected==result,
                "On affiche le booléen renvoyé par la fonction <b>est_pair</b> et le bon résultat est affiché."
            )

        if self.all_tests_are_fine:
            if self.round>=2 :
                self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                self.next_question()
                return
            else :
                self.next_question()
                self.display(self.new_round_button('Essayer une alternative'))
                return


    def default_answer(self):
        return """// Écriture de la fonction

// main() qui doit appeler la fonction
fn main(){

}
"""


class Q_Boucle(Question):
    """Les boucles loop et while"""
    answer = [1,2,3,4,5,6,7,8,9,10]
    def question(self):
        self.nb_version = 2
        self.version = self.random_version(2)
        question = """
        <h3>La boucle loop</h3>
        <p>
        <b>loop</b> crée une boucle infinie. On en sort avec <b>break</b> :
        </p>
        <pre>
let mut i = 0;

loop {
    // Instructions exécutées à chaque itération

    // Vérification de la condition d'arrêt
    if i == limite {
        break;
    }

    // Autres instructions si nécessaire
}</pre><br>

        <h3>La boucle while</h3>
        <p>
        <b>while</b> répète un bloc tant qu'une condition est vraie :
        </p>
        <pre>
while condition {
    // Instructions exécutées tant que la condition est vraie

    // Mise à jour des variables utilisées par la condition
}</pre>
        <p>
        Contrairement à <b>loop</b>, la condition d'arrêt est directement
        dans le <b>while</b>, pas besoin de <b>break</b>.
        </p>
        <p>
        En Rust, <b>while</b> est utilisé lorsque l'on connaît la condition qui doit maintenir la boucle active :
        la boucle continue tant qu'une expression est vraie. À l'inverse, <b>loop</b> permet de créer une
        boucle qui s'exécute indéfiniment jusqu'à ce qu'une instruction <b>break</b> indique explicitement
        le moment de sortir. On utilise donc généralement <b>while</b> pour des répétitions contrôlées par
        une condition simple, et <b>loop</b> lorsque la sortie dépend d'un événement ou de plusieurs
        conditions possibles.
        </p>
        """

        Exercice = [
        """
        <h4>Exercice :</h4>
        <p>
        Créez une fonction <b>boucle_loop</b> qui prend un paramètre
        <b>limite: i32</b> et affiche, avec une boucle <b>loop</b>,
        tous les nombres de <b>1</b> jusqu'à <b>limite</b> (inclus).
        Dans <b>main</b>, vous appelerez boucle_loop(5) pour voir le résultat.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Créez une fonction <b>boucle_while</b> qui prend un paramètre
        <b>limite: i32</b> et affiche, avec une boucle <b>while</b>,
        tous les nombres de <b>1</b> jusqu'à <b>limite</b> (inclus).
        Dans <b>main</b>, vous appelerez boucle_while(5) pour voir le résultat.
        </p>
        """
        ]
        question += Exercice[self.version]
        return question
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        main_struct = extract_struct(source, "fn main()")

        if self.version == 0 :
            boucle_loop_struct = extract_struct(source, "fn boucle_loop(")
            if_in_loop = extract_struct(boucle_loop_struct, "if")

            self.message(
                "fnboucle_loop(limite:i32){" in canoniseALLNotLower(source),
                "La fonction <b>boucle_loop</b> est bien déclarée avec le bon argument"
            )
            self.message(
                "loop{" in canoniseALLNotLower(boucle_loop_struct),
                "<b>loop</b> est utilisé dans la fonction que nous avons créée."
            )
            is_if = False
            for line in source.split('\n'):
                if 'if' in canoniseALLNotLower(line) and "==limite" in canoniseALLNotLower(line):
                    is_if = True
            self.message(
                is_if,
                "La condition d'arrêt de la boucle <b>loop</b> utilise le paramètre <b>limite</b> comme attendu."
            )
            self.message(
                "break" in canoniseALLNotLower(if_in_loop),
                "On met fin à la boucle loop quand le cas d'arrêt est vérifié avec <b>break</b>."
            )
            self.message(
                "boucle_loop(5)" in canoniseALLNotLower(main_struct),
                "On appelle <b>boucle_loop</b> avec pour argument <b>limite</b> = 5 dans la fonction <b>main</b>."
            )

        if self.version == 1 :
            boucle_while_struct = extract_struct(source, "fn boucle_while(")

            self.message(
                "fnboucle_while(limite:i32){" in canoniseALLNotLower(source),
                "La fonction <b>boucle_while</b> est bien déclarée avec le bon argument"
            )
            self.message(
                "while" in canoniseALLNotLower(boucle_while_struct),
                "<b>while</b> est utilisé dans la fonction que nous avons créée."
            )
            end_while = False
            for line in source.split('\n'):
                if 'while' in canoniseALLNotLower(line) and ("<limite" in canoniseALLNotLower(line) or "<=limite" in canoniseALLNotLower(line)):
                    end_while = True
            self.message(
                end_while,
                "La condition d'arrêt de la boucle while utilise bien le paramètre <b>limite</b>."
            )
            self.message(
                "boucle_while(5)" in canoniseALLNotLower(main_struct),
                "On appelle <b>boucle_while</b> avec pour argument <b>limite</b> = 5 dans la fonction <b>main</b>."
            )

        expected="1\n2\n3\n4\n5"
        self.message(
            expected==result,
            "On obtient le bon affichage/résultat"
        )
        if self.all_tests_are_fine:
            self.display('<p style="background:#8F8">' + "Vous avez bien respectés les conditions.")
            if self.round>=1 :
                self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                self.next_question()
                return
            else :
                self.next_question()
                self.display(self.new_round_button('Essayer une alternative'))
                return
    def default_answer(self):
        return """fn main() {

}
"""


class Q_tableaux(Question):
    """Les tableaux"""
    elem0=0
    elem1=1
    elem2=2
    answer =[]
    def question(self):
        self.elem0 = self.random_version(51)
        self.elem1 = self.random_version(51)
        self.elem2 = self.random_version(51)
        self.answer=[self.elem0,self.elem1,self.elem2]
        self.version=self.random_version(2)
        question = """
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
        <p>
        Par défaut, un tableau est <b>immuable</b> : on ne peut pas changer
        ses éléments après sa création. Pour pouvoir le modifier, il faut
        le déclarer avec le mot-clé <b>mut</b> :
        </p>
        <pre>
let mut notes: [i32; 3] = [12, 15, 18];</pre>
        <p>
        Une fois le tableau déclaré <code>mut</code>, on peut modifier un
        élément en accédant à son <b>index</b> (les index commencent à 0) :
        </p>
        <pre>
let mut notes: [i32; 3] = [12, 15, 18];
notes[1] = 20; // on remplace 15 par 20
// notes vaut maintenant [12, 20, 18]</pre>
"""
        Exercice = [
        """
        <h4>Exercice :</h4>
        <p>
        Dans un premier temps vous déclarerez un tableau dynamique <b>tab</b> de 3 entiers qui ont pour valeurs <b>0</b>.<br>
        Ensuite vous remplacerez une à une les valeurs de ce tableaux par les valeurs """ + str(self.elem0) + ", " + str(self.elem1) + " et " + str(self.elem2) + """.<br>\
        Enfin, vou afficherez chaque élément de ce tableau sur une seule et même ligne.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <p>
        Dans un premier temps vous déclarerez un tableau dynamique <b>tab</b> de 3 entiers qui ont pour valeurs <b>0</b>.<br>
        Vous remplacerez le premier élément du tableau par : """ + str(self.elem0) +""".<br>
        Le second élément aura pour valeur : <b>tab[0] multiplié par 2</b>.<br>
        Le troisième élément sera : <b>tab[1] multiplié par 3</b>.<br>
        Enfin, vou afficherez chaque élément de ce tableau sur une seule et même ligne.
        </p>
        """
        ]
        question += Exercice[self.version]
        return question
    def tester(self):
        source = self.worker.source
        result = self.worker.execution_result.strip()
        expected = str(self.elem0) + str(self.elem1) + str(self.elem2)
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        if self.version == 0:

            self.message(
                'letmuttab:[i32;3]=[0,0,0]' in canoniseALLNotLower(source),
                "On a un tableau dynamique '<b>tab</b>' de taille 3 initialisé avec 3 entier à 0"
            )
            self.message(
                'tab[0]=' in source or 'tab[0] =' in source,
                "On modifie le premier élément de 'tab'"
            )
            self.message(
                'tab[1]=' in source or 'tab[1] =' in source,
                "On modifie le deuxième élément de 'tab'"
            )
            self.message(
                'tab[2]=' in source or 'tab[2] =' in source,
                "On modifie le troisième élément de 'tab'"
            )
            count_println=0
            found = False
            for line in source.split('\n'):
                if 'println!' in line :
                    count_println += 1
                if 'println!' in line and 'tab[0]' in line and 'tab[1]' in line and 'tab[2]' in line:
                    found = True
            self.message(
                found,
                'les 3 éléments de tab sont affichés ensemble dans un println!.'
            )
            if count_println > 1:
                        self.display('<p style="background:#F88">'
                                + 'Essayer avec un seul println!(), vous pouvez le faire !!!')

        if self.version == 1:

            self.message(
                'letmuttab:[i32;3]=[0,0,0]' in canoniseALLNotLower(source),
                "On a un tableau dynamique '<b>tab</b>' de taille 3 initialisé avec 3 entier à 0"
            )
            self.message(
                'tab[0]='+str(self.elem0)+';' in canoniseALLNotLower(source),
                "On modifie le premier élément de 'tab' en y insérant "+str(self.elem0)+"."
            )
            self.message(
                'tab[1]=tab[0]*2;' in canoniseALLNotLower(source) or 'tab[1]=2*tab[0];' in canoniseALLNotLower(source),
                "On modifie le second élément de 'tab' en y insérant le double du premier élément."
            )
            self.message(
                'tab[2]=tab[1]*3;' in canoniseALLNotLower(source) or 'tab[2]=3*tab[1];' in canoniseALLNotLower(source),
                "On modifie le troisième élément de 'tab' en y insérant le triple du second élément"
            )
            count_println=0
            found = False
            for line in source.split('\n'):
                if 'println!' in line :
                    count_println += 1
                if 'println!' in line and 'tab[0]' in line and 'tab[1]' in line and 'tab[2]' in line:
                    found = True
            self.message(
                found,
                'les 3 éléments de tab sont affichés ensemble dans un println!.'
            )
            if count_println > 1:
                self.display('<p style="background:#F88">'+ 'Essayer avec un seul println!(), vous pouvez le faire !!!')
        if self.all_tests_are_fine:
            if self.round>=1 :
                self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                self.next_question()
                return
            else :
                self.next_question()
                self.display(self.new_round_button('Essayer une alternative'))
                return
    def default_answer(self):
        return """fn main() {

}
"""


class Q_tableaux_boucles(Question):
    """Les tableaux et des boucles"""
    def question(self):
        return """
        <h4>La boucle for</h4>
        <p>
        Pour parcourir un tableau, on utilise une boucle <b>for</b>.
        Avec <b>&amp;</b> on passe une référence du tableau : la fonction le voit mais ne le prend pas, donc le tableau n’est pas perdu après l’appel. :
        </p><pre>
for element in &amp;notes {
    println!("{}", element);
}</pre>
        <p>
        Ce code afficherait :
        </p>
        <pre>
12
15
18</pre>
        <h4>Remplir un tableau avec une boucle for</h4>
        <p>
        On peut aussi utiliser une boucle <b>for</b> pour remplir un tableau avec des saisies clavier.
        </p>
        <p>
        Dans ce cas, on parcourt les indices du tableau grâce à <b>tab.len()</b> :
        </p>
        <pre>
for i in 0..tab.len() {
    ...
}</pre>
        <p>
        Cela permet de remplir chaque case du tableau une par une.
        </p>

        <h4>Exercice :</h4>
        <p>
        On veut insérer autant de valeur que possible dans le tableau !<br>
        Pour cela utilisez la boucle for et insérez à chaque indice la valeur 21.<br>
        Ensuite on veut afficher tous les éléments de ce tableau, toujours avec une boucle for.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        found_for_indice = False
        found_for_tab = False
        found_print = False
        found_insert_tab = False
        for line in source.split('\n'):
            if 'for' in line and '0..tab.len()' in line:
                found_for_indice = True
            if 'tab[' in canoniseALL(line) and ']=' in canoniseALL(line):
                found_insert_tab = True
            if 'for' in line and ('in tab' in line or 'in &tab' in line):
                found_for_tab = True
            if 'println!("{}",' in canoniseALL(line) :
                found_print = True
        self.message(
            found_for_indice,
            "Un indice parcours bel et bien l'ensemble du tableau"
        )
        self.message(
            found_insert_tab,
            "On insère les élément saisis au clavier dans le tableau"
        )
        self.message(
            found_for_tab,
            "On parcours tous les éléments du tableau"
        )
        self.message(
            found_print,
            "On affiche uniquement les éléments du tableau"
        )
        if self.all_tests_are_fine:
            if canoniseALLNotLower(result) == "2121212121":
                self.display('<p style="background:#8F8">' + "Bravo !")
                self.next_question()
                return
            else:
                self.display('<p style="background:#F88">' + "Ce n'est pas les bonne valeurs qui sont affichées.")
                return
        else:
            self.display('<p style="background:#F88">' + "Ce n'est pas ce qui est demandé.")
            return
    def default_answer(self):
        return """use std::io;
fn main() {
    let mut tab: [i32; 5] = [0, 0, 0, 0, 0];
    for i in ??? {
        let mut input = String::new();
        io::stdin().read_line(&mut input).expect("ERREUR");
        tab[???] = ???;
    }
    for ??? {
        println!("{}", ???);
    }
}
"""


class Q_vec(Question):
    """Tableaux dynamiques : vecteur"""
    def question(self):
        return """
        <h3>La macro vec! en Rust</h3>

        <p>
        En Rust, <b>vec!</b> est une <b>macro</b>.
        Comme toutes les macros en Rust, elle se reconnaît grâce au <b>!</b> à la fin de son nom.
        </p>
        <p>
        La macro <b>vec!</b> permet de créer un <b>vecteur</b>, c'est-à-dire un tableau dynamique.
        Contrairement à un tableau classique de type <b>[i32; 5]</b>, un vecteur peut grandir ou rétrécir pendant l'exécution du programme.
        </p>
        <h4>Créer un vecteur avec vec!</h4>
        <pre>
let nombres = vec![1, 2, 3, 4, 5];</pre>
        <p>
        Ici, on crée un vecteur contenant directement des valeurs.
        C'est la manière la plus simple d'initialiser un vecteur.
        </p>
        <h4>Vecteur vide</h4>
        <p>
        On peut aussi créer un vecteur vide, mais dans ce cas il doit être déclaré avec <b>mut</b>
        si on veut pouvoir le modifier.<br>
        On peut vouloir notifier le type à l'avance. Dans ce cas le type est : <b>Vec&lt;type&gt;</b>.<br>
        Si on ne précise pas le type, Rust va inférer le type à la première utilisation du tableau. Tant que rien n'est ajouté, Rust ne peut pas savoir le type, donc cette ligne seule provoquerait une erreur de compilation si le vecteur n'est jamais utilisé après.
        </p>
        <pre>
let mut nombres: Vec&lt;i32&gt; = vec![];

let mut nombres = vec![];</pre>

        <h4>Ajouter des éléments dans un vec!</h4>
        <p>
        La méthode <b>push()</b> permet d'ajouter un élément à la fin du vecteur.<br>
        Nous n'avons pas encore vu ce qu'est une méthode, mais pour que vous compreniez, c'est une fonction qui s'appelle sur un une variable avec un «.». Nous les verrons prochainement
        </p>
        <pre>
let mut nombres = vec![];

nombres.push(10);
nombres.push(20);
nombres.push(30);</pre>
        <p>
        Notez le <b>mut</b> : comme pour un vecteur vide (<code>let mut v = vec![];</code>),
        il est obligatoire dès qu'on veut modifier un vecteur, car les variables sont immuables par défaut en Rust.
        </p>
        <p>
        Il existe de nombreuses autres méthodes sur les vecteurs (suppression, taille, tri...) que nous verrons
        dans certaines autres questions. Toutes les méthodes disponibles sont référencées dans
        <a href="https://doc.rust-lang.org/std/vec/struct.Vec.html">la documentation officielle de Vec</a>.
        </p>

        <h4>Accéder aux éléments</h4>
        <pre>
let nombres = vec![10, 20, 30];

println!("{}", nombres[0]); // 10</pre>
        <p>
        On peut accéder aux éléments avec des crochets <b>[ ]</b>, comme un tableau classique.
        </p>

        <h4>Passer un tableau en paramètre d'une fonction</h4>
        <p>
        Pour passer un vecteur en paramètre à une fonction, on précise son type avec
        <b>Vec&lt;type&gt;</b>, où <b>type</b> est le type des éléments qu'il contient :
        </p>
        <pre>
fn add_char_tab(mut tab: Vec&lt;char&gt;) -> Vec&lt;char&gt; {
    // corps de la fonction
    tab
}</pre>
        <p>
        Le mot-clé <b>mut</b> avant <b>tab</b> permet de modifier le vecteur
        <b>à l'intérieur de la fonction</b> (ajouter, retirer des éléments...).
        Ici, la fonction devient <b>propriétaire</b> du vecteur passé en argument
        (il est déplacé), c'est pourquoi on le <b>retourne</b> à la fin pour
        pouvoir continuer à l'utiliser après l'appel.
        </p>

        <h4>Exercice :</h4>
        <p>
        Déclarez une fonction <b>remplir_tab</b> prenant comme argument un tableau dynamique d'entiers nommé <b>tab</b>. Cette fonction va ajouter 5 nouveaux chiffres (1, 2, 3, 4, 5) après le dernier élément du tableau.<br>
        Ensuite déclarez une fonction <b>afficher_tab</b> qui va afficher tous les éléments d'un tableau <b>tab</b> passé en paramètre en utilisant <b>print!()</b> et non <b>println!()</b>.<br>
        Enfin dans un <b>main</b> vous appelerez la fonction <b>remplir_tab</b> avec pour argument un tableau nommé «tab» que vous aurez préalablement initialisé comme vide. Le résultat sera stocké puis affiché avec la fonction <b>afficher_tab</b>.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        main_struct = extract_struct(source, "fn main()")
        remplir_tab_struct = extract_struct(source, "fn remplir_tab(")
        afficher_tab_struct = extract_struct(source, "fn afficher_tab(")

        self.message(
            'fnremplir_tab(muttab:Vec<i32>)->Vec<i32>{' in canoniseALLNotLower(source),
            "La fonction <b>remplir_tab</b> est bien déclarée."
        )
        is_for1 = False
        for line in remplir_tab_struct.split('\n'):
            if 'for' in canoniseALLNotLower(line) and "in" in canoniseALLNotLower(line):
                is_for1 = True
        self.message(
            is_for1,
            "Une boucle <b>for</b> est utilisée pour remplir le tableau."
        )
        self.message(
            '.push(' in canoniseALLNotLower(remplir_tab_struct),
            "Les éléments sont ajoutés au tableau avec la méthode <b>push()</b>."
        )
        self.message(
            'fnafficher_tab(tab:Vec<i32>){' in canoniseALLNotLower(source),
            "remplir_tab déclarée correctement"
        )
        is_print = False
        is_for2 = False
        for line in afficher_tab_struct.split('\n'):
            if 'print!(' in line and "{}" in line:
                is_print = True
            if 'for' in line and "in" in line:
                is_for2 = True
        self.message(
            is_for2,
            "On parcours le tableau avec une boucle <b>for</b> dans la fonction <b>afficher_tab</b>"
        )
        self.message(
            is_print,
            "Les éléments du tableau sont affichés avec la fonction <b>print!()</b>."
        )
        self.message(
            'remplir_tab(tab)' in main_struct,
            "On rempli le tableau 'tab' dans le <b>main</b> avec la fonction qu'on a créée"
        )
        self.message(
            'afficher_tab(' in main_struct,
            "On affiche le tableau 'tab' dans le <b>main</b> avec la fonction qu'on a créée"
        )
        self.message(
            canoniseALLNotLower(result)=="12345",
            "Le résultat de l'éxecution est le résultat attendu"
        )
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """fn main() {

}
"""

# fn remplir_tab(mut tab: Vec<i32>) -> Vec<i32> {
#     for i in 1..=5 {
#         tab.push(i);
#     }
#     tab
# }

# fn afficher_tab(tab: Vec<i32>) {
#     for element in tab {
#         print!("{} ", element);
#     }
# }

# fn main() {
#     let tab: Vec<i32> = vec![];

#     let tab = remplir_tab(tab);

#     afficher_tab(tab);
# }


class Q_pattern_matching(Question):
    """Le pattern matching avec match"""
    note = 0
    def question(self):
        self.note = self.random_version(21)
        return """
        <h3>Le pattern matching en Rust</h3>
        <p>
        En Rust, <b>match</b> est une structure de contrôle puissante qui permet
        de comparer une valeur à plusieurs cas possibles — comme un <b>switch</b>
        en C, mais bien plus expressif.
        </p>
        <pre>
match valeur {
    1 => println!("un"),
    2 => println!("deux"),
    3 | 4 => println!("trois ou quatre"),
    5..=10 => println!("entre 5 et 10"),
    _ => println!("autre chose"),  // cas par défaut
}</pre>

        <p>
        <b>match</b> fonctionne avec n'importe quel type : entiers, chaînes de caractères, booléens,
        tuples, et bien d'autres. La seule contrainte est que la valeur comparée et les cas
        doivent être du <b>même type</b> :
        </p>
        <pre>
// ici c'est une chaine de caractère
match prenom {
    "Alice" => println!("Bonjour Alice !"),
    "Bob"   => println!("Bonjour Bob !"),
    _       => println!("Bonjour inconnu !"),
}

// ici c'est un tuple
match (x, y) {
    (0, 0) => println!("origine"),
    (0, _) => println!("sur l'axe Y"),
    (_, 0) => println!("sur l'axe X"),
    _      => println!("ailleurs"),
}</pre>
        <p>
        Points clés :
        <ul>
            <li><b>=&gt;</b> sépare le motif de l'action à effectuer</li>
            <li><b>|</b> permet de matcher plusieurs valeurs à la fois</li>
            <li><b>..=</b> définit un intervalle inclusif</li>
            <li><b>_</b> est le cas par défaut — il capture tout ce qui n'a pas été matché</li>
            <li>Tous les cas possibles doivent être couverts — Rust vérifie ça à la compilation</li>
        </ul>
        </p>

        <h4>Exercice :</h4>
        <p>
        Déclarez une variable <b>note</b> de type <b>i32</b> valant <b>""" + str(self.note) + """</b>.
        En utilisant <b>match</b>, affichez :
        <ul>
            <li><b>"Excellent"</b> si la note est entre 16 et 20</li>
            <li><b>"Bien"</b> si la note est entre 12 et 15</li>
            <li><b>"Passable"</b> si la note est entre 10 et 11</li>
            <li><b>"Insuffisant"</b> si la note est inférieure à 10</li>
        </ul>
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source

        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        self.message(
            'match' in source,
            '«match» est utilisé.'
        )
        self.message(
            '_=>' in source or '_ =>' in source,
            'Le cas par défaut a été défini.'
        )
        count_cases_in_match = len(source.split('=> println!("')) - 1 + len(source.split('=>println!("')) - 1
        self.message(
            count_cases_in_match == 5,
            'Tous les cas sont définis.'
        )

        expected = ''
        if self.note >= 16:
            expected = 'Excellent'
        elif self.note >= 12:
            expected = 'Bien'
        elif self.note >= 10:
            expected = 'Passable'
        else:
            expected = 'Insuffisant'

        self.message(
            result == expected,
            'Le bon résultat est affiché pour la note ' + str(self.note) + '.'
        )
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """fn main() {
    let note: i32 = 11;
    match // A compléter

}
"""


class Q_if_let_while_let(Question):
    """If let / While let"""
    def question(self):
        self.values = []
        i = 0
        while i < 5:
            self.values.append(self.random_version(100))
            i += 1
        return """
        <h3>if let et while let</h3>
        <h4>Option : Some et None</h4>
        <p>
        En Rust, certaines opérations peuvent ne pas avoir de résultat (vecteur vide,
        fin d'une liste...). Plutôt que de retourner une valeur invalide, Rust utilise
        le type <b>Option</b> qui a deux variantes :
        <ul>
            <li><b>Some(x)</b> : il y a une valeur, et elle vaut <b>x</b></li>
            <li><b>None</b> : il n'y a pas de valeur</li>
        </ul>
        Par exemple, <b>pop()</b> sur un vecteur retourne <b>Some(valeur)</b>
        s'il reste des éléments, ou <b>None</b> si le vecteur est vide.
        C'est ce qui empêche les erreurs du type "accès à un élément qui n'existe pas".
        </p>
        <h4>if let</h4>
        <p>
        Pour traiter un <b>Option</b>, on peut utiliser <b>match</b> :
        </p>
        <pre>
match valeur {
    Some(x) => println!("j'ai {}", x),
    _ => {}
}</pre>
        <p>
        <b>if let</b> est un raccourci quand on ne veut tester qu'un seul cas.
        Le <b>=</b> ici n'est pas une comparaison : c'est une tentative de
        <b>déstructuration</b> — si <b>valeur</b> correspond au motif <b>Some(x)</b>,
        alors <b>x</b> reçoit la valeur contenue, et le bloc s'exécute :
        </p>
        <pre>
if let Some(x) = valeur {
    println!("j'ai {}", x);
}</pre>
        <h4>while let</h4>
        <p>
        <b>while let</b> fonctionne de la même façon mais en boucle :
        il répète le bloc tant que le motif est vérifié.
        </p>
        <pre>
let mut pile = vec![1, 2, 3];
while let Some(sommet) = pile.pop() {
    println!("{}", sommet);
}
// affiche 3, puis 2, puis 1</pre>
        <p>
        <b>while let</b> s'arrête automatiquement quand <b>pop()</b> retourne <b>None</b>
        (vecteur vide). C'est l'équivalent d'un <b>for</b> qui parcourt le vecteur,
        mais en retirant les éléments un par un depuis la fin.
        </p>
        <h4>Itérateur et next()</h4>
        <p>
        Pour parcourir un vecteur <b>sans le modifier</b> (dans l'ordre, depuis le début),
        on peut créer un <b>itérateur</b> avec <b>.iter()</b>. C'est l'équivalent
        de ce que fait un <b>for</b> en coulisses :
        </p>
        <pre>
let mut curseur = nombres.iter();
// curseur.next() avance d'un élément et retourne
// Some(&valeur) ou alors None s'il n'en reste plus</pre>
        <p>
        Chaque appel à <b>curseur.next()</b> consomme l'élément courant et passe
        au suivant — on ne peut pas revenir en arrière.
        </p>
        <h4>Exercice :</h4>
        <p>
        Créez un vecteur <b>nombres</b> contenant les valeurs
        <b>""" + ", ".join(map(str, self.values)) + """</b>.
        En utilisant <b>while let</b> et <b>next()</b>, affichez chaque
        élément sur une ligne séparée, dans l'ordre (comme le ferait un <b>for</b>).
        </p>
        <pre>
let mut curseur = nombres.iter();
while let Some(val) = curseur.next() {
    // à compléter
}</pre>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source

        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        self.message(
            'while let' in source,
            '«while let» est utilisé.'
        )
        self.message(
            'next()' in source,
            '«next()» est utilisé pour retirer les éléments.'
        )
        self.message(
            'Some' in source,
            '«Some» est utilisé pour le pattern matching.'
        )
        expected = "\n".join([str(v) for v in self.values])
        self.message(
            result == expected,
            'Les valeurs sont affichées dans le bon ordre.'
        )
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """fn main() {
    let nombres = vec![???];
    let mut curseur = nombres.iter();

    while let ???{
        println!("{}", ???);
    }
}
"""


class Q_Ownership(Question):
    """L'ownership en Rust"""
    def question(self):
        self.version=self.random_version(3)
        question = """
        <h3>L'ownership (propriété)</h3>
        <p>
        En Rust, chaque donnée est associée à une seule variable à la fois. Cette variable en est le **propriétaire**. Lorsque cette variable disparaît (par exemple à la fin d'un bloc de code), Rust supprime automatiquement la donnée de la mémoire. Cela évite au programmeur d'avoir à libérer la mémoire lui-même.
        </p>

        <h4>Le déplacement (move)</h4>
        <p>
        Pour les types qui vivent sur le tas (comme <b>String</b>), affecter
        une variable à une autre <b>déplace</b> la propriété — l'ancienne
        variable devient invalide :
        </p>
        <pre>
let a = String::from("bonjour");
let b = a;              // 'a' est déplacé dans 'b'
println!("{}", a);
// erreur : 'a' n'est plus valide, il a été "move"</pre>
        <p>
        C'est différent d'un type simple comme <b>i32</b>, qui est
        <b>copié</b> automatiquement (il ne "vit" pas sur le tas) :
        </p>
        <pre>
let x = 5;
let y = x;           // x est copié, pas déplacé
println!("{}", x);   // OK, x est toujours valide</pre>

        <h4>Le clonage (clone)</h4>
        <p>
        Si on veut vraiment <b>dupliquer</b> une valeur sur le tas (et garder
        les deux variables valides), on utilise <b>.clone()</b> :
        </p>
        <pre>
let a = String::from("bonjour");
let b = a.clone();  // copie complète des données
println!("{}", a);  // OK, 'a' est toujours valide
println!("{}", b);  // OK aussi</pre>

        <h4>L'emprunt (borrowing) avec &</h4>
        <p>
        Plutôt que de déplacer une valeur, on peut la <b>prêter</b> temporairement
        avec <b>&</b> — la fonction ou le bloc qui reçoit la référence peut la lire,
        mais n'en devient pas propriétaire :
        </p>
        <pre>
fn est_vide(texte: &String) -> bool {
    texte.len() == 0
}
fn main() {
    let phrase = String::from("Bonjour");
    // on prête 'phrase' à la fonction :
    let vide = est_vide(&phrase);
    println!("{}", vide);    // affiche false
    println!("{}", phrase);  // 'phrase' valide
}</pre>

        <h4>L'emprunt mutable avec &mut</h4>
        <p>
        Pour prêter une valeur et pouvoir la <b>modifier</b>, on utilise
        <b>&mut</b>. La variable d'origine doit être déclarée <b>mut</b> :
        </p>
        <pre>
fn ajouter_bonjour(texte: &mut String) {
    texte.push_str(" bonjour");
}
fn main() {
    let mut a = String::from("salut");
    ajouter_bonjour(&mut a);
    println!("{}", a);  // affiche "salut bonjour"
}</pre>
        <p>
        Règle importante : Rust n'autorise <b>qu'un seul emprunt mutable à la fois</b>
        sur une même valeur (pas d'emprunt en lecture pendant qu'un autre modifie).
        C'est ce qui garantit qu'il n'y a jamais de conflit d'accès à la mémoire.
        </p>

        <p>
        <b>Remarque :</b><br>
        Il y a plusieurs versions alternatives qui traitent des différents éléments de l'ownership.
        N'hésitez pas à tester les autres exercices de ce thème !
        </p>
        """

        Exercice = [
        """
        <h4>Exercice :</h4>
        <h4>Clonage</h4>
        <p>
        Déclarez une variable <b>original</b> contenant la chaîne de caractères "Rust".
        Créez une copie indépendante nommée <b>copie</b> en utilisant <code>.clone()</code>.
        Affichez original et copie, pour montrer que les deux variables restent valides.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <h3>Emprunt</h3>
        <p>
        Créez une fonction <b>afficher_taille</b> qui prend un <b>&String</b> en paramètre et affiche sa longueur avec <code>.len()</code>. Dans 'main', déclarez une variable <b>mot</b> contenant "Bonjour", appelez afficher_taille en lui prêtant <b>mot</b> avec <b>&,</b> puis affichez à nouveau <b>mot</b> pour montrer qu'il est toujours valide après l'appel.
        </p>
        """
        ,
        """
        <h4>Exercice :</h4>
        <h3>Empreint mutable</h3>
        <p>
        Créez une fonction <b>ajouter_copie</b> qui prend une String nommé <b>texte</b> que nous allons modifier en paramètre (par valeur, donc elle en devient propriétaire). On lui ajoute ensuite " copie" avec <code>.push_str(" copie")</code> (oui l'espace est important !), puis retourne cette String modifiée.<br>Dans 'main', déclarez <b>original</b> contenant "Rust", appelez la fonction <code>ajouter_copie</code> avec en argument <b>original</b>, puis affichez uniquement le résultat de cet appel.<br>(Attention, vous ne pouvez plus afficher original, car il a été déplacé dans la fonction).
        </p>
        """
        ]
        question += Exercice[self.version]
        return question
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        main_struct = extract_struct(source, "fn main()")

        if self.version == 0 :

            self.message(
                'letoriginal=String::from("Rust");' in canoniseALLNotLower(main_struct),
                "Une variable 'original' contenant 'Rust' a bien été déclarée."
            )
            self.message(
                'letcopie=original.clone();' in canoniseALLNotLower(main_struct),
                "Une copie de 'original' a bien été stockée dans une nouvelle variabel 'copie'."
            )
            expected ="RustRust"
            self.message(
                canoniseALLNotLower(result) == expected,
                "Le résultat attendu est affiché !"
            )

        if self.version == 1 :

            afficher_taille_struct = extract_struct(source, "fn afficher_taille(")
            println_struct = extract_struct(afficher_taille_struct, "println!(", '(', ')')
            println_struct2 = extract_struct(main_struct, "println!(", '(', ')')

            self.message(
                'fnafficher_taille(texte:&String)' in canoniseALLNotLower(source),
                "La fonction 'afficher_taille' est déclarée avec la bonne signature."
            )
            self.message(
                'texte.len()' in println_struct,
                "La longueur du texte est affiché dans un println avec <code>.len()</code>"
            )
            self.message(
                'letmot=String::from("Bonjour");' in canoniseALLNotLower(main_struct),
                "'mot' a été initialisé correctement"
            )
            self.message(
                'afficher_taille(&mot)' in main_struct,
                "Appelez afficher_taille en lui prêtant mot avec '&'"
            )
            self.message(
                ',mot' in canoniseALLNotLower(println_struct2),
                "le contenu de la variable 'mot' est affiché"
            )
            expected = "7Bonjour"
            self.message(
                canoniseALLNotLower(result) == expected,
                "Le résultat attendu est affiché !"
            )


        if self.version == 2 :

            ajouter_copie_struct = extract_struct(source, "fn ajouter_copie(")

            self.message(
                'fnajouter_copie(muttexte:String)->String' in canoniseALLNotLower(source),
                "La fonction 'ajouter_copie' est déclarée avec la bonne signature et le bon type de retour."
            )
            self.message(
                'texte.push_str(" copie")' in ajouter_copie_struct,
                """On ajoute ' copie' au texte avec la méthode <code>.push_str(" copie")</code>."""
            )
            self.message(
                'letoriginal=String::from("Rust");' in canoniseALLNotLower(main_struct),
                "'original' est déclarée correctement."
            )
            self.message(
                'ajouter_copie(original)' in main_struct,
                "On utilise la fonction ajouter_copie() sur <b>original</b>."
            )
            expected = "Rust copie"
            self.message(
                result == expected,
                "Le résultat attendu est affiché !"
            )

        if self.all_tests_are_fine:
            if self.round>=2 :
                self.display('<p style="background:#CCF">' + "Il n'y a plus de versions alternatives !")
                self.next_question()
                return
            else :
                self.next_question()
                self.display(self.new_round_button('Essayer une alternative'))
                return

    def default_answer(self):
        return """fn main() {

}
"""

#Alt 1
# fn main() {
#     let original = String::from("Rust");
#     let copie = original.clone();
#     println!("{}", original);
#     println!("{}", copie);
# }

#Alt 2
# fn afficher_taille(texte: &String) {
#     println!("{}", texte.len());
# }

# fn main() {
#     let mot = String::from("Bonjour");
#     afficher_taille(&mot);
#     println!("{}", mot);
# }

#Alt 3
# fn ajouter_copie(mut texte: String) -> String {
#     texte.push_str(" copie");
#     texte
# }

# fn main() {
#     let original = String::from("Rust");
#     let resultat = ajouter_copie(original);
#     println!("{}", resultat);
# }


class Q_structures(Question):
    """Les structures (struct)"""
    nom = ''
    poids = 0
    def question(self):
        self.nom = "Pomme"
        self.poids = self.random_version(51) + 100
        return """
        <h3>Les structures en Rust</h3>
        <p>
        Une <b>struct</b> permet de regrouper plusieurs données sous un même type personnalisé.
        C'est l'équivalent d'un objet simple — comme une fiche qui regroupe plusieurs informations liées.
        </p>
        <pre>
struct Personne {
    nom: String,
    age: i32,
}</pre>
        <p>
        Chaque élément dans la struct s'appelle un <b>champ</b>. Ici, <b>Personne</b> a deux champs :
        <b>nom</b> de type <b>String</b> et <b>age</b> de type <b>i32</b>.
        </p>

        <h4>Créer une instance</h4>
        <p>
        La struct définit le <b>modèle</b> (le moule). Une <b>instance</b> est un exemplaire concret
        créé à partir de ce modèle, avec des valeurs réelles pour chaque champ :
        </p>
        <pre>
let p = Personne {
    nom: String::from("Alice"),
    age: 25,
};</pre>
        <p>
        On peut créer autant d'instances qu'on veut à partir du même modèle :
        </p>
        <pre>
let p1 = Personne {
    nom: String::from("Alice"),
    age: 25
};
let p2 = Personne {
    nom: String::from("Bob"),
    age: 30
};</pre>
        <p>
        On accède aux champs d'une instance avec le <b>.</b> :
        </p>
        <pre>
println!("{} a {} ans", p.nom, p.age);</pre>

        <h4>Modifier une instance</h4>
        <p>
        Pour modifier les champs d'une instance, elle doit être déclarée avec <b>mut</b> :
        </p>
        <pre>
let mut p = Personne {
    nom: String::from("Alice"),
    age: 25
};
p.age = 26; // OK</pre>

        <h4>Ajouter des méthodes avec impl</h4>
        <p>
        On peut associer des fonctions à une struct avec <b>impl</b>. Ces fonctions s'appellent
        des <b>méthodes</b> et s'utilisent avec le <b>.</b> sur une instance :
        </p>
        <pre>
impl Personne {
    fn saluer(&self) {
        println!("Bonjour, je suis {} et j'ai {}
        ans", self.nom, self.age);
    }
}
p.saluer();</pre>
        <p>
        <b>&self</b> est le premier paramètre de toute méthode — il représente l'instance sur laquelle
        on appelle la méthode. Il y a deux variantes :
        <ul>
            <li><b>&self</b> : accès en lecture seule aux champs, l'instance n'est pas modifiée</li>
            <li><b>&mut self</b> : accès en écriture, permet de modifier les champs</li>
        </ul>
        </p>
        <pre>
impl Personne {
    fn vieillir(&mut self) {
        self.age += 1; // modifie le champ age
    }
}
p.vieillir(); // p.age vaut maintenant 26</pre>

        <h4>Les fonctions associées</h4>
        <p>
        On peut aussi définir dans <b>impl</b> des fonctions qui ne prennent pas <b>&self</b>
        en paramètre. Elles s'appellent des <b>fonctions associées</b> et s'utilisent avec <b>::</b>
        au lieu du <b>.</b>. Elles servent souvent de constructeur :
        </p>
        <pre>
impl Personne {
    fn nouveau(nom: &str, age: i32) -> Personne {
        Personne {
            nom: String::from(nom),
            age,
        }
    }
}
let p = Personne::nouveau("Alice", 25);</pre>

        <h4>Exercice :</h4>
        <p>
        Créez une struct <b>Fruit</b> avec deux champs :
        <ul>
            <li><b>nom</b> de type <b>String</b></li>
            <li><b>poids</b> de type <b>i32</b></li>
        </ul>
        Ajoutez via <b>impl</b> une méthode <b>presentation</b> qui affiche :
        <pre>Ce fruit s'appelle : [nom] et pèse [poids] grammes.</pre>
        Créez une instance avec nom=<b>\"</b>""" + self.nom + """<b>\"</b>
        et poids=<b>""" + str(self.poids) + """</b>, puis appelez <b>presentation</b>.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )

        block_struct = extract_struct(source, "struct Fruit")
        block_print = extract_struct(source,"println!(", '(', ')')
        block_instance = extract_struct(source, "let f")

        self.message(
            'nom:string' in canoniseALL(block_struct) and 'poids:i32' in canoniseALL(block_struct),
            "Les éléments 'nom' et 'poids' sont bien définis avec leur bon type"
        )
        self.message(
            'self.nom' in canoniseALL(block_print) and 'self.poids' in canoniseALL(block_print),
            "Le nom et le poids du fruit sont affichés dans un seul et même print"
        )
        self.message(
            'nom:string::from("pomme"),' in canoniseALL(block_instance) and ('poids:' + str(self.poids) + ',') in canoniseALL(block_instance),
            "Une instance Pomme a bien été crée"
        )
        expected = canoniseALL("Ce fruit s'appelle : Pomme et pèse "+str(self.poids)+" grammes.")
        self.message(
            canoniseALL(result) == expected,
            "La bonne phrase est affiché."
        )
        if self.all_tests_are_fine:
            self.display('<p style="background:#8F8">' + 'Bravo !')
            self.next_question()
        else:
            self.display('<p style="background:#F88">' + "Ce n'est pas tout à fait ce qui est demandé !")

    def default_answer(self):
        return """struct Fruit {
    // À compléter
}

impl Fruit {
    fn presentation(&self) {
        // À compléter
    }
}

fn main() {
    let f = Fruit {
        // À compléter
    };
    f.presentation();
}
"""


class Q_input(Question):
    """La saisie clavier"""
    def question(self):
        return """
        <h3>Input</h3>
        <p>
        Pour avoir accès aux input/output en Rust, il faut utiliser le module io de la bibliothèque standard.
        On peut donc importer le module <b>io</b> de la bibliothèque standard : <b>use std::io;</b><br>
        Pour lire une saisie clavier il faut donc utiliser <code><b>std::io::stdin()</b></code>
        </p>
        <h4>Les méthodes, des fonctions particulières</h4>
        <p>
        Vous avez vu les <b>fonctions</b>, qu'on appelle directement par leur nom :
        <b>ma_fonction(argument)</b>. Il existe aussi des fonctions qu'on appelle
        <b>sur</b> une valeur, avec un point <b>.</b> : ce sont des <b>méthodes</b>.
        C'est justement le cas de <b>.read_line(...)</b> et <b>.expect(...)</b>
        que vous venez de voir : ce sont des méthodes appelées sur le résultat de
        <b>stdin()</b>.
        </p>
        <p>
        Une méthode fonctionne comme une fonction classique, sauf que la valeur
        sur laquelle elle est appelée (avant le point) lui est passée automatiquement
        en premier argument caché :
        </p>
        <p>
        Pour lire des saisies claviers, nous allons utiliser des méthodes sur une io::stdin. On a donc :<br>
        .read_line(&amp;mut input);</b> sert à lire jusqu'à ce que l'utilisateur presse la touche Entrée.<br>
        <b>.expect("Erreur");</b> permet de gérer les potentielles erreurs.
        </p>
        <p>
        On peut d'ailleurs <b>enchaîner</b> plusieurs méthodes à la suite avec
        plusieurs points, comme ci-dessous : chaque méthode retourne une valeur
        sur laquelle on peut rappeler une nouvelle méthode.
        </p>
<pre>
io::stdin()
    .read_line(&mut input)
    .expect("ERREUR");</pre>
        <h4>Pourquoi <b>String::new()</b> et pas <b>&amp;str</b> ?</h4>
        <p>
        Jusqu'ici vous avez souvent utilisé <b>&amp;str</b> pour stocker du texte, par exemple <code>let prenom: &amp;str = "Alice";</code>.
        Comme vous l'avez vu dans la question sur les modules, 'String:: ...' est utilisé pour les string modifiales
        Pour une saisie clavier, la valeur n'est connue qu'au moment de l'exécution : il faut donc
        une chaîne <b>dynamique</b> et <b>modifiable</b>.<br>
        <code>String::new()</code> crée une chaîne vide que <b>read_line</b> pourra remplir avec ce que tape l'utilisateur.
        </p>
        <p>
        Vous avez peut-être remarqué que <b>println!</b> fonctionne sans importer <b>io</b>.
        C'est parce que <b>println!</b> est une <b>macro</b> intégrée au <i>prélude</i> de Rust :
        un ensemble de fonctionnalités importées <b>automatiquement</b> dans tout programme Rust.
        En revanche, la lecture clavier via <b>stdin()</b> n'en fait pas partie,
        il faut donc l'importer explicitement avec <b>use std::io;</b>.
        </p>
        <pre>
let mut input = String::new();

io::stdin()
    .read_line(&amp;mut input)
    .expect("ERREUR");
//Ces lignes permettent d'avoir saisie clavier</pre>
        <p>
        Important :
        <ul>
            <li><code>read_line</code> stocke toujours une chaîne de caractères</li>
            <li>Pour stocker un entier, il faut le convertir <code>parse()</code></li>
        </ul>
        </p>
        <pre>
input.trim().parse().expect("Pas un entier");</pre>
        <p>
        - <b>trim()</b> enlève les retours à la ligne et les espaces en début et fin de chaîne<br>
        - <b>parse()</b> convertit en entier
        </p>

        <h4>Exercice :</h4>
        <p>
        Vous stockerez dans une variable le résultat d'une saisie clavier de contenant du texte. Vous vous occuperez aussi des potentielles erreurs. Ensuite vous afficherez uniquement le contenu de cette variable.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        self.message(
            'println!("{}", input);' in source or 'println!("{}",input);' in source,
            "On affiche uniquement le résultat de l'input"
        )
        if self.all_tests_are_fine:
            self.next_question()
    def default_answer(self):
        return """use std::io;
fn main() {
}
"""


class Q_Threads_Process(Question):
    """Threads"""
    def question(self):
        return """
        <h3>Les threads</h3>
        <p>
        Un <b>thread</b> permet d'exécuter du code <b>en parallèle</b> du
        programme principal, tout en partageant la même mémoire. En Rust,
        on crée un thread avec <b>std::thread::spawn</b>, qui prend une
        <b>closure</b> (une fonction anonyme) contenant le code à exécuter :
        </p>
        <pre>
use std::thread;

fn main() {
    let handle = thread::spawn(|| {
        // corps du thread
    });
    // reste du main
    handle.join().unwrap(); // attend la fin du thread
}</pre>
        <p>
        Points clés :
        <ul>
            <li><b>thread::spawn(...)</b> lance le thread et retourne
                immédiatement un <b>handle</b> (une "poignée" pour le suivre)</li>
            <li>Le code entre <b>|| { ... }</b> est une <b>closure</b> :
                une fonction sans nom, exécutée dans le nouveau thread</li>
            <li><b>.join()</b> attend que le thread se termine avant de continuer</li>
        </ul>
        </p>

        <h4>Exercice :</h4>
        <p>
        Créez un thread qui affiche
        <b>"Bonjour depuis le thread"</b>. Dans le programme principal,
        affichez <b>"Bonjour depuis le main"</b>. Utilisez <b>.join()</b>
        pour attendre la fin du thread.
        </p>
        """
    def tester(self):
        result = self.worker.execution_result.strip()
        source = self.worker.source
        self.display(
            "La zone en bas à droite contient :<pre>"
            + self.worker.escape(result)
            + "</pre>"
        )
        # No tester at the moment

        if self.all_tests_are_fine:
            self.display('<p style="background:#F88">No tester() at the moment')
            self.next_question()
            return
    def default_answer(self):
        return """use std::thread;

fn main() {

}

// Il n'y a que la partie thread pour l'instant.
// La partie processus est similaire et a besoin de
// use std::process::Command
"""














    # TITRE DE LA QUESTION  :                   THÈMES ABORDÉS  :
    # """Hello World et prise en main de C5"""  C5
    # """La fonction 'println!()'"""            Afficher avec Println!
    # """Les variables"""                       Déclarer/afficher une variable + préfixer une variable non utilisée
    # """Les conditions if/else"""              If /else if/ else
    # """Les variables mutables"""              Variable mutable + If/else
    # """Les fonctions"""                       Fonction + retour implicite + If/else
    # """Les boucles loop et while"""           While/loop + Fonction
    # """Les tableaux"""                        Tableaux + tableaux mutables + modifier une élément du tableau
    # """Les tableaux et des boucles"""         Boucle for + tableaux + input + modifier un élément du tableau
    # """Tableaux dynamiques : vecteur"""       vecteur (macro vec!) + modifs + fonctions (plusieurs en un code) + boucle for
    # """Le pattern matching avec match"""      match
    # """If let / While let"""                  if let/while let
    # """L'ownership en Rust"""                 Ownership + fonctions
    # """Les structures (struct)"""             Structures + instances + méthodes struct avec impl
    # """La saisie clavier"""                   Saisie clavier (à refaire peut-être, un peu brute de décoffrage)
    # """Threads et processus séparés"""        thread

    # il manque 2 questions sur thread/fork
