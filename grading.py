class State:
    def __init__(self):
        print('Initialize server link to receive updates')
        def message(event):
            print(event.target.responseText)
            for line in event.target.responseText.split('\n'):
                try:
                    x = JSON.parse(line)
                except:
                    continue
                if x[0] == 'active_teacher_room' and x[2] in self.students:
                    student = self.students[x[2]]
                    if x[3]:
                        student.data[1][x[3]] = x[1]
                    else:
                        student.data[1] = x[1]
                    analyze_STUDENT(student, student.data)
                    # self.sort_students()
                    self.fill_labels()

        self.xhr = eval('new XMLHttpRequest()') # pylint: disable=eval-used
        self.xhr.addEventListener('readystatechange', message)
        # self.xhr.addEventListener('error', reload_on_error)
        # self.xhr.addEventListener('abort', reload_on_error)
        # self.xhr.addEventListener('timeout', reload_on_error)
        self.xhr.open("GET", 'journal/' + COURSE + '?ticket=' + TICKET)
        self.xhr.send()

        self.sort_column = 0
        self.sort_direction = 1
        self.rows = {}

        print('Get student list to display')
        path = location.pathname.split('/grading/')[1].split('/')
        path = [decodeURIComponent(i) for i in path]
        self.course = path[0]
        self.students_logins = path[1:]

        print('Create student dictionnary')
        self.students = {}
        stats_nr_grades = {}
        stats_nr_competences = {}
        for student in STUDENTS:
            login = student[0]
            if login not in self.students_logins:
                continue # Not interested
            infos = self.students[login] = {}
            analyze_STUDENT(infos, student)
            stats_nr_grades[infos.grade[1]] = (stats_nr_grades[infos.grade[1]] or 0) + 1
            stats_nr_competences[infos.grade[1]] = (stats_nr_competences[infos.grade[1]] or 0) + 1
        
        def expected_value(counters):
            """Return the more frequent values"""
            m = list(counters.Values())
            m.sort()
            m = m[-4:]
            values = []
            for value, nr in counters.Items():
                if nr in m and nr > len(self.students) / 8:
                    values.append(int(value))
            return values

        self.expected_nr_grades = expected_value(stats_nr_grades)
        self.expected_nr_competences = expected_value(stats_nr_competences)

        self.sort_students()

        print('Initialize page content')
        self.iframes = {}
        self.on_screen = None

        self.labels = document.createElement('TABLE')
        self.labels.className = 'labels'
        self.labels.onclick = bind(self.onclick, self)
        self.labels.onmousemove = bind(self.onmousemove, self)
        document.body.appendChild(self.labels)
        self.editor = document.createElement('DIV')
        self.editor.className = 'editor'
        document.body.appendChild(self.editor)
        self.tip = document.createElement('DIV')
        self.tip.className = 'tip'
        document.body.appendChild(self.tip)
        def hide_tip():
            self.tip.style.display = 'none'
            self.labels.style.zIndex = 1
        self.editor.onmouseenter = hide_tip
        self.fill_labels()

    def sort_students(self):
        def cmp_student(login_a, login_b):
            a = self.students[login_a] or 'ZZZ' + login_a
            b = self.students[login_b] or 'ZZZ' + login_b
            a = a.surname + '/' + a.firstname
            b = b.surname + '/' + b.firstname
            if a > b:
                return self.sort_direction
            elif a < b:
                return -self.sort_direction
            return 0
        def cmp_col(login_a, login_b):
            a = self.rows[login_a].childNodes[self.sort_column].textContent
            if not isNaN(a):
                a = float(a)
                if isNaN(b):
                    b = 1e99
            b = self.rows[login_b].childNodes[self.sort_column].textContent
            if not isNaN(b):
                b = float(b)
                if isNaN(a):
                    a = 1e99
            if a > b:
                return self.sort_direction
            elif a < b:
                return -self.sort_direction
            return 0
        if self.sort_column == 0:
            self.students_logins.sort(cmp_student)
        else:
            self.students_logins.sort(cmp_col)

    def fill_labels(self):
        print('Create students')

        self.labels.innerHTML = ''
        def format_grade(v):
            if v:
                return v.toFixed(2)
            return ''

        label = document.createElement('TR')
        self.labels.appendChild(label)
        label.innerHTML = ''.join(['<TD><button disabled>Corriger</button>',
            '<TD>Note<TD>#<TD>Com<TD>#<TD>✅<TD>🚨<TD>#<TD>👁<TD>Ⓐ<TD>⌚<TD>⛔<TD>Surveillant<TD>Bâtiment<TD>🖳<TD>🗨'])
        for login in self.students_logins:
            student = self.students[login]
            label = document.createElement('TR')
            self.labels.appendChild(label)
            self.rows[login] = label
            if student:
                if student.grade[1]:
                    grade = format_grade(student.grade[0])
                    nr_grades = student.grade[1]
                    if nr_grades not in self.expected_nr_grades:
                        nr_grades = '<E>' + nr_grades + '</E>'
                else:
                    grade = ''
                    nr_grades = ''
                if student.grade[3]:
                    competence = format_grade(student.grade[2])
                    nr_competences = student.grade[3]
                    if nr_competences not in self.expected_nr_competences:
                        nr_competences = '<E>' + nr_competences + '</E>'
                else:
                    competence = ''
                    nr_competences = ''
                if student.nr_questions_done:
                    nr_questions_done = student.nr_questions_done + '<sup></sup>'
                else:
                    nr_questions_done = ''
                if student.blur:
                    blur = student.blur
                    blur_time = student.blur_time
                else:
                    blur = ''
                    blur_time = ''
                t = [
                    '<TD><button id="', login, '">',
                    student.surname, ' ', student.firstname,
                    '</button>',
                    '<TD>', grade,
                    '<TD>', nr_grades,
                    '<TD>', competence,
                    '<TD>', nr_competences,
                    '<TD>', nr_questions_done,
                    '<TD>', blur,
                    '<TD>', blur_time,
                    '<TD>', ['', 's', 'c', '👁', '<o>👁</o>', '<g>👁</g>'][student.feedback],
                    '<TD>', student.version,
                    '<TD>', student.bonus_time / 60 or '',
                    '<TD>', student.active and '' or '' ,
                    '<TD>', student.teacher,
                    '<TD>', student.building,
                    '<TD>', student.fullscreen or '',
                    '<TD>', (student.remarks and student.remarks.split('\n').length) or ''
                ]
                label.innerHTML = ''.join(t)
            else:
                label.innerHTML = '<TD><BUTTON>' + login + ' : jamais connecté</BUTTON>'

    def onclick(self, event):
        element = event.target
        if element.id:
            login = element.id
            iframe = self.iframes[login]
            if not iframe:
                self.iframes[login] = iframe = document.createElement('IFRAME')
                iframe.src = BASE + '/grade/' + self.course + '/' + login + '?ticket=' + TICKET
                self.editor.appendChild(iframe)
            if self.on_screen:
                self.iframes[self.on_screen].style.display = 'none'
                document.getElementById(self.on_screen).style.background = ''
                self.rows[self.on_screen].style.opacity = 0.5
            self.on_screen = login
            element.style.background = '#FF8'
            iframe.style.display = 'block'
            return
        tr = element
        while tr and tr.tagName != 'TR':
            if tr.tagName == 'TD':
                td = tr
            tr = tr.parentNode
        if tr and tr.rowIndex == 0:
            if self.sort_column == td.cellIndex:
                self.sort_direction *= -1
            else:
                self.sort_direction = 1
            self.sort_column = td.cellIndex
            self.sort_students()
            self.fill_labels()


    def onmousemove(self, event):
        if event.target is self.last_target:
            return
        if event.target.tagName == 'BUTTON':
            self.labels.style.zIndex = 20
        self.last_target = event.target
        tr = event.target
        while tr and tr.tagName != 'TR':
            if tr.tagName == 'TD':
                td = tr
            tr = tr.parentNode
        if not tr:
            return
        button = tr.cells[0].firstChild
        login = button.id
        student = self.students[login]
        feedback = [
            FEEDBACK_LEVEL[0],
            FEEDBACK_LEVEL[1],
            FEEDBACK_LEVEL[1] + ' + corrigé',
            FEEDBACK_LEVEL[1] + ' + corrigé + commentaires',
            FEEDBACK_LEVEL[1] + ' + corrigé + commentaires + note totale',
            FEEDBACK_LEVEL[1] + ' + corrigé + commentaires + notation détaillée',
        ]
        if student:
            lines = [
                login + ' ' + student.surname.upper() + ' ' + student.firstname.lower(),
                'Moyenne des ' + student.grade[1] + ' notes : ' + student.grade[0],
                'Moyenne des ' + student.grade[3] + ' compétences : ' + student.grade[2],
                '✅ Nombre de questions validées : ' + student.nr_questions_done,
                '🚨 ' + student.blur + ' pertes de focus pour un total de ' + student.blur_time + ' secondes',
                "👁 Affichage à l'étudiant : " + feedback[student.feedback],
                "Ⓐ Version du sujet : " + student.version,
                "⌚ Temps bonus accordé (hors tiers-temps) : " + student.bonus_time/60 + ' minutes',
                "⛔ L'étudiant peut composer : " + (student.active and 'OUI' or 'NON'),
                "Placé par «" + student.teacher + '» à «' + student.building + '»',
                "🖳 Accorde le non plein écran : " + (student.fullscreen and 'OUI' or 'NON'),
                "🗨 Remarques :" + replace_all(html('\n' + student.remarks), '\n', '<br>'),
                '',
                'Cliquez sur le titre de la colonne pour trier'
            ]
            conv = [0, 1, 1, 2, 2, 3, 4, 4, 5, 6, 7, 8, 9, 9, 10, 11]
            i = conv[td.cellIndex]
            lines[i] = '<x>' + lines[i] + '</x>'
            for td in tr.childNodes:
                i = conv[td.cellIndex]
                if td.textContent == '' and '<span' not in lines[i]:
                    lines[i] = '<span style="color:#888">' + lines[i] + '</span>'
            self.tip.innerHTML = '<br>'.join(lines)
        else:
            self.tip.innerHTML = login + ' jamais connecté'
        scroll = document.body.parentNode.scrollTop
        if tr.offsetTop - scroll + self.tip.offsetHeight > window.innerHeight:
            y = window.innerHeight + scroll - self.tip.offsetHeight
        else:
            y = tr.offsetTop 
        self.tip.style.top = y + 'px'
        self.tip.style.display = 'block'
        self.tip.style.left = tr.offsetWidth + 'px'

STATE = State()
