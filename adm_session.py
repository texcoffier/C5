"""
Page to configure a session
"""

THEMES = "a11y-dark a11y-light agate an-old-hope androidstudio arduino-light arta ascetic atom-one-dark-reasonable atom-one-dark atom-one-light brown-paper codepen-embed color-brewer dark default devibeans docco far felipec foundation github-dark-dimmed github-dark github gml googlecode gradient-dark gradient-light grayscale hybrid idea intellij-light ir-black isbl-editor-dark isbl-editor-light kimbie-dark kimbie-light lightfair lioshi magula mono-blue monokai-sublime monokai night-owl nnfx-dark nnfx-light nord obsidian panda-syntax-dark panda-syntax-light paraiso-dark paraiso-light pojoaque purebasic qtcreator-dark qtcreator-light rainbow routeros school-book shades-of-purple srcery stackoverflow-dark stackoverflow-light sunburst tokyo-night-dark tokyo-night-light tomorrow-night-blue tomorrow-night-bright vs vs2015 xcode xt256" # pylint: disable=line-too-long

State = {
    'selected_tab': None,
    'config': {},
    'original_value': {}
}

def add(element):
    """Add an element to the document BODY"""
    document.body.appendChild(element)

def load_config():
    """Retrieve the current configuration"""
    script = document.createElement('SCRIPT')
    script.src = '/course_config/' + COURSE + '?ticket=' + TICKET
    add(script)
    select_tab('Config')

def do_grade(login):
    """Open the window to grade the student"""
    window.open('/grade/' + COURSE + '/' + login + '?ticket=' + TICKET)

def update_course_config(config, feedback): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Update the HTML with the configuration.
    This function is called by server answer.
    """
    State.config = config
    if len(State.original_value) == 0:
        for attr in config:
            State.original_value[attr] = config[attr]
    for attr in config: # pylint: disable=too-many-nested-blocks
        value = config[attr]
        if attr == 'highlight':
            attr = value # One element ID per radio button
            value = 1
        element = document.getElementById(attr)
        if element:
            if element.tagName != 'DIV':
                if JSON.stringify(value) == JSON.stringify(State.original_value[attr]):
                    class_name = ''
                else:
                    class_name = 'changed'
                if element.parentNode.tagName == 'LABEL' and element.tagName != 'SELECT':
                    element.parentNode.className = class_name
                else:
                    element.className = class_name
            if element.tagName == 'TEXTAREA':
                content = []
                if value.splice:
                    for val in value:
                        content.append('    ' + JSON.stringify(val))
                    element.value = '[\n' + ',\n'.join(content) + '\n]'
                elif value.toLowerCase:
                    element.value = value
                    content = "overrided by style"
                else:
                    for key in value:
                        content.append('    ' + JSON.stringify(key) + ':' + JSON.stringify(value[key]))
                    element.value = '{\n' + ',\n'.join(content) + '\n}'
                if attr not in ('admins', 'graders', 'proctors', 'expected_students', 'expected_students_required', 'tt'):
                    element.rows = len(content) + 3
                if attr == 'expected_students':
                        document.getElementById("nr_expected_students").innerHTML = count_words('expected_students')
                if attr == 'tt':
                    document.getElementById("nr_tt").innerHTML = count_words('tt')
            elif element.tagName == 'INPUT':
                if element.type in ('checkbox', 'radio'):
                    element.checked = value != 0
                else:
                    if not value.toLowerCase:
                        value = JSON.stringify(value)
                    element.value = value
            elif element.tagName == 'SELECT':
                element.value = value
            elif attr == 'messages':
                content = []
                for message in value:
                    date = Date()
                    date.setTime(1000 * message[1])
                    date = str(date)[:24]
                    content.append('<p>' + date + ' '
                        + '<b>' + message[0] + '</b> ' + html(message[2]))
                element.innerHTML = ''.join(content)
            elif attr == 'active_teacher_room':
                content = [
                    '''<table class="students">
                       <tr>
                       <th>Student
                       <th>Closed
                       <th>Proctor
                       <th>Room
                       <th>Last student action
                       <th>#Blurs
                       <th>#Questions
                       <th>Last hostname
                       <th>Time bonus
                       <th>Grade,#items graded
                       </th>
                    ''']
                for login in value:
                    active, teacher, room, timestamp, nr_blurs, nr_questions, \
                        hostname, time_bonus, grade = value[login]
                    date = Date()
                    date.setTime(1000 * timestamp)
                    more = ''
                    if grade:
                        val = float(grade[0])
                        nice = grade[0]
                        if int(val) == val:
                            nice += '.0'
                        if val < 10:
                            nice = ' ' + nice
                        more += '\t' + nice + '[' + grade[1] + ']'
                    if time_bonus:
                        more += '⏱'
                    date = nice_date(date.getTime() / 1000)
                    # do_grade_login
                    content.append(
                        '<tr><td><span style="width:' + 2*nr_blurs + 'px"></span>'
                        + '<a target="_blank" href="/grade/' + COURSE + '/'
                        + login + '?ticket=' + TICKET + '">' + login + '</a>'
                        + '<td>' + active + '</td>'
                        + '<td>' + teacher + '</td>'
                        + '<td>' + room + '</td>'
                        + '<td>' + date + '</td>'
                        + '<td>' + nr_blurs + '</td>'
                        + '<td>' + nr_questions + '</td>'
                        + '<td>' + hostname + '</td>'
                        + '<td>' + time_bonus + '</td>'
                        + '<td>' + grade + '</td>'
                        + '</tr>')
                content.append('</table>')
                element.innerHTML = ''.join(content)
            else:
                element.innerHTML = value
    if config.start > config.stop:
        display = 'block'
    else:
        display = 'none'
    if document.getElementById('invalid_date'):
        document.getElementById('invalid_date').style.display = display

    update_course_config.div.style.display = 'block'
    if feedback:
        div = document.getElementById('server_feedback')
        div.innerHTML = feedback
        if feedback[-1] == '!':
            div.className = "error"
        else:
            div.className = ""

def upload():
    """Send the source file"""
    document.getElementById('server_feedback').innerHTML = """
    <iframe id="script" name="script"></iframe>"""
    file = document.getElementById('file')
    event = eval("new MouseEvent('click', {'view': window, 'bubbles': true, 'cancelable': true})") # pylint: disable=eval-used
    file.dispatchEvent(event)

def upload_media():
    """Send a media file"""
    document.getElementById('server_feedback').innerHTML = """
    <iframe id="script" name="script"></iframe>"""
    file = document.getElementById('media')
    event = eval("new MouseEvent('click', {'view': window, 'bubbles': true, 'cancelable': true})") # pylint: disable=eval-used
    file.dispatchEvent(event)

def do_submit(element):
    """Upload a course replacement"""
    element.parentNode.submit()

def onchange(event):
    """Send the change to the server"""
    target = event.target
    attr = target.id
    if target.type == 'radio':
        if not target.checked:
            return
        value = target.id
        attr = target.name
        target = target.parentNode
    elif not State.original_value[attr] and State.original_value[attr] != 0 and State.original_value[attr] != '':
        return
    else:
        if target.parentNode.tagName == 'LABEL' and target.tagName != 'SELECT':
            if target.checked:
                value = '1'
            else:
                value = '0'
            target = target.parentNode
        else:
            if target.id in ('tt', 'expected_students'):
                target.value = target.value.toLowerCase().replace(RegExp('\\b1', 'g'), 'p')
            value = target.value
    target.className = 'wait_answer'
    post('/adm/session/' + COURSE + '/' + attr + '?ticket=' + TICKET, value, True)
    event.stopPropagation()


def rename_session():
    """Rename the session"""
    name = prompt('New name?')
    if name and name != 'null':
        window.location = '/adm/session2/' + COURSE + '/rename/' + name + '?ticket=' + TICKET

def delete_all():
    """Delete everything"""
    if confirm('Really delete everything?'):
        window.location = '/adm/session2/' + COURSE + '/delete?ticket=' + TICKET

def delete_students():
    """Delete student logs"""
    if confirm('Really delete student logs?'):
        window.location = '/adm/session2/' + COURSE + '/delete_students?ticket=' + TICKET

def git_pull():
    """Pull source update from GIT"""
    window.location = '/adm/git_pull/' + COURSE + '?ticket=' + TICKET

def select_action(element):
    """Action on the select menu"""
    if element.selectedIndex > 0:
        eval(element.options[element.selectedIndex].getAttribute('action'))(element.parentNode)
    element.selectedIndex = 0

def load_min_zip():
    """Get all the session files"""
    window.location = ("/adm/get_exclude/LOGS session.cf questions.js questions.json/COMPILE_"
        + COURSE.replace('=', '/') + '.zip?ticket=' + TICKET)

def load_full_zip():
    """Get all the session files"""
    window.location = "/adm/get/COMPILE_" + COURSE.replace('=', '/') + '.zip?ticket=' + TICKET

def select_tab(label):
    """Select the tab to display"""
    new_tab = document.getElementById(label)
    if not new_tab:
        return # Action menu
    if State.selected_tab:
        State.selected_tab.className = ''
    State.selected_tab = new_tab
    State.selected_tab.className = "selected"

    if label == "Try A":
        content = '<iframe src="=' + COURSE + '/Va?ticket=' + TICKET + '"></iframe>'
    elif label == "Try B":
        content = '<iframe src="=' + COURSE + '/Vb?ticket=' + TICKET + '"></iframe>'
    elif label == "Place":
        content =  '<iframe src="/checkpoint/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == 'Edit':
        content = '<iframe src="/adm/editor/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == "Media":
        content = '<iframe src="/adm/media/' + COURSE + '/list/*?ticket=' + TICKET + '"></iframe>'
    elif label == 'Results':
        content = '<iframe src="/adm/course/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == 'Chat':
        content = '<div id="messages"></div>'
    elif label == 'Students':
        content = '<div id="active_teacher_room"></div>'
    elif label == 'Access':
        content = """
    <table class="access">
    <tr><th>Creator
        <td><p id="creator"></p>
    </tr>
    <tr><th>Admins
        <td><textarea id="admins"></textarea>
    </tr>
    <tr><th>Graders
        <td><textarea id="graders"></textarea>
    </tr>
    <tr><th>Proctors
        <td><textarea id="proctors"></textarea>
    </tr>
    <tr><th><span id="nr_expected_students"></span> Students (<label><input type="checkbox" id="expected_students_required">hide to others</label>)
        <td><textarea id="expected_students"></textarea>
    </tr>
    <tr><th><span id="nr_tt"></span> Students with ⅓ more time to answer
        <td><textarea id="tt"></textarea>
    </tr>
    </table>"""
    elif label == 'Grading':
        content = """
    <div style="display:grid; height: 100%; grid-template-rows: min-content auto">
    <div>
    Indicate the maximum grade (20 for example): <input id="notation_max" size="4">
    <p>
    Example of grading definition for the «hello world» C program.<br>
    The grading part is right aligned and green with one button for each grade.
    <p>
    If the <b>exact text</b> found left to the '▶'
    is found in the student source code,<br>
    then '▶' is blue and clickable to scroll the source code to the first matching line.
    </p>
    <p>
    If the grading part is «{printf:SomeKey:0,1,2,3}» then «SomeKey» will be
    hidden to the grader but used to compute the competence export table
    for TOMUSS. <b>If it is a competence the value will not be used to compute the grade</b>.
    <pre>
#include &lt;stdio.h&gt;               {stdio.h:0,1}
int main()▶                      {main declaration:0,1}
{                                {bloc:0,1}
   printf("Hello World\\n");      {printf:0,0.5,1,1.5,2}
}
// Malus                         {No comments:-1,0}
</pre>
<b>Indicate your session gradings here,</b>
A subject and B subject if they are different.
(Grading sum : <span id="grading_sum" style="background: #0F0"></span>):
</div>
    <div style="display: flex"><textarea id="notation" style="flex:1"></textarea> <textarea id="notationB" style="flex:1"></textarea></div>"""
    elif label == 'Config':
        content = ["""
    <div style="height: 100%; display: grid">
    <div></div>
    """]
        content.append('<div style="align-self:stretch; overflow:scroll">')
        content.append('<table style="width:100%">')
        for line in DEFAULT_COURSE_OPTIONS:
            if len(line) != 3:
                if line == "Access tab":
                    break
                content.append('<tr><td colspan="2"><h2>' + line + '</h2></tr>')
                continue
            key, default_value, comment = line
            if key in ('feedback', 'default_building', 'theme', 'state'):
                if key == 'feedback':
                    choices = FEEDBACK_LEVEL.Items()
                elif key == 'default_building':
                    choices = [[val, val] for val in BUILDINGS]
                elif key == 'theme':
                    choices = [[val, val] for val in THEMES.split(' ')]
                else:
                    choices = [[val, val] for val in "Draft Ready Grade Done Archive".split(' ')]
                tag = ['<select id="', key, '">']
                for i, name in choices:
                    tag.append('<option value="' + i + '">' + name + '</option>')
                tag.append('</select>')
                tag = ''.join(tag)
                comment = '<div style="float:right">' + comment + '</div>'
            elif key == 'highlight':
                tag = []
                for color in ['#FFF', '#CCC',
                            '#AFA', '#0F0', '#CCF', '#88F', '#FBB', '#F66',
                            '#FF8', '#EE0', '#8FF', '#0EE', '#FAF', '#F5F']:
                    tag.append('<span style="background:' + color + '">'
                        + ' <input type="radio" name="highlight" id="' + color + '"> </span>')
                tag = ''.join(tag)
                comment = '<div style="float:right">' + comment + '</div>'
            elif default_value in (0, 1):
                tag = ('<label><input type="checkbox" id="' + key + '">'
                    + comment + '</label>')
                comment = ''
            else:
                if isinstance(default_value, Object):
                    tag = ('<textarea style="width: 100%" id="' + key + '"></textarea>')
                else:
                    tag = '<input style="width: 100%" id="' + key + '">'
                comment = '<div style="float:right">' + comment + '</div>'
            content.append(
                '<tr><td style="width: 30em"><tt>' + key + '</tt>' + comment + '<td>' + tag + '</tr>')
        content.append('</table></div>')
        content = ''.join(content)
    else:
        content = ''

    document.getElementById('content').innerHTML = content
    if len(State.original_value):
        update_course_config(State.config, '')

def init():
    """Create the HTML"""
    div = document.createElement('DIV')
    div.style.display = 'none'
    update_course_config.div = div

    div.onchange = onchange
    title = html(COURSE.replace('=', '   '))
    if title.startswith('^'):
        title = '<span style="background: #F00; color: #FFF">' + title + ' (session set)</span>'
    div.innerHTML = ('<h1 style="display: flex"><span>' + title + """</span>
     <div id="server_feedback">Problems and server feedbacks will be written here.</div>
    </h1>
    <title>""" + html(COURSE.replace(RegExp('.*=', ''), ' ')) + """</title>
    <link rel="stylesheet" href="/adm_session.css?ticket=""" + TICKET + """">
    <div id="tabs" onclick="select_tab(event.target.id)">
    <div id="Config">Config</div>
    <div id="Access">Access</div>
    <div id="Edit">Source</div>
    <div id="Media">Media</div>
    <div id="Try A">Try A</div>
    <div id="Try B">Try B</div>
    <div id="Place">Place</div>
    <div id="Chat">Chat</div>
    <div id="Students">Students</div>
    <div id="Grading">Grading</div>
    <div id="Results">Export/Stats</div>
    <select onchange="select_action(this)" style="vertical-align: top;">
    <option>Actions</option>
    <option action="upload">Upload a new source</option>
    <option action="upload_media">Upload a new media</option>
    <option action="rename_session">Rename session</option>
    <option action="delete_all">Delete <b>ALL</b></option>
    <option action="delete_students">Delete <b>Students</b></option>
    <option action="load_min_zip">Load ZIP question+media</option>
    <option action="load_full_zip">Load ZIP question+media+logs</option>
    <option action="git_pull">GIT pull</option>
    </select>
    </div>
    <div id="content"></div>
    <form method="POST" enctype="multipart/form-data" style="display:none" target="script"
          action="/upload_course/""" + COURSE.replace('=', '/') + "?ticket=" + TICKET + """">
          <input id="file" type="file" name="course" onchange="do_submit(this)">
    </form>
    <form method="POST" enctype="multipart/form-data" style="display:none" target="script"
          action="/upload_media/""" + COURSE.replace('=', '/') + "?ticket=" + TICKET + """">
          <input id="media" type="file" name="course" onchange="do_submit(this)">
    </form>
    """)
    add(div)
    setTimeout(load_config, 10) # Wait CSS loading
    setInterval(update_interface, 1000)

def count_words(element_id):
    text = document.getElementById(element_id).value.strip()
    if len(text) == 0:
        return ''
    words = text.split(RegExp('[ \t\n\r]+'))

    uniq = {}
    for word in words:
        uniq[word] = True
    message = str(len(uniq))
    if len(uniq) != len(words):
        message = ('<tt style="background:#F88; font-size:200%">'
                   + (len(words) - len(uniq)) + ' duplicate student</tt><br>'
                   + message)
    return message

def update_interface():
    """Update grading"""
    grading_sum = document.getElementById('grading_sum')
    notation = document.getElementById("notation")
    notationB = document.getElementById("notationB")
    if grading_sum and notation:
        total = 0
        for _text1, _text2, grades in parse_notation(notation.value):
            if len(grades):
                total += Number(grades[-1])
        total2 = 0
        for _text1, _text2, grades in parse_notation(notationB.value):
            if len(grades):
                total2 += Number(grades[-1])
        if total == total2 or total2 == 0:
            grading_sum.innerHTML = total
        else:
            grading_sum.innerHTML = '<span style="background:#F88">' + total + '/' + total2 + '</span>'

    required = document.getElementById("expected_students_required")
    expected_students = document.getElementById("expected_students")
    if required and expected_students:
        if required.checked and expected_students.value.trim() == '':
            required.parentNode.style.background = "#F00"
        else:
            required.parentNode.style.background = "#FFF"
init()
