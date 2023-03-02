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
    last = -1
    current_question = -1
    if not http_server:
        http_server = ''
    for line in http_server.split('\n'):
        if len(line) == 0:
            continue
        line = eval(line) # pylint: disable=eval-used
        current_time = line[0]
        for cell in line[1:]:
            if is_int(cell):
                current_time += cell
                continue
            if cell.toLowerCase:
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
            'time_bonus': time_bonus,
           }

WHAT = ['nr_answered', 'grades', 'graders', 'time', 'key_stroke', 'mouse_click',
        'copy_ok', 'copy_bad', 'cut_ok', 'cut_bad', 'paste_ok', 'paste_bad', 'nr_blurs'
       ]

COLORS = ["888", "F44", "FF0", "0F0", "0FF", "88F", "F0F", "CCC"]

def display(): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Create the admin home page"""
    document.title = "👁" + COURSE.split('=')[1]
    students = []
    for student in STUDENTS:
        students.append(student)
    students.sort()
    ungraded = []
    nr_grades = {}
    sums = {}
    for what in WHAT:
        sums[what] = ''
        sums[what + '\001done']  = ''
    text = ["""<!DOCTYPE html>
<style>
TABLE { border-spacing: 0px; border-collapse: collapse }
TABLE TD { vertical-align: top; border: 1px solid #888; padding: 0px; white-space: pre}
TEXTAREA { border: 0px; min-height:10em; font-size:60%; width:10em; height:100% }
BUTTON { width: 100% }
E { font-family: emoji }
TABLE TR:hover TD { background: #EEE }
"""]
    for i, color in enumerate(COLORS):
        text.append(
            'SPAN.sec' + i + '{ display: inline-block; height: 1em; vertical-align: top;'
            + 'height: 1.3em;}')
        text.append('.sec' + i + '{ background: #' + color + '}')
    text.append("""
</style>
<p>
<table border>
    <tr><th>Login<th>Time<br>Bonus<th>Status<th colspan="2">Questions<br>Validated<th>Grade<th>Graders<th>Time<br>in sec.<th>Keys
        <th>Mouse<th>Copy<th>Copy<br>Fail<th>Cut<th>Cut<br>Fail<th>Paste<th>Paste<br>Fail<th>Window<br>Blur<th>Time per question<br>
        <E>🐌</E> : clipped to """ + SNAIL + """ times the median answer time.<th>Files</tr>
""")
    cache = {}
    question_times = []
    for login in students:
        print(login)
        student = STUDENTS[login]
        cache[login] = analyse(student.http_server)
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
        text.append('<td>')
        if stats['time_bonus']:
            text.append(stats['time_bonus'] / 60 + " min.")
        else:
            text.append('')
        text.append('<td>')
        text.append(student.status)
        text.append('<td>')
        text.append(stats['questions'])
        stats['time'] = sum(stats['time_sum'])
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'
            if student.status == 'done':
                sums[what + '\001done'] += login + '\t' + stats[what] + '\n'

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
    text.append('''
<tr><td><td><td><td>Sources:
<button onclick="window.location.pathname = '/adm/answers/' + COURSE + '.zip'"
>Sources<br>txt ZIP</button>
''')
    for what in WHAT:
        text.append('<td><textarea>' + sums[what] + '</textarea>')
        text.append('<p>Only «done» :<br>')
        text.append('<textarea>' + sums[what + '\001done'] + '</textarea>')
    text.append('<td><table style="font-size: 90%">')
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
    for teacher, students in by_teacher.Items():
        text.append('<tr><td>')
        text.append(teacher)
        text.append('<td>')
        text.append(links(students))
        text.append('<td>')
        text.append(links(students, True))
        text.append('</tr>')

    text.append('</table>')

    document.body.innerHTML = text.join('') # pylint: disable=no-member

display()
