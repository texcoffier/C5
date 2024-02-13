#lang racket

(require racket/sandbox)

(define (compile-and-run filename)
    (
        (parameterize ([sandbox-eval-limits '(1 4)]) ; seconds and megabytes
            (make-evaluator
                'racket
                '(define (error-handler exn) exn)
                '(define (repl source)
                    (let ( [ast (read-syntax "" source)] )
                        (if (eof-object? ast)
                            '()
                            (let ([result (with-handlers ([exn:fail? error-handler])
                                            (eval ast)
                                        )
                                ])
                                (if (exn:fail? result)
                                    (cons ast (cons result 'error))
                                    (cons ast (cons result (repl source)))
                                )
                            )
                        )
                    )
                )
                '(define (run source) (repl source))
            )
        )
        (list 'run (open-input-file filename))
    )
)

(define (show a-list)
   (if (null? a-list)
       '()
       (list
            (display "\001\002RACKET")
            (write (car a-list))
            (display "\n")
            (if (equal? 'error (cdr (cdr a-list)))
                (list
                    (display (car (cdr a-list)))
                    (display "\001")
                    )
                (list
                    (write (car (cdr a-list)))
                    (display "\001")
                    (show (cdr (cdr a-list)))
                    )
                )
            )
   )
)

(define (error-handler exn) (display "\001\002RACKET") (display exn) (display "\001"))

(define (daemon)
    (with-handlers ([exn:fail? error-handler])
        (show (compile-and-run (read-line))))
    (display "\001\002RACKETFini !\001")
    (flush-output)
    (collect-garbage 'major)
    (daemon)
)

(daemon)