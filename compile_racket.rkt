#lang racket
; A change in this file implies a server restart.

(require racket/sandbox)

(define sandbox (lambda ()
    (parameterize (
                    [sandbox-eval-limits '(2 16)] ; seconds and megabytes
                    [sandbox-output (current-output-port)]
                    [sandbox-path-permissions
                        (list
                            (list 'read (build-path (current-directory) "Grapic.rkt"))
                            (list 'read (build-path (current-directory) "compiled"))
                            (list 'exists (current-directory))
                            )]
                    )
        (make-evaluator 'racket)
    )))

(define (compile-and-run source)
    (let ( (SB (sandbox)) )
        (SB '(namespace-require "Grapic.rkt"))
        (SB '(define (error-handler exn) exn))
        (SB '(define (repl source)
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
        )
        (SB (list 'repl source))
    ))

(define (error-handler exn) (display "\001\002RACKET") (display exn) (display "\001"))

(define (daemon)
    (with-handlers ([exn:fail? error-handler]) ; File does not exists
        (let ( (source (open-input-file (read-line))) )
            (with-handlers ([exn:fail? (lambda (exn) (close-input-port source) (error-handler exn))])
                (compile-and-run source))
        )
    )
    (display "\001\002RACKETFini !\001")
    (flush-output)
    (daemon)
)

(daemon)