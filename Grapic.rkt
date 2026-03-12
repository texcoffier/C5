#lang racket

(provide turtles turn move draw disc)

(define grapic-parameters (lambda (L)
    (if (empty? (cdr L))
      (list (number->string (car L)) ")\001")
      (cons (number->string (car L))
        (cons "," (grapic-parameters (cdr L)))
        ))))
(define grapic (lambda (L) ; Function and args
    (display
      (string-join
        (cons
          "\001\002EVALG."
          (cons
            (car L)
            (cons "(" (grapic-parameters (cdr L)))
            ))))))
(define turtles (lambda (largeur hauteur X Y A)
    (grapic (list "init" largeur hauteur))
    (list X (- hauteur Y) A)
    ))
(define turn ; -> turtle
  (lambda (angle T) ; angle: rotation en radian. Turtle
    (list (car T) (cadr T) (+ (caddr T) angle))
    ))
(define move ; -> turtle
  (lambda (longueur T) ; longueur du déplacement. Turtle
    (let* (
        (X (car T))
        (Y (cadr T))
        (A (caddr T))
        (RAD (* pi (/ A 180)))
        )
      (list
        (+ X (* longueur (cos RAD)))
        (+ Y (* longueur (sin RAD)))
        A
        )
      )
    ))
(define draw ; -> turtle
  (lambda (longueur T) ; longueur du déplacement. Turtle
    (let (
        (nouveau (move longueur T))
        )
      (grapic (list "line"
          (car T) (cadr T) (car nouveau) (cadr nouveau)))
      nouveau
      )))

(define disc ; -> turtle
  (lambda (radius T) ; Rayon du disc. Turtle
    (grapic (list "circleFill" (car T) (cadr T) radius))
    ))
