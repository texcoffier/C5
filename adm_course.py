"""
Generate the home page for a course.
"""

MAX_WIDTH = 400
SNAIL = 4

def analyse(http_server): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Extract statistiques from log"""
    answered = []
    key_stroke = 0
    mouse_click = 0
    copy_bad = 0
    copy_ok = 0
    cut_bad = 0
    cut_ok = 0
    paste_bad = 0
    paste_ok = 0
    nr_answered = 0
    nr_blurs = 0
    time_start = 0
    time_sum = []
    time_bonus = 0
    blur_time = 0
    last = -1
    current_question = -1
    current_time = 0
    if not http_server:
        http_server = ''
    blur_start = 0
    for line in http_server.split('\n'):
        if len(line) == 0:
            continue
        line = eval(line) # pylint: disable=eval-used
        if line[0] < current_time:
            print(current_time, line)
            continue
        current_time = line[0]
        for cell in line[1:]:
            if is_int(cell):
                current_time += cell
                continue
            if cell.toLowerCase:
                if blur_start:
                    blur_time += current_time - blur_start
                    blur_start = 0
                if cell.startswith('Mouse'):
                    mouse_click += 1
                elif cell == 'CopyRejected':
                    copy_bad += 1
                elif cell == 'CutRejected':
                    cut_bad += 1
                elif cell == 'PasteRejected':
                    paste_bad += 1
                elif cell.startswith('Paste'):
                    paste_ok += 1
                elif cell.startswith('Copy'):
                    copy_ok += 1
                elif cell.startswith('Cut'):
                    cut_ok += 1
                elif cell.startswith('Blur'):
                    nr_blurs += 1
                    blur_start = current_time
                else:
                    key_stroke += 1
                continue
            if cell[0] == 'time bonus':
                time_bonus = cell[1]
            if cell[0] == 'answer':
                answered[cell[1]] = cell[2]
                if cell[1] > last:
                    last = cell[1]

            if cell[0] in ('question', 'answer'):
                if current_question >= 0:
                    time_sum[current_question] = (time_sum[current_question] or 0
                                                 ) + (current_time - time_start)
                if cell[0] == 'answer':
                    current_question = -1
                else:
                    current_question = cell[1]
                time_start = current_time

    text = ''
    for i in range(last+1):
        if answered[i]:
            text += '|'
            nr_answered += 1
        else:
            text += '·'
        if not time_sum[i]:
            time_sum[i] = 0
    return {'questions': text, 'key_stroke': key_stroke, 'mouse_click': mouse_click,
            'copy_bad': copy_bad, 'copy_ok': copy_ok,
            'paste_bad': paste_bad, 'paste_ok': paste_ok,
            'cut_bad': cut_bad, 'cut_ok': cut_ok,
            'nr_answered': nr_answered,
            'nr_blurs': nr_blurs,
            'time_sum': time_sum,
            'time_bonus': time_bonus / 60,
            'blur_time': blur_time
           }

WHAT = ['time_bonus', 'status', 'nr_answered', 'grades', 'graders', 'time',
        'key_stroke', 'mouse_click',
        'copy_ok', 'copy_bad', 'cut_ok', 'cut_bad', 'paste_ok', 'paste_bad', 'nr_blurs', 'blur_time'
       ]

COLORS = ["888", "F44", "FF0", "0F0", "0FF", "88F", "F0F", "CCC"]

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
TABLE#report TR:first-child, TABLE#TOMUSS TR:first-child { position: sticky; top: 0px; background: #FFFD; }
TABLE TR:hover TD { background: #EEE }
BUTTON.download { width: calc(100% - 2px); font-size: 150%; height: 1.5em; margin: 1px;}
DIALOG { position: fixed; right: 0px; top: 0px; border: 4px solid #0F0 }
DIALOG BUTTON { font-size: 200%; width: 2em }
DIALOG TEXTAREA { width: 40em ; height: 40em }
"""]
    for i, color in enumerate(COLORS):
        text.append(
            'SPAN.sec' + i + '{ display: inline-block; height: 1em; vertical-align: top;'
            + 'height: 1.3em;}')
        text.append('.sec' + i + '{ background: #' + color + '}')
    text.append("""
</style>
<dialog id="dialog"></dialog>
<p>
<table id="report" border>
    <tr><th>Login<th>Minutes<br>Bonus<th>Status<th colspan="2">Questions<br>Validated<th>Grade<th>Graders<th>Time<br>in sec.<th>Keys
        <th>Mouse<th>Copy<th>Copy<br>Fail<th>Cut<th>Cut<br>Fail<th>Paste<th>Paste<br>Fail<th>Window<br>Blur<th>Blur<br>time<th>Time per question<br>
        <E>🐌</E> : clipped to """ + SNAIL + """ times the median answer time.<th>Files</tr>
""")
    cache = {}
    question_times = []
    for login in students:
        print(login)
        student = STUDENTS[login]
        cache[login] = analyse(student.http_server)
        cache[login]['status'] = student.status
        grading = parse_grading(student['grades'])
        grade = 0
        graders = []
        for question in grading:
            grade += Number(grading[question][0])
            if len(grading[question][0]):
                grader = grading[question][1].split('\n')[1]
                if grader not in graders:
                    graders.append(grader)
        nr_grades[login] = len(grading)
        if len(grading) == 0 and student.status == 'done':
            ungraded.append(login)
            cache[login]['grades'] = ''
        else:
            cache[login]['grades'] = grade
        graders.sort()
        cache[login]['graders'] = ' '.join(graders)
        for i, seconds in enumerate(cache[login]['time_sum']):
            if not question_times[i]:
                question_times[i] = []
            question_times[i].append(seconds)
    question_medians = []
    for i, times in enumerate(question_times):
        sortable = [1000000000 + time for time in times] # JS can't sort numbers
        sortable.sort()
        middle = Math.floor(len(sortable) // 2)
        if len(sortable) % 2 == 1:
            median = sortable[middle]
        else:
            median = (sortable[middle-1] + sortable[middle]) / 2
        if len(sortable) < 3:
            median = 1000000010 # Seconds if not 3 samples
        question_medians[i] = median - 1000000000
    max_time = Math.max(MAX_WIDTH, sum(question_medians))

    for login in students:
        student = STUDENTS[login]
        stats = cache[login]
        text.append('<tr><td>')
        if student.status != 'checkpoint':
            text.append('<a href="/checkpoint/' + COURSE + '?ticket=' + TICKET + '#' + login
                + '" target="_blank">' + login + '</a>')
        else:
            text.append(login)
        stats['time'] = sum(stats['time_sum'])
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'
            if student.status == 'done':
                sums[what + '\001done'] += login + '\t' + stats[what] + '\n'
            if what == 'status':
                text.append('<td>')
                text.append(stats['questions'])

        text.append('<td>')
        for i, seconds in enumerate(stats['time_sum']):
            if seconds > question_medians[i] * SNAIL:
                seconds = question_medians[i] * SNAIL
                if question_medians[i] != 10:
                    more = '<E>🐌</E>'
            else:
                more = ''
            text.append('<span style="width:' + (MAX_WIDTH*seconds)/max_time
                        + 'px" class="sec' + i % len(COLORS) + '">' + more + '</span>')
        text.append('<td>')
        for filename in student.files:
            text.append(' <a target="_blank" href="/adm/get/COMPILE_'
                + COURSE.replace('=', '/') + '/')
            text.append(login)
            text.append('/')
            text.append(filename)
            text.append(window.location.search)
            text.append('">')
            text.append(filename)
            text.append('</a>')
    text.append('<tr><td><tt>login value</tt>\nStatus=Any')
    for what in WHAT:
        text.append('<td><button class="download" onclick="show(\''
                    + what + '\')">📥</button>')
        if what == 'status':
            text.append('''
<td rowspan="2">Sources:
<button onclick="window.location.pathname = '/adm/answers/' + COURSE + '.zip'"
>Sources<br>txt ZIP</button>''')

    text.append('<td rowspan="2"><table style="font-size: 90%">')
    text.append('<tr><th>Question<th>Students<th>Min<th>Average<th>Median<th>Max</tr>')
    for i, times in enumerate(question_times):
        text.append('<tr><td class="sec' + (i % len(COLORS)) + '">' + (i+1)
                    + '<td>' + len(times)
                    + '<td>' + min(times)
                    + '<td>' + Math.floor(sum(times)/len(times))
                    + '<td>' + question_medians[i]
                    + '<td>' + max(times)
                    + '</tr>')
    text.append('</table></tr>')
    text.append('<tr><td><tt>login value</tt>\nStatus=done')
    for what in WHAT:
        text.append('<td><button  class="download" onclick="show(\''
                    + what + '\001done' + '\')">📥</button>')
    text.append('</tr>')
    text.append('</table>')

    def link(login, replace=False):
        """Grading link"""
        if replace:
            txt = login.replace('p', '1')
        else:
            txt = login
        return ('<a href="/grade/'+COURSE+'/'+login+'?ticket='+TICKET
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
    nr_grades_max = max(*nr_grades.Values())
    for login, nrg in nr_grades.Items():
        if nrg and nrg < nr_grades_max:
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
    nr_grades_max = max(*nr_grades.Values())
    for login, nrg in nr_grades.Items():
        if nrg and nrg < nr_grades_max - 1:
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


    notation = parse_notation(NOTATION)
    text.append("""<h2>Importation du détail des notes dans TOMUSS</h2>
    <ul>
    <li> Passez une colonne TOMUSS dans le type «Notation»
    <li> Cliquez sur «Importer» (en rouge)
    <li> Faite un copier/coller de la table suivante complète dans la zone blanche.
    <li> Cliquer sur le bouton «Importer les détails de notation»
    </ul>
    <table id="TOMUSS"><tr><td>ID<td>Nom<td>Prénom""")
    labels = {}
    for infos in notation:
        _text, grade_label, values = infos
        if len(grade_label) == 0:
            continue
        while grade_label in labels:
            grade_label += '+'
        labels[grade_label] = True
        step = 1
        grade_max = float(values[0])
        grade_min = float(values[0])
        for value in values:
            value = float(value)
            if value > grade_max:
                grade_max = value
            elif value < grade_min:
                grade_min = value
            mod = Math.abs(value) % 1.
            if mod and mod < step:
                step = mod
        if grade_min < 0 or 'bonus' in grade_label.lower():
            what = '±'
        else:
            what = ''
        if -grade_min > grade_max:
            grade_max = -grade_min
        text.append(
            "<td>" + what + grade_max + '<td>' + html(grade_label)
        )
    text.append('</tr><tr><td><td><td>')
    for _ in range(len(notation) - 1):
        text.append('<td>Note<td>Commentaire')
    text.append('</tr>')
    for login in students:
        student = STUDENTS[login]
        if student.status != 'done':
            continue
        text.append('<tr><td>')
        text.append(login)
        text.append('<td><td>')
        grading = parse_grading(student['grades'])
        for i in range(len(notation) - 1):
            text.append('<td>')
            if grading[i]:
                text.append(grading[i][0])
            else:
                text.append('???')
            text.append('<td>')
        text.append('</tr>')
    text.append('</table>')
    document.body.innerHTML = text.join('') # pylint: disable=no-member


display()
