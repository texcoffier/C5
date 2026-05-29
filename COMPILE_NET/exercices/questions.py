

COURSE_OPTIONS = {
    "state": "Ready",
    "checkpoint": 0,
    "title": "Création et configuration de réseaux",
    "sequential": 0,
    }

class Q1(Question):
    """2 réseaux, 1 routeur"""
    def default_answer(self):
        return """On a :
    * Le réseau 1:«10.0.0.0/8»     contenant la machine «M1»
    * Le réseau 2:«192.168.0.0/24» contenant la machine «M2»
    * Un unique routeur nommé «A»

Vous devez configurer le routeur pour que les 2 machines communiquent.
Les IP des interfaces des routeurs doivent être les dernières valides des réseaux.
La passerelle des machines est toujours la dernière IP valide du réseau.

Les tables au dessous ne doivent pas contenir de rouge.
La matrice 2×2 de pings à droite doit être verte.

Les interfaces des routeurs :
┏━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃ Un unique routeur «A» avec 2 interfaces
┣━━━━━━━╋━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│ Vous indiquez le numéro du réseau : 1 2 3 ...
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│ L'adresse IP de l'interface sous la forme A.B.C.D
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│ Le netmask du réseau sous la forme A.B.C.D
┣━━━━━━━╉───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│ Et la deuxième interface du routeur.
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┘

Les tables de routage des routeurs, elles sont inutiles pour cet exercice
car les routes vers les réseaux locaux sont automatiquement utilisées.
┏━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Routes┃   Routeur A   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━┩
┃Réseau ┃   Inutile     │
┃Netmask┃               │
┃Gateway┃               │
┣━━━━━━━╉───────────────┤
┃Réseau ┃   Inutile     │
┃Netmask┃               │
┃Gateway┃               │
┗━━━━━━━┹───────────────┘
"""
    def tester(self):
        A = self.worker.executable.analyze
        if (A.nr_routers == 1 and A.nr_routes == 0 and A.nr_interfaces == 2
                and A.nr_max_routers_per_switch == 1
                and A.total_ping_fails == 0
                and A.total_ping_distance == 6
                and A.r_total_ping_fails == 2
                and A.r_total_ping_distance == 2
                and A.s_total_ping_fails == 4
                and A.s_total_ping_distance == 4
                and A.l_total_ping_fails == 4
                and A.l_total_ping_distance == 4
                and A.nr_problems == 0
                ):
            self.next_question()

class Q2(Question):
    """3 réseaux, 2 routeurs"""
    def default_answer(self):
        return """On a :
    * Le réseau 1:«10.0.0.0/8»     contenant la machine «M1»
    * Le réseau 2:«192.168.0.0/24» contenant la machine «M2»
    * Le réseau 3:«1.1.1.16/29»    contenant la machine «M3»
    * Deux routeurs «A» et «B».

Vous devez configurer les routeurs pour que les 3 machines communiquent.
Les IP des interfaces des routeurs doivent être les dernières valides des réseaux.
La passerelle des machines est toujours la dernière IP valide du réseau.

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃   Routeur B   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃       1       │       2       │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┤
┃Réseau ┃       3       │       3       │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┘
Indiquez toujours le réseau destination le plus petit possible.
┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃Routes ┃    Routeur A  ┃   Routeur B   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│Adresse réseau destination sous la forme A.B.C.D
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│Netmask réseau destination sous la forme A.B.C.D
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│IP de la passerelle sous la forme A.B.C.D
┣━━━━━━━╉───────────────┼───────────────┤
┃Réseau ┃    Inutile    │    Inutile    │
┃Netmask┃               │               │
┃Gateway┃               │               │
┗━━━━━━━┹───────────────┴───────────────┘
"""
    def tester(self):
        A = self.worker.executable.analyze
        if (A.nr_routers == 2 and A.nr_routes == 2 and A.nr_interfaces == 2
                and A.nr_max_routers_per_switch == 2
                and A.total_ping_fails == 0
                and A.total_ping_distance == 18
                and A.r_total_ping_fails == 9
                and A.r_total_ping_distance == 12
                and A.s_total_ping_fails == 14
                and A.s_total_ping_distance == 18
                and A.l_total_ping_fails == 17
                and A.l_total_ping_distance == 27
                and A.nr_problems == 0
                ):
            self.next_question()

class Q3(Question):
    """5 réseaux, 2 routeurs (agrégations)"""
    def default_answer(self):
        return """On a :
    * Le réseau 1:«1.1.1.64/27»  contenant la machine «M1»
    * Le réseau 2:«1.1.1.96/27»  contenant la machine «M2»
    * Le réseau 3:«1.1.2.64/26»  contenant la machine «M3»
    * Le réseau 4:«1.1.2.128/26» contenant la machine «M4»
    * Le réseau 5:«1.1.2.0/26»   contenant la machine «M5»
    * Deux routeurs «A» et «B».

Vous devez configurer les routeurs pour que toutes les machines communiquent.
Les IP des interfaces des routeurs doivent être les dernières valides des réseaux.
La passerelle des machines est toujours la dernière IP valide du réseau.

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃   Routeur B   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃       1       │       3       │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┤
┃Réseau ┃       2       │       4       │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┤
┃Réseau ┃       5       │       5       │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┘
Indiquez toujours le réseau destination le plus petit possible.
┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃Routes ┃    Routeur A  ┃   Routeur B   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┘
"""
    def tester(self):
        A = self.worker.executable.analyze
        if (A.nr_routers == 2 and A.nr_routes <= 3 and A.nr_interfaces == 3
                and A.nr_max_routers_per_switch == 2
                and A.total_ping_fails == 0
                and A.total_ping_distance == 55
                and A.r_total_ping_fails == 30
                and A.r_total_ping_distance == 30
                and A.s_total_ping_fails == 48
                and A.s_total_ping_distance == 151
                and A.l_total_ping_fails == 58
                and A.l_total_ping_distance == 176
                and A.nr_problems == 0
                ):
            self.next_question()

class Q4(Question):
    """3 réseaux, 3 routeurs. Routes multiples"""
    def default_answer(self):
        return """On a :
    * Le réseau 1:«1.1.1.0/29»  contenant la machine «M1»
    * Le réseau 2:«1.1.1.32/28» contenant la machine «M2»
    * Le réseau 3:«1.1.1.64/27» contenant la machine «M3»

Configurez les routeurs pour que le réseau distant soit
accessible même si un routeur ou un lien tombe en panne.

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃   Routeur B   ┃   Routeur C   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃       1       │       2       │      3        │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┤
┃Réseau ┃       3       │       1       │      2        │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┘

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃Routes ┃    Routeur A  ┃   Routeur B   ┃   Routeur C   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┘

Pour ce simulateur on considère que le ping fonctionne
de X vers Y même si le retour Y vers X est impossible.
"""

    def tester(self):
        A = self.worker.executable.analyze
        if (A.nr_routers == 3 and A.nr_routes <= 6 and A.nr_interfaces == 2
                and A.nr_max_routers_per_switch == 2
                and A.total_ping_fails == 0
                and A.total_ping_distance == 18
                and A.r_total_ping_fails == 6
                and A.r_total_ping_distance == 39
                and A.s_total_ping_fails == 12
                and A.s_total_ping_distance == 24
                and A.l_total_ping_fails == 12
                and A.l_total_ping_distance == 78
                and A.nr_problems == 0
                ):
            self.next_question()

class Q5(Question):
    """4 réseaux, 3 routeurs. Agrégation de routes"""
    def default_answer(self):
        return """On a :
    * Le réseau 1:«1.1.0.0/25»   contenant la machine «M1»
    * Le réseau 2:«1.1.0.128/25» contenant la machine «M2»
    * Le réseau 3:«1.1.1.0/25»   contenant la machine «M3»
    * Le réseau 4:«1.1.1.128/25» contenant la machine «M4»

Une fois les interfaces des routeurs configurées,
indiquez un nombre MINIMAL de routes pour que cela fonctionne.

ATTENTION : la passerelle par défaut des ordinateurs est la dernière valide du réseau.
Cela va changer la résilience du réseau suivant l'ordre des IP des routeurs.
On veut évidemment le réseau qui supporte le mieux les pannes.
Pensez à sauvegarder quand vous testez différentes versions.
┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃   Routeur B   ┃   Routeur C   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃       1       │       2       │      3        │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┤
┃Réseau ┃       2       │       3       │      4        │
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┘

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃Routes ┃    Routeur A  ┃   Routeur B   ┃   Routeur C   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┘
"""

    def tester(self):
        A = self.worker.executable.analyze
        if (A.nr_routers == 3 and A.nr_routes <= 4 and A.nr_interfaces == 2
                and A.nr_max_routers_per_switch == 2
                and A.total_ping_fails == 0
                and A.total_ping_distance == 38
                and A.r_total_ping_fails == 22 # 23
                and A.r_total_ping_distance == 46
                and A.s_total_ping_fails == 32 # 34
                and A.s_total_ping_distance == 56
                and A.l_total_ping_fails == 42 # 43
                and A.l_total_ping_distance == 98
                and A.nr_problems == 0
                ):
            self.next_question()


class QEnd(Question):
    """Faire communiquer une machine et un routeur"""
    def default_answer(self):
        return """

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃       ┃   Routeur A   ┃   Routeur B   ┃   Routeur C   ┃   Routeur D   ┃   Routeur E   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃  IP   ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┴───────────────┴───────────────┘

┏━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃Routes ┃    Routeur A  ┃   Routeur B   ┃   Routeur C   ┃   Routeur D   ┃   Routeur E   ┃
┣━━━━━━━╋━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┣━━━━━━━╉───────────────┼───────────────┼───────────────┼───────────────┼───────────────┤
┃Réseau ┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Netmask┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┃Gateway┃♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│♯♯♯♯♯♯♯♯♯♯♯♯♯♯♯│
┗━━━━━━━┹───────────────┴───────────────┴───────────────┴───────────────┴───────────────┘
"""
