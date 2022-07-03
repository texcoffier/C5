
TICKET = TICKET
COURSES = COURSES
MORE = MORE
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
    text = ['''
    <title>C5 Administration</title>
    <h1>C5 Administration</h1>
    <style>
        TABLE { border-spacing: 0px; border-collapse: collapse ; }
        TABLE TD { border: 1px solid #888; padding: 0px }
        TABLE TD INPUT { margin: 0.5em ; margin-right: 0px }
        TABLE TD TEXTAREA { border: 0px; height: 4em }
        TT, PRE, INPUT { font-family: monospace, monospace; font-size: 100% }
        BUTTON { margin-left: 5px ; margin-right: 5px; height: 3em }
        .done { background: #FDD }
        .running { background: #DFD }
        .running_tt { background: #FEB }
        .more { font-size: 150% ; border: 1px solid black ; background: #FFE;
                padding: 1em ; margin: 1em
              }
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
    <tr><th>Course<th>Master<th>Logs<th>Try<th>Start<th>Stop<th>TT logins<th>ZIP</tr>
    ''']
    def add_button(url, label):
        return text.append(
            '<button onclick="window.location = \'' + url + '?ticket=' + TICKET + '\'">'
            + label + '</button>')
    def add_input(url, value):
        return text.append(
            '<input onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'"'
            + ' value="' + value + '">')
    def add_textarea(url, value):
        return text.append(
            '<textarea onchange="window.location = \''
            + url + "'+encodeURIComponent(this.textContent)+" + '\'?ticket=' + TICKET + '\'">'
            + encodeURIComponent(value)) + '</textarea>'

    for course in COURSES:
        text.append('<tr class="' + course.status + '"><td><b>')
        text.append(course.course)
        text.append('</b><td>')
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
        text.append('</tr>\n')
    text.append('</table>')
    action = location.toString().replace('adm_home', 'upload_course')
    text.append('''
    <p>
    <form id="upload_course" method="POST" enctype="multipart/form-data" action="''' + action + '''">
    Upload a new course:
    <input type="file" name="course">
    <input type="submit">
    </form>
    ''' + MORE)
    document.body.innerHTML = text.join('')


display()
