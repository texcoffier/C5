# The following options are used only when the session is created.
# One created, you must edit interactivly the session parameters.
COURSE_OPTIONS = {
            'title': 'Test Rust',
            'compiler': 'cargo',
            'state': 'Ready',
            'checkpoint': 0,
            'allow_copy_paste': 1,
            'expected_students': 'nobody',
            'positions' : {
                'question': [1, 28, 0, 30, '#EFE'],
                'tester': [1, 28, 30, 70, '#EFE'],
                'editor': [30, 40, 0, 100, '#FFF'],
                'compiler': [70, 30, 0, 30, '#EEF'],
                'executor': [70, 30, 30, 70, '#EEF'],
                'time': [80, 20, 98, 2, '#0000'],
                'index': [0, 1, 0, 100, '#0000'],
                }
            }
class Q1(Question):
    def question(self):
        return "Écriver un programme Rust qui affiche la somme de 2 entiers saisis au clavier avec 1 entier par ligne."
    def default_answer(self):
        return """
use std::io;

fn read_integer() -> i32 {
    let line = &mut String::new();
    io::stdin().read_line(line).expect("Failed to read");
    let i: i32 = line.trim().parse().expect("Not integer");
    i
}


fn main() {
    println!("Premier nombre :");
    let i = read_integer();

    println!("Deuxième nombre :");
    let j = read_integer();

    println!("{}+{}={}\n", i, j, i + j);
}
"""
    def expectations(self):
        def TRUE(infos)        : return True
        def premier_entier()   : return '666'
        def deuxieme_entier()  : return '-111'
        def args(txt)          : return '666+-111' in txt
        def resultat(txt)      : return '555' in txt
        def complet(txt)       : return '666+-111=555' in txt
        def flottant()         : return '3.14'
        def erreur_lecture(txt): return 'ParseIntError' in txt
        def exit_ok(infos)     : return '= 0' in infos[0]
        def exit_error(infos)  : return '= -' in infos[0]

        return [
            ['EXIT', "Première exécution terminée."          , TRUE],

            ['MSG' , "Teste l'addition de 2 entiers :"],
            ['IN'  , "Lecture première valeur."              , premier_entier],
            ['IN'  , "Lecture deuxième valeur."              , deuxieme_entier],
            ['OUT' , "Affichage des arguments."              , args],
            ['OUT' , "Affichage correcte du résultat."       , resultat],
            ['OUT' , "Affichage complet."                    , complet],
            ['EXIT', "Se termine sans erreur."               , exit_ok],

            ['MSG' , "Teste l'addition de flottants (doit échouer)."],
            ['IN'  , "Lecture première valeur."              , flottant],
            ['OUT' , "La lecture d'un flottant doit échouer.", erreur_lecture],
            ['EXIT', "Se termine en faisant une erreur."     , exit_error],
        ]
