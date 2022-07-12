
STUDENTS = STUDENTS
COURSE = COURSE
document = document
window = window
isNaN = isNaN
Math = Math

MAX_WIDTH = 400
SNAIL = 4

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
    nr_blurs = 0
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
                elif cell.startswith('Blur'):
                    nr_blurs += 1
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
            text += '|'
            nr_answered += 1
        else:
            text += '·'
        if not time_sum[i]:
            time_sum[i] = 0
    return {'questions': text, 'key_stroke': key_stroke, 'mouse_click': mouse_click,
            'copy_bad': copy_bad, 'copy_ok': copy_ok,
            'paste_bad': paste_bad, 'paste_ok': paste_ok,
            'nr_answered': nr_answered,
            'nr_blurs': nr_blurs,
            'time_sum': time_sum,
           }

WHAT = ['nr_answered', 'time', 'key_stroke', 'mouse_click',
        'copy_ok', 'copy_bad', 'paste_ok', 'paste_bad', 'nr_blurs'
       ]

COLORS = ["888", "F44", "FF0", "0F0", "0FF", "88F", "F0F", "CCC"]

def display(): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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
TABLE TD { vertical-align: top; border: 1px solid #888; padding: 0px; white-space: pre}
TEXTAREA { border: 0px; min-height:10em; font-size:60%; width:10em; height:100% }
BUTTON { width: 100% }
E { font-family: emoji }
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
    <tr><th>Login<th colspan="2">Questions<br>Validated<th>Time<br>in sec.<th>Keys
        <th>Mouse<th>Copy<th>Copy<br>Fail<th>Paste<th>Paste<br>Fail<th>Window<br>Blur<th>Time per question<br>
        <E>🐌</E> : clipped to """ + SNAIL + """ times the median answer time.<th>Files</tr>
""")
    cache = {}
    question_times = []
    for login in students:
        student = STUDENTS[login]
        cache[login] = analyse(student.http_server)
        for i, seconds in enumerate(cache[login]['time_sum']):
            if not question_times[i]:
                question_times[i] = []
            question_times[i].append(seconds)
    question_medians = []
    for i, times in enumerate(question_times):
        times.sort()
        middle = Math.floor(len(times) // 2)
        if len(times) % 2 == 1:
            median = times[middle]
        else:
            median = (times[middle-1] + times[middle]) / 2
        question_medians[i] = median
    max_time = Math.max(MAX_WIDTH, sum(question_medians))

    for login in students:
        student = STUDENTS[login]
        stats = cache[login]
        text.append('<tr><td>')
        text.append(login)
        text.append('<td>')
        text.append(stats['questions'])
        stats['time'] = sum(stats['time_sum'])
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'

        text.append('<td>')
        for i, seconds in enumerate(stats['time_sum']):
            if seconds > question_medians[i] * SNAIL:
                seconds = question_medians[i] * SNAIL
                more = '<E>🐌</E>'
            else:
                more = ''
            text.append('<span style="width:' + (MAX_WIDTH*seconds)/max_time
                        + 'px" class="sec' + i % len(COLORS) + '">' + more + '</span>')
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
    text.append('''
<tr><td><td>Sources:
<button onclick="window.location.pathname = 'adm_answers/0/' + COURSE + '.zip'"
>Validated questions<br>txt ZIP</button>
<button onclick="window.location.pathname = 'adm_answers/1/' + COURSE + '.zip'"
>Saved questions<br>txt ZIP</button>
''')
    for what in WHAT:
        text.append('<td><textarea>' + sums[what] + '</textarea>')
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
    document.body.innerHTML = text.join('') # pylint: disable=no-member

display()
