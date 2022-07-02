
STUDENTS = STUDENTS
COURSE = COURSE
document = document
window = window


def analyse(http_server):
    """Extract statistiques from log"""
    answered = []
    key_stroke = 0
    mouse_click = 0
    copy_bad = 0
    copy_ok = 0
    paste_bad = 0
    paste_ok = 0
    nr_answered = 0
    last = -1
    for line in http_server.split('\n'):
        if len(line) == 0:
            continue
        line = eval(line) # pylint: disable=eval-used
        for cell in line[1:]:
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
            if cell[0] == 'answer':
                answered[cell[1]] = cell[2]
                if cell[1] > last:
                    last = cell[1]
    text = ''
    for i in range(last+1):
        if answered[i]:
            text += '*'
            nr_answered += 1
        else:
            text += '·'
    return {'questions': text, 'key_stroke': key_stroke, 'mouse_click': mouse_click,
            'copy_bad': copy_bad, 'copy_ok': copy_ok,
            'paste_bad': paste_bad, 'paste_ok': paste_ok,
            'nr_answered': nr_answered
           }

WHAT = ['nr_answered', 'key_stroke', 'mouse_click',
        'copy_ok', 'copy_bad', 'paste_ok', 'paste_bad'
       ]

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
    text = [
        '<table border><tr><th>Login<th colspan="2">Questions<th>Keys',
        '<th>Mouse<th>Copy<th>Copy<br>Fail<th>Paste<th>Paste<br>Fail<th>Files</tr>']
    for login in students:
        student = STUDENTS[login]
        stats = analyse(student.http_server)
        text.append('<tr><td>')
        text.append(login)
        text.append('<td>')
        text.append(stats['questions'])
        for what in WHAT:
            text.append('<td>')
            text.append(stats[what])
            sums[what] += login + '\t' + stats[what] + '\n'

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
        text.append('<td><textarea style="font-size:60%;width:10em;height:8em">'
                    + sums[what] + '</textarea>')
    text.append('</tr>')
    text.append('</table>')
    document.body.innerHTML = text.join('')

display()
