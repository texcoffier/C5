"""
Generate the home page for a course.
"""

WHAT = ['bonus_time', 'status', 'nr_answered', 'grades', 'comments', 'version', 'graders',
        'nr_blurs', 'blur_time']

sums = {}

def hide():
    """Close the dialog"""
    document.getElementById('dialog').close()

def show(what):
    """Display the export file for this key"""
    dialog = document.getElementById('dialog')
    ths = document.getElementById('report').rows[0]
    label = ths.cells[WHAT.indexOf(what.split('\001')[0]) + 1].textContent
    if '\001' in what:
        status = "done"
    else:
        status = "any"
    dialog.innerHTML = ('<button onclick="hide()">×</button> <b>' + label + '</b> Status=' + status
                        + '<br><br><textarea>' + html(sums[what]) + '</textarea>')
    dialog.showModal()

def display(): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Create the admin home page"""
    notation = Grades(NOTATION)
    document.title = "👁" + COURSE.split('=')[1]
    students = []
    for student in STUDENTS:
        students.append(student)
    students.sort()
    ungraded = []
    nr_grades = {}
    for what in WHAT:
        sums[what] = ''
        sums[what + '\001done']  = ''
    text = ["""<!DOCTYPE html>
<style>
BODY { font-family: sans-serif; }
TABLE { border-spacing: 0px; }
TABLE TD { vertical-align: top; border: 1px solid #888; padding: 0px; white-space: pre}
BUTTON { width: 100% }
E { font-family: emoji }
TABLE#report TR:first-child, TABLE#TOMUSS TR:first-child {
  height: 3em; z-index: 100;position: sticky; top: 0px; background: #FFFD; }
TABLE#report > TBODY > TR:hover > TD { background: #DDD }
TABLE#report > TBODY > TR > TD:nth-child(2) > DIV { font-size: 60% }
BUTTON.download { width: calc(100% - 2px); font-size: 150%; height: 1.5em; margin: 1px;}
DIALOG { position: fixed; right: 0px; top: 0px; border: 4px solid #0F0 }
DIALOG BUTTON { font-size: 200%; width: 2em }
DIALOG TEXTAREA { width: 40em ; height: 40em }
DIV[onclick] { cursor: pointer; width: 100%; height: 3em }
DIV[onclick]:hover { background: #EEE }
</style>
<dialog id="dialog"></dialog>
<p>
<table id="report" border><tbody><tr>
<th><div onclick="sort_report(0)">Login</div>
<th><div onclick="sort_report(1)">Name</div>
<th><div onclick="sort_report(2)">Minutes<br>Bonus</div>
<th><div onclick="sort_report(3)">Status</div>
<th><div onclick="sort_report(4)">Questions<br>Validated</div>
<th><div onclick="sort_report(5)">Grade</div>
<th><div onclick="sort_report(6)">Comments</div>
<th><div onclick="sort_report(7)">Version</div>
<th><div onclick="sort_report(8)">Graders</div>
<th><div onclick="sort_report(9)">Window<br>Blur</div>
<th><div onclick="sort_report(10)">Blur<br>time</div>
<th><div onclick="sort_report(11)">Files</div></tr>
"""]
    cache = {}
    nr_grades_max = {'a': 0, 'b': 0}
    for login in students:
        print(login)
        student = STUDENTS[login]
        cache[login] = journal = Journal(student.journal)
        journal['status'] = student.status
        journal.login = login
        journal['comments'] = len([bubble
                                        for bubble in journal.bubbles
                                        if bubble.login
                                      ])
        nr_blurs = 0
        blur_time = 0
        last_blur = 0
        nr_answered = 0
        for line in journal.lines:
            if line.startswith('#bonus_time '):
                journal['bonus_time'] = int(line.split(' ')[1]) / 60
            elif line.startswith('T'):
                t = int(line[1:])
            elif line.startswith('F'):
                if last_blur:
                    blur_time += t - last_blur
            elif line.startswith('B'):
                last_blur = t
                nr_blurs += 1
            elif line.startswith('g'):
                nr_answered += 1
            elif line.startswith('#checkpoint_stop'):
                break
        journal['nr_blurs'] = nr_blurs
        journal['blur_time'] = blur_time
        journal['nr_answered'] = nr_answered
            
        if not STUDENT_DICT[login]:
            print(login, "In LOGS but not in session.cf")
            continue
        version = journal['version'] = STUDENT_DICT[login][2].split(',')[3]
        grading = parse_grading(student['grades'])
        grade = 0
        graders = []
        for grd in notation.grades:
            if grd.is_competence:
                continue # It'a a competence
            value = grading[grd.key]
            if not value or value[0] == '?':
                continue
            grade += Number(value[0])
            grader = value[1].split('\n')[1]
            if grader not in graders:
                graders.append(grader)
        nr_grades[login] = len(grading)
        nr_grades_max[version] = max(nr_grades_max[version], len(grading))
        if len(grading) == 0 and student.status == 'done':
            ungraded.append(login)
            journal['grades'] = ''
        else:
            journal['grades'] = grade
        graders.sort()
        journal['graders'] = ' '.join(graders)

    for login in students:
        student = STUDENTS[login]
        stats = cache[login]
        text.append('<tr><td>')
        if student.status != 'checkpoint':
            text.append('<a href="checkpoint/' + COURSE + '?ticket=' + TICKET + '#{&quot;student&quot;:&quot;' + login
                + '&quot;}" target="_blank">' + login + '</a>')
        else:
            text.append(login)
        text.append('<td><div>')
        infos = window.parent.STUDENTS[login] or {'sn': '?', 'fn': '?'}
        text.append(infos.sn + '<br>' + infos.fn)
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'
            if student.status == 'done':
                sums[what + '\001done'] += login + '\t' + stats[what] + '\n'

        text.append('<td>')
        for filename in student.files:
            text.append(' <a target="_blank" href="adm/get/COMPILE_'
                + COURSE.replace('=', '/') + '/')
            text.append('LOGS/')
            text.append(login)
            text.append('/')
            text.append(filename)
            text.append(window.location.search)
            text.append('">')
            text.append(filename)
            text.append('</a>')
    text.append('''<tr><td><tt>login value</tt>\nStatus=Any<td rowspan="2"
><div style="vertical-align:top;font-size:80%">All sources codes:<br>
<button onclick="window.open(BASE + '/adm/answers/' + COURSE + '/*/' + COURSE + '.zip')"
 style="background: #EEE">Sources<br>txt ZIP</button></div>''')

    for what in WHAT:
        text.append('<td><button class="download" onclick="show(\''
                    + what + '\')">📥</button>')

    text.append('</tr>')
    text.append('<tr><td><tt>login value</tt>\nStatus=done')
    for what in WHAT:
        text.append('<td><button  class="download" onclick="show(\''
                    + what + '\001done' + '\')">📥</button>')
    text.append('</tr>')
    text.append('</tbody></table>')

    ###########################################################################
    ###########################################################################
    ###########################################################################

    def link(login, replace=False):
        """Grading link"""
        if replace:
            txt = student_id(login)
        else:
            txt = login
        return ('<a href="grade/'+COURSE+'/'+login+'?ticket='+TICKET
                + '" target="_blank">' + txt + '</a>')

    def links(logins, replace=False):
        """List a links"""
        return ' | '.join([link(login, replace) for login in logins])

    text.append('''
    <p>
    <style>
    TABLE.problems { table-layout: fixed; max-width: 100% }
    .problems TR TH:first-child { width: 10em }
    .problems TR TD:nth-child(2), .problems TD:nth-child(3) {
            width: 40vw;
            white-space: normal;
            padding: 0.5em;
            }
    </style>
    <table class="problems">
    ''')

    if ungraded:
        text.append('<tr><th>Ungraded students<td>')
        text.append(links(ungraded))
        text.append('<td>')
        text.append(links(ungraded, True))
        text.append('</tr>')

    by_teacher = {}
    partially_graded = []
    for login, nrg in nr_grades.Items():
        if nrg and nrg < nr_grades_max[cache[login]['version']]:
            partially_graded.append(login)
            for grader in cache[login]['graders'].split(' '):
                if not by_teacher[grader]:
                    by_teacher[grader] = [login]
                else:
                    by_teacher[grader].append(login)

    if partially_graded:
        text.append('<tr><th>One or more grades are missing<td>')
        text.append(links(partially_graded))
        text.append('<td>')
        text.append(links(partially_graded, True))
        text.append('</tr>')

    partially_graded = []
    for login, nrg in nr_grades.Items():
        if nrg and nrg < nr_grades_max[cache[login]['version']] - 1:
            partially_graded.append(login)
    if partially_graded:
        text.append('<tr><th>Two or more grades are missing<td>')
        text.append(links(partially_graded))
        text.append('<td>')
        text.append(links(partially_graded, True))
        text.append('</tr>')
    for teacher, students_of_teacher in by_teacher.Items():
        text.append('<tr><td>')
        text.append(teacher)
        text.append('<td>')
        text.append(links(students_of_teacher))
        text.append('<td>')
        text.append(links(students_of_teacher, True))
        text.append('</tr>')

    text.append('</table>')

    ###########################################################################
    ###########################################################################
    ###########################################################################

    if NOTATIONB.strip() != '':
        text.append("<h2>Importation du détail des notes dans TOMUSS impossible car 2 barèmes</h2>")
    else:
        text.append("""<h2>Importation du détail des notes dans TOMUSS</h2>
        <ul>
        <li> Passez une colonne TOMUSS dans le type «Notation»
        <li> Cliquez sur le «Importer» à droite du bouton «Notation» (en rouge)
        <li> Faite un copier/coller de la table suivante complète dans la zone blanche.
        <li> Cliquer sur le bouton «Importer les détails de notation»
        </ul>
        <table id="TOMUSS"><tr><td>ID<td>Nom<td>Prénom""")
        labels = {}
        header2 = '' # Second line of headers
        for grade in notation.grades:
            while grade.label in labels:
                grade.label += '+'
            labels[grade.label] = True
            step = 1
            grade_max = float(grade.grades[0])
            grade_min = float(grade.grades[0])
            for value in grade.grades:
                value = float(value)
                if value > grade_max:
                    grade_max = value
                elif value < grade_min:
                    grade_min = value
                mod = Math.abs(value) % 1.
                if mod and mod < step:
                    step = mod
            if grade_min < 0 or 'bonus' in grade.label.lower():
                what = '±'
            else:
                what = ''
            if -grade_min > grade_max:
                grade_max = -grade_min
            text.append(
                "<td>" + what + grade_max + '<td>' + html(grade.label))
            header2 += '<td>Note<td>Commentaire'

        text.append('</tr><tr><td><td><td>')
        text.append(header2)
        text.append('</tr>')
        for login in students:
            student = STUDENTS[login]
            if student.status != 'done':
                continue
            text.append('<tr><td>')
            text.append(login)
            text.append('<td><td>')
            grading = parse_grading(student['grades'])
            for grade in notation.grades:
                text.append('<td>')
                if grading[grade.key]:
                    text.append(grading[grade.key][0])
                else:
                    text.append('???')
                text.append('<td>')
            text.append('</tr>')
        text.append('</table>')

    ###########################################################################
    ###########################################################################
    ###########################################################################

    text.append("""<h2>Compétences</h2>
                   <table id="TOMUSS_competence"><tr><td>ID<td>Compétence</tr>""")
    for login in students:
        student = STUDENTS[login]
        if student.status != 'done':
            continue
        text.append('<tr><td>')
        text.append(login)
        text.append('<td>')
        grading = parse_grading(student['grades'])
        competences = {}
        for grade in notation.competences:
            code = replace_all(grade.key, "'", "") # «'» used for duplicate keys
            if code not in competences:
                competences[code] = []
            note = grading[grade.key]
            if note and note[0] != '' and note[0] != '?':
                competences[code].append(float(note[0]))
        competences_list = []
        for key, values in competences.Items():
            if len(values):
                competences_list.append(key + 'o' + (Math.round(sum(values) / len(values)) + 1))
            else:
                competences_list.append(key + 'o0')
        competences_list.sort()
        text.append(' '.join(competences_list))
        text.append('</tr>')
    text.append('</table>')

    document.body.innerHTML = text.join('') # pylint: disable=no-member

def sort_report(col):
    print("Sorting")
    def cmp(a, b):
        if a > b:
            return 1
        if a == b:
            return 0
        return -1
    table = document.getElementById('report')
    lines = []
    for line in table.rows:
        if line.cells[0].innerHTML.startswith('<a'):
            value = line.cells[col].textContent
            if not isNaN(value):
                value = 1000000000 + Number(value)
            lines.append([value, line])
        else:
            last = line
    lines.sort(cmp)
    last = last.previousSibling
    for _, line in lines:
        line.remove()
    for _, line in lines:
        table.firstChild.insertBefore(line, last)

display()
