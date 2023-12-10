"""
Example for racket
"""

class Q1(Question): # pylint: disable=undefined-variable
    """Suite de Conway"""
    def question(self):
        """The question."""
        return """Modifiez le programme"""
    def tester(self):
        """Test the student answer."""
        self.check(self.worker.execution_result, [
            [r'[(]1[)]', '(1)'],
            [r'[(]1 1[)]', '(1 1)'],
            [r'[(]2 1[)]', '(2 1)'],
            [r'[(]1 2 1 1[)]', '(1 2 1 1)'],
            [r'[(]1 1 1 2 2 1[)]', '(1 1 1 2 2 1)'],
            [r'[(]3 1 2 2 1 1[)]', '(3 1 2 2 1 1)'],
        ])
        return 
    def default_answer(self):
        """The initial editor content."""
        return """
(define (ajoute nombre liste)
    (if (= (car (cdr liste)) nombre)
        (cons (+ (car liste) 1) (cdr liste))
        (cons 1 (cons nombre liste))
    )
)

(define (conway liste)
    (if
        (null? (cdr liste))
        (list 1 (car liste))
        (ajoute (car liste) (conway (cdr liste)))
    )
)

(define (block liste) "Done")

(define (suiteconway liste nr)
    (if (= nr 0)
        "C'est fini."
        (block
            (display liste)
            (display "\\n")
            (suiteconway (conway liste) (- nr 1))
        )
    )
)

(define (valeur_initiale)
    (display "Valeur initiale (1 par exemple)\\n")
    (read)
)

(suiteconway (list (valeur_initiale)) 10)

(display "C'est fini\\n")
"""
