
STUDENTS = STUDENTS
COURSE = COURSE
document = document
window = window
isNaN = isNaN
Math = Math

def analyse(http_server): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Extract statistiques from log"""
    answered = []
    key_stroke = 0
    mouse_click = 0
    copy_bad = 0
    copy_ok = 0
    paste_bad = 0
    paste_ok = 0
    nr_answered = 0
    time_start = 0
    time_sum = []
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
            if not isNaN(cell):
                current_time += cell
                continue
            if cell.toLowerCase:
                if cell.startswith('Mouse'):
                    mouse_click += 1
                elif cell == 'CopyRejected':
                    copy_bad += 1
                elif cell == 'PasteRejected':
                    paste_bad += 1
                elif cell.startswith('Paste'):
                    paste_ok += 1
                elif cell.startswith('Copy'):
                    copy_ok += 1
                else:
                    key_stroke += 1
                continue
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
            text += '*'
            nr_answered += 1
        else:
            text += '·'
        if not time_sum[i]:
            time_sum[i] = 0
    return {'questions': text, 'key_stroke': key_stroke, 'mouse_click': mouse_click,
            'copy_bad': copy_bad, 'copy_ok': copy_ok,
            'paste_bad': paste_bad, 'paste_ok': paste_ok,
            'nr_answered': nr_answered,
            'time_sum': time_sum,
           }

WHAT = ['nr_answered', 'key_stroke', 'mouse_click',
        'copy_ok', 'copy_bad', 'paste_ok', 'paste_bad'
       ]

COLORS = ["444", "F00", "FF0", "0F0", "0FF", "00F", "F0F", "CCC"]

def display():
    """Create the admin home page"""
    document.title = "C5 " + COURSE
    students = []
    for student in STUDENTS:
        students.append(student)
    students.sort()
    sums = {}
    for what in WHAT:
        sums[what] = ''
    text = ["""<!DOCTYPE html>
<style>
TABLE { border-spacing: 0px; border-collapse: collapse }
TABLE TD { vertical-align: top; border: 1px solid #888; padding: 0px}
TEXTAREA { border: 0px; min-height:10em; font-size:60%; width:10em; height:100% }
BUTTON { width: 100% }
"""]
    for i, color in enumerate(COLORS):
        text.append(
            '.sec' + i + '{ display: inline-block; height: 1em; vertical-align: top;'
            + 'height: 1.3em; background: #' + color + '}')
    text.append("""
</style>
<table border>
    <tr><th>Login<th colspan="2">Questions<br>Validated<th>Keys
        <th>Mouse<th>Copy<th>Copy<br>Fail<th>Paste<th>Paste<br>Fail<th>Time per question<th>Files</tr>
""")
    cache = {}
    max_time = 600
    question_times = []
    for login in students:
        student = STUDENTS[login]
        cache[login] = analyse(student.http_server)
        full_time = sum(cache[login]['time_sum'])
        if full_time > max_time:
            max_time = full_time
    for login in students:
        student = STUDENTS[login]
        stats = cache[login]
        text.append('<tr><td>')
        text.append(login)
        text.append('<td>')
        text.append(stats['questions'])
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'

        text.append('<td>')
        for i, seconds in enumerate(stats['time_sum']):
            text.append('<span style="width:' + (600*seconds)/max_time
                        + 'px" class="sec' + i % len(COLORS) + '"></span>')
            if not question_times[i]:
                question_times[i] = []
            question_times[i].append(seconds)
        text.append('<td>')
        for filename in student.files:
            text.append(' <a target="_blank" href="adm_get/' + COURSE + '/')
            text.append(login)
            text.append('/')
            text.append(filename)
            text.append(window.location.search)
            text.append('">')
            text.append(filename)
            text.append('</a>')
    text.append('<tr><td><td>')
    for what in WHAT:
        text.append('<td><textarea>' + sums[what] + '</textarea>')
        if what == 'nr_answered':
            text.append('''
            <br>
            <button onclick="window.location.pathname = 'adm_answers/' + COURSE + '.zip'"
            >Sources<br>txt ZIP</button>''')
    text.append('<td><table style="font-size: 60%">')
    text.append('<tr><th>Question<th>Min<th>Average<th>Median<th>Max</tr>')
    for i, times in enumerate(question_times):
        times.sort()
        text.append('<tr><td>' + (i+1)
                    + '<td>' + min(times)
                    + '<td>' + Math.floor(sum(times)/len(times))
                    + '<td>' + times[Math.floor(len(times)/2)]
                    + '<td>' + max(times)
                    + '</tr>')
    text.append('</table></tr>')
    text.append('</table>')
    document.body.innerHTML = text.join('') # pylint: disable=no-member

display()
