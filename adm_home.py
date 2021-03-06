TICKET = TICKET
COURSES = COURSES
MORE = MORE
LOGIN = LOGIN
CONFIG = CONFIG
history = history
RegExp = RegExp
encodeURIComponent = encodeURIComponent
document = document

def update_url():
    """Hide the last action from URL"""
    url = location.toString() # pylint: disable=undefined-variable
    clean = url.replace(RegExp('(.*)/(adm|upload)_.*([?]ticket=.*)'), "$1/adm_home$3")
    history.replaceState('_a_', '_t_', clean)

def display():
    """Display adm home page"""
    update_url()
    action = location.toString().replace('adm_home', 'upload_course')
    text = ['''
    <title>C5 Administration</title>
    <h1>C5 Administration</h1>
    <style>
        TABLE { border-spacing: 0px; border-collapse: collapse ; }
        TABLE TD { border: 1px solid #888; padding: 0px }
        TABLE TD INPUT { margin: 0.5em ; margin-right: 0px }
        TABLE TD TEXTAREA { border: 0px; height: 4em }
        TT, PRE, INPUT { font-family: monospace, monospace; font-size: 100% }
        TD BUTTON {
            margin: 1px ; height: 2.5em; vertical-align: top;
            font-size: 100% ;
            }
        .done { background: #FDD }
        .running { background: #DFD }
        .running_tt { background: #FEB }
        .more { font-size: 150% ; border: 1px solid black ; background: #FFE;
                padding: 1em ; margin: 1em
              }
        TD INPUT[type=submit], TD INPUT[type=file] { margin: 0px }
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
    <tr><th>Course<br>Master<th>Logs<th>Try<th>Start<th>Stop<th>TT logins
        <th>ZIP<th>Update<br>course source</tr>
    ''']
    def add_button(url, label, name=''):
        text.append(
            '<button onclick="window.location = \'' + url + '?ticket=' + TICKET
            + '\'" class="' + name + '">'
            + label + '</button>')
    def add_input(url, value, name=''):
        text.append(
            '<input onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'"'
            + ' value="' + value + '" class="' + name + '">')
    def add_textarea(url, value):
        text.append(
            '<textarea onchange="window.location = \''
            + url + "'+encodeURIComponent(this.textContent)+" + '\'?ticket=' + TICKET + '\'">'
            + encodeURIComponent(value) + '</textarea>')
    def form(content, disable):
        value = (
            '<form id="upload_course" method="POST" enctype="multipart/form-data" action="'
            + action + '">'
            + '<input type="file" name="course">'
            + content
            + '</form>')
        if disable:
            value = value.replace(RegExp("input ", "g"), "input disabled ")
        text.append(value)

    for course in COURSES:
        text.append('<tr class="' + course.status + ' ' + course.course.split('.')[0] + '"><td><b>')
        text.append(course.course)
        text.append('</b><br>')
        text.append(course.master)
        text.append('<td>')
        if course.logs:
            add_button('adm_course=' + course.course, 'Logs')
        text.append('<td>')
        add_button('=' + course.course + '.js', 'Try')
        text.append('<td>')
        add_input('adm_config=' + course.course + '=start:', course.start)
        if course.status != 'running':
            add_button('adm_config=' + course.course + '=start', 'Now')
        text.append('<td>')
        add_input('adm_config=' + course.course + '=stop:', course.stop)
        if course.status != 'done':
            add_button('adm_config=' + course.course + '=stop', 'Now')
        text.append('<td>')
        add_textarea('adm_config=' + course.course + '=tt:', course.tt)
        text.append('</textarea><td>')
        if course.logs:
            add_button('adm_get/' + course.course + '.zip', 'ZIP')
        text.append('<td>')
        form(
            '<div><input type="submit" value="Replace ??'
            + course.course + '.js??'
            + '" name="replace"></div>',
            LOGIN != course.master)
        text.append('</tr>\n')
    text.append('</table><p>')
    form('<input type="submit" value="Add a new course">', False)
    text.append('<hr>')
    text.append('Masters: ')
    for master in CONFIG.masters:
        add_button('adm_c5=del_master=' + master, '????',
                   name='del_master_' + master.replace('.', '_')) # For regtests
        text.append(' ' + master + ', ')
    add_input('adm_c5=add_master=', '', name="add_master")
    text.append('<hr>')
    text.append('Session ticket time to live in seconds: ')
    add_input('adm_c5=ticket_ttl=', CONFIG.ticket_ttl, name="ticket_ttl")
    text.append(' ')
    add_button('adm_c5=remove_old_tickets=0', 'Remove old tickets now', name="remove_olds")
    text.append('<hr>')
    text.append(MORE)
    document.body.innerHTML = text.join('')


display()
