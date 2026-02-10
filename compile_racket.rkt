#lang racket
; A change in this file implies a server restart.

(require racket/sandbox)

(define (compile-and-run filename)
    (
        (parameterize (
                        [sandbox-eval-limits '(1 4)] ; seconds and megabytes
                        [sandbox-output (current-output-port)]
                      )
            (make-evaluator
                'racket
                '(define (error-handler exn) exn)
                '(define (repl source)
                    (let ( [ast (read-syntax "" source)] )
                        (if (eof-object? ast)
                            (close-input-port source)
                            (let ([result (with-handlers ([exn:fail? error-handler])
                                            (eval ast)
                                        )
                                ])
                                (display "\001\002RACKET")
                                (display ast)
                                (display "\n")
                                (flush-output)
                                (if (exn:fail? result)
                                    (list (display result) (display "\001"))
                                    (list (display result) (display "\001") (cons result (repl source)))
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

(define (error-handler exn) (display "\001\002RACKET") (display exn) (display "\001"))

(define (daemon)
    (with-handlers ([exn:fail? error-handler])
        (compile-and-run (read-line)))
    (display "\001\002RACKETFini !\001")
    (flush-output)
    ;(collect-garbage 'major)
    (daemon)
)

(daemon)