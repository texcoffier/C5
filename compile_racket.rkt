#lang racket

(require racket/sandbox)

(define (compile-and-run filename)
    (
        (make-evaluator
            'racket
            '(define (error-handler exn) exn)                
            '(define (repl source ns)
                (let ( [ast (read-syntax "" source)] )
                    (if (eof-object? ast)
                        '()
                        (let ([result (with-handlers ([exn:fail? error-handler])
                                          (eval ast ns)
                                      )
                              ])
                              (if (exn:fail? result)
                                   (cons ast (cons result '()))
                                   (cons ast (cons result (repl source ns)))
                              )
                        )
                    )
                )
            )
            '(define (run source) (repl source (make-base-namespace)))
        )
        (list 'run (open-input-file filename))
    )
)

(define (show a-list)
   (if (null? a-list)
       '()
       (list
            (display "\001\002RACKET")
            (display (car a-list))
            (display "\n")
            (display (car (cdr a-list)))
            (display "\001")
            (show (cdr (cdr a-list))))
   )
)

(define (daemon)
    (show (compile-and-run (read-line)))
    (display "\001\002RACKETFini !\001")
    (flush-output)
    (daemon)
)

(daemon)