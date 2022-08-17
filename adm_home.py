"""Home page for the C5 administrator"""

try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    COURSES = COURSES
    MORE = MORE
    LOGIN = LOGIN
    CONFIG = CONFIG
    history = history
    RegExp = RegExp
    encodeURIComponent = encodeURIComponent
    document = document
except ValueError:
    pass


def update_url():
    """Hide the last action from URL"""
    url = location.toString() # pylint: disable=undefined-variable
    clean = url.replace(RegExp('(.*)/(adm|upload).*([?]ticket=.*)'), "$1/adm/home$3")
    history.replaceState('_a_', '_t_', clean)

def html(txt):
    """Escape < > &"""
    # pylint: disable=undefined-variable
    return txt.replace(RegExp('&', 'g'), '&amp;'
                      ).replace(RegExp('<', 'g'), '&lt;').replace(RegExp('>', 'g'), '&gt;')

def display(): # pylint: disable=too-many-statements
    """Display adm home page"""
    update_url()
    text = [
        '<title>C5 Administration</title>',
        MORE,
        '''
    <h1>C5 Administration</h1>
    <style>
        TABLE { border-spacing: 0px; border-collapse: collapse ; }
        TABLE TD { border: 1px solid #888; padding: 0px }
        TABLE TD > INPUT { margin: 0.5em ; margin-right: 0px }
        TABLE TD TEXTAREA { border: 0px; height: 4em }
        TT, PRE, INPUT { font-family: monospace, monospace; font-size: 100% }
        TD BUTTON {
            margin: 1px ; height: 2.5em; vertical-align: top;
            font-size: 100% ;
            }
        LABEL { display: block }
        .done { background: #FDD }
        .running { background: #DFD }
        .running_tt { background: #FEB }
        .more { border: 1px solid black ; background: #FFE;
                padding: 0.3em ; margin: 0.1em ;
                float: right;
              }
        TD INPUT[type=submit], TD INPUT[type=file] { margin: 0px }
        BODY > TEXTAREA { width: 100%; height: 10em }
    </style>
    <p>
    Colors:
        <span class="done">The session is done</span>,
        <span class="running">The session is running</span>,
        <span class="running_tt">The session is running for tiers-temps</span>,
        <span>The session has not yet started</span>.
    <p>
    Changing the stop date will not update onscreen timers.
    <table>
    <tr><th>Course<br>Master<th>Logs<th>Try<th>Start<th>Stop<th>Options<th>TT logins
        <th>ZIP<th>Update<br>course source<th>Teachers</tr>
    ''']
    def add_button(url, label, name='', new_window=False):
        url = "'" + url + '?ticket=' + TICKET + "'"
        if new_window:
            action = 'window.open(' + url + ')'
        else:
            action = 'window.location = ' + url
        text.append('<button onclick="' + action + '" class="' + name + '">'
            + label + '</button>')
    def add_input(url, value, name='', disable=False):
        text.append(
            '<input onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'"'
            + ' value="' + value + '" class="' + name + '"'
            + (disable and ' disabled' or '')
            + '>')
    def add_toggle(url, value, label, disable=False):
        text.append(
            '<label><input type="checkbox" onchange="window.location = \''
            + url + "'+(this.checked ? 1 : 0)+" + '\'?ticket=' + TICKET + '\'"'
            + ((value == '1') and ' checked' or '')
            + (disable and ' disabled' or '')
            + '>' + label + '</label>')
    def add_textarea(url, value, disable=False):
        text.append(
            '<textarea onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'" '
            + (disable and ' disabled' or '')
            + '>'
            + html(value) + '</textarea>')
    def form(content, disable):
        value = (
            '<form id="upload_course" method="POST" enctype="multipart/form-data" '
            + 'action="/upload_course?ticket=' + TICKET + '">'
            + '<input type="file" name="course">'
            + content
            + '</form>')
        if disable:
            value = value.replace(RegExp("input ", "g"), "input disabled ")
        text.append(value)

    for course in COURSES:
        i_am_a_teacher = LOGIN in course.teachers.replace('\n', ' ').split(' ')
        text.append('<tr class="' + course.status + ' ' + course.course.replace('=','_') + '"><td>')
        text.append(course.course.replace('=', '<br><b>'))
        text.append('</b>')
        text.append('<td>')
        if course.logs:
            add_button('/adm/course/' + course.course, 'Logs', '', True)
        text.append('<td>')
        add_button('=' + course.course, 'Try', '', True)
        text.append('<td>')
        add_input('/adm/config/' + course.course + '/start/', course.start)
        if course.status != 'running':
            add_button('/adm/config/' + course.course + '/start/now', 'Now')
        text.append('<td>')
        add_input('/adm/config/' + course.course + '/stop/', course.stop)
        if course.status != 'done':
            add_button('/adm/config/' + course.course + '/stop/now', 'Now')
        text.append('<td>')
        add_toggle('/adm/config/' + course.course + '/copy_paste/', course.copy_paste, 'Copy/Paste')
        label = 'Checkpoint'
        if course.checkpoint != '0': # and i_am_a_teacher:
            label = ('<a href="/checkpoint/' + course.course
                     + '?ticket=' + TICKET + '">' + label + '</a>')
        add_toggle('/adm/config/' + course.course + '/checkpoint/', course.checkpoint,
                   label, disable=not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/tt/', course.tt)
        text.append('</textarea><td>')
        if course.logs:
            add_button('/adm/get/COMPILE_' + course.course.replace('=', '/') + '.zip', 'ZIP')
        text.append('<td>')
        form(
            '<div><input type="submit" value="Replace «' + course.course + '.py»'
            + '" name="replace"></div>',
            not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/teachers/', course.teachers,
                     disable=not i_am_a_teacher)
        text.append('</tr>\n')
    text.append('</table><p>')
    form('<input type="submit" value="Add a new course">', False)
    text.append('<hr>')
    text.append('Masters: ')
    for master in CONFIG.masters:
        add_button('/adm/c5/del_master/' + master, '🗑',
                   name='del_master_' + master.replace('.', '_')) # For regtests
        text.append(' ' + master + ', ')
    add_input('/adm/c5/add_master/', '', name="add_master")
    text.append('<hr>')
    text.append('Session ticket time to live in seconds: ')
    add_input('/adm/c5/ticket_ttl/', CONFIG.ticket_ttl, name="ticket_ttl")
    text.append(' ')
    add_button('/adm/c5/remove_old_tickets/0', 'Remove old tickets now', name="remove_olds")
    text.append('<hr>')
    content = []
    for room in CONFIG.ips_per_room:
        content.append(room + ' ' + CONFIG.ips_per_room[room])
    add_textarea('/adm/c5/ips_per_room/', '\n'.join(content))
    text.append('<hr>')
    text.append('It is a student if the login match regexp: ')
    add_input('/adm/c5/student/', CONFIG.student, name="student")
    document.body.innerHTML = text.join('') # pylint: disable=no-member


display()
