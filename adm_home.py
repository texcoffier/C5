"""Home page for the C5 administrator"""

try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    COURSES = COURSES
    MORE = MORE
    LOGIN = LOGIN
    CONFIG = CONFIG
    HOME = HOME
    history = history
    RegExp = RegExp
    encodeURIComponent = encodeURIComponent
    document = document
    setTimeout = setTimeout
    html = html
except ValueError:
    pass


def update_url():
    """Hide the last action from URL"""
    url = location.toString() # pylint: disable=undefined-variable
    clean = url.replace(RegExp('(.*)/(adm|upload).*([?]ticket=.*)'), "$1/adm/" + HOME + "$3")
    history.replaceState('_a_', '_t_', clean)

def display(): # pylint: disable=too-many-statements
    """Display adm home page"""
    update_url()
    text = [
        '<title>Administration</title>',
        MORE,
        '''
    <h1>Administration</h1>
    <style>
        BODY { font-family: sans-serif }
        TABLE { border-spacing: 0px; border-collapse: collapse ; }
        TABLE TD { border: 1px solid #888; padding: 0px; white-space: nowrap }
        TABLE TD > INPUT { margin: 0.5em ; margin-right: 0px }
        INPUT.start_date {margin-top: 0.2em; margin-bottom: 0.1em }
        INPUT.stop_date { margin-top: 0.1em; margin-bottom: 0.2em }
        BUTTON.start_date, BUTTON.stop_date { height: 1.55em }
        BUTTON.start_date { margin-top: 0.2em }
        BUTTON.stop_date { margin-top: 0.1em }
        BUTTON.edit { float: right }
        TABLE TD TEXTAREA { border: 0px; height: 3.5em; margin-bottom: 0px;
                            font-family: monospace,monospace }
        TABLE TD TEXTAREA.tt { width: 5em }
        TT, PRE, INPUT { font-family: monospace, monospace; font-size: 100% }
        TD BUTTON {
            margin: 1px ; height: 2.5em; vertical-align: top;
            font-size: 100% ;
            }
        LABEL { display: inline-block }
        .done { background: #FDD }
        .running { background: #DFD }
        .running_tt { background: #FEB }
        #more { border: 1px solid black ; background: #FFE;
                padding: 0.3em ; margin: 0.1em ;
                position: absolute;
                right: 0px;
                top: 0px;
                transform: scale(5, 5);
                transform-origin: top right;
                transition: transform 1s
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
    <tr><th>Compiler<br>Session<th>Logs<th>Try
        <th>Start date/time<br>Stop date/time<th>Options<th>TT<br>logins
        <th>full<br>ZIP<th>Update<br>course source<th>Creator<th>Admins<th>Graders<th>Proctors
        <th>Highlight<br>theme<th>Notation
        </tr>
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
    def add_textarea(url, value, disable=False, name=''):
        text.append(
            '<textarea onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'" '
            + (disable and ' disabled' or '')
            + (name and ' class="' + name + '"' or '')
            + '>'
            + html(value) + '</textarea>')
    def form(replace, disable):
        value = (
            '<form id="upload_course" method="POST" enctype="multipart/form-data" '
            + 'action="/upload_course/' + replace + '?ticket=' + TICKET + '">'
            + '<input type="file" name="course" onchange="this.parentNode.submit()">'
            + '</form>')
        if disable:
            value = value.replace(RegExp("input ", "g"), "input disabled ")
        text.append(value)

    for course in COURSES:
        i_am_a_teacher = LOGIN == course.creator or LOGIN in course.admins.replace('\n', ' ').split(' ')
        text.append('<tr class="' + course.status + ' '
                    + course.course.replace('=', '_') + '"><td>')
        text.append(course.course.replace('=', '<br><b>'))
        text.append('</b>')
        text.append('<td>')
        if course.logs:
            add_button('/adm/course/' + course.course, 'Logs', '', True)
        text.append('<td>')
        add_button('=' + course.course, 'Try', '', True)
        text.append('<td>')
        add_input('/adm/config/' + course.course + '/start/', course.start, 'start_date')
        if course.status != 'running':
            add_button('/adm/config/' + course.course + '/start/now', 'Now', 'start_date')
        text.append('<br>')
        add_input('/adm/config/' + course.course + '/stop/', course.stop, 'stop_date')
        if course.status != 'done':
            add_button('/adm/config/' + course.course + '/stop/now', 'Now', 'stop_date')
        text.append('<td>')
        add_toggle('/adm/config/' + course.course + '/copy_paste/', course.copy_paste, 'Copy/Paste')
        add_toggle('/adm/config/' + course.course + '/coloring/', course.coloring, 'Coloring')
        text.append('<br>')
        label = ('<a target="_blank" href="/checkpoint/' + course.course
                 + '?ticket=' + TICKET + '">Checkpoint</a>')
        add_toggle('/adm/config/' + course.course + '/checkpoint/', course.checkpoint,
                   label, disable=not i_am_a_teacher)
        add_toggle('/adm/config/' + course.course + '/highlight/', course.highlight,
                   'Highlight', disable=not i_am_a_teacher)
        text.append('<br>')
        add_toggle('/adm/config/' + course.course + '/sequential/', course.sequential,
                   'Sequential', disable=not i_am_a_teacher)
        add_toggle('/adm/config/' + course.course + '/save_unlock/', course.save_unlock,
                   'Save→Unlock', disable=not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/tt/', course.tt, not i_am_a_teacher, 'tt')
        text.append('<td>')
        if course.logs:
            add_button('/adm/get/COMPILE_' + course.course.replace('=', '/') + '.zip', 'ZIP')
        text.append('<td>')
        form(course.course, not i_am_a_teacher)
        add_button('/adm/editor/' + course.course, 'Edit', 'edit', True)
        text.append('<td>')
        text.append(course.creator)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/admins/', course.admins,
                     disable=not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/graders/', course.graders,
                     disable=not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/proctors/', course.proctors,
                     disable=not i_am_a_teacher)
        text.append('<td>')
        add_input('/adm/config/' + course.course + '/theme/', course.theme,
                  disable=not i_am_a_teacher)
        text.append('<td>')
        add_textarea('/adm/config/' + course.course + '/notation/', course.notation, not i_am_a_teacher, 'notation')
        text.append('<td>')
        if i_am_a_teacher:
            add_button('/adm/config/' + course.course + '/delete/', '🗑')
        text.append('</tr>\n')
    text.append('</table><p>')
    text.append('''
        Add a new session, filename must be as «{JS|CPP|PYTHON|REMOTE|SQL|TEXT|LISP}=SESSION.py»
        for example «JS=foo_loop.py», the session name must not yet exists.''')
    form('', False)
    document.body.innerHTML = text.join('') # pylint: disable=no-member
    def anime():
        more = document.getElementById('more')
        if more:
            more.style.transform = 'scale(1,1)'
    setTimeout(anime, 100)

display()
