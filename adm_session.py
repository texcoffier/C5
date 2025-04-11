"""
Page to configure a session
"""

THEMES = "a11y-dark a11y-light agate an-old-hope androidstudio arduino-light arta ascetic atom-one-dark-reasonable atom-one-dark atom-one-light brown-paper codepen-embed color-brewer dark default devibeans docco far felipec foundation github-dark-dimmed github-dark github gml googlecode gradient-dark gradient-light grayscale hybrid idea intellij-light ir-black isbl-editor-dark isbl-editor-light kimbie-dark kimbie-light lightfair lioshi magula mono-blue monokai-sublime monokai night-owl nnfx-dark nnfx-light nord obsidian panda-syntax-dark panda-syntax-light paraiso-dark paraiso-light pojoaque purebasic qtcreator-dark qtcreator-light rainbow routeros school-book shades-of-purple srcery stackoverflow-dark stackoverflow-light sunburst tokyo-night-dark tokyo-night-light tomorrow-night-blue tomorrow-night-bright vs vs2015 xcode xt256" # pylint: disable=line-too-long

State = {
    'selected_tab': None,
    'config': {},
    'original_value': {}
}

DEFAULT_COURSE_OPTIONS_DICT = {}

def add(element):
    """Add an element to the document BODY"""
    document.body.appendChild(element)

def load_config():
    """Retrieve the current configuration"""
    script = document.createElement('SCRIPT')
    script.src = BASE + '/course_config/' + COURSE + '?ticket=' + TICKET
    add(script)
    select_tab('Config')

def do_grade(login):
    """Open the window to grade the student"""
    window.open(BASE + '/grade/' + COURSE + '/' + login + '?ticket=' + TICKET)

def update_course_config(config, feedback): # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Update the HTML with the configuration.
    This function is called by server answer.
    """
    State.config = config
    if len(State['original_value']) == 0:
        for attr in config:
            State['original_value'][attr] = config[attr]
    for attr in config: # pylint: disable=too-many-nested-blocks
        value = config[attr]
        if attr == 'highlight':
            attr = value # One element ID per radio button
            value = 1
        element = document.getElementById(attr)
        if element:
            if element.tagName != 'DIV':
                if JSON.stringify(value) == JSON.stringify(State['original_value'][attr]):
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
                        content.append('    ' + JSON.stringify(key)
                                       + ':' + JSON.stringify(value[key]))
                    element.value = '{\n' + ',\n'.join(content) + '\n}'
                if attr not in ('admins', 'graders', 'proctors', 'expected_students', 'tt'):
                    element.rows = len(content) + 3
                if element.parentNode.parentNode.cells:
                    tt = element.parentNode.parentNode.cells[0].firstChild
                    if tt.className == 'counter':
                        tt.innerHTML, element.value = count_words(element)
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
                    '''
                    <style>TABLE.students TD:nth-child(2) { font-size: 50% }</style>
                    <table class="students">
                    <tr>
                    <th colspan="2">Student
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
                    infos = STUDENTS[login] or {'sn': '?', 'fn': '?'}
                    content.append(
                        '<tr><td><span style="width:' + 2*nr_blurs + 'px"></span>'
                        + '<a target="_blank" href="grade/' + COURSE + '/'
                        + login + '?ticket=' + TICKET + '">' + login + '</a>'
                        + '<td>' + infos.sn + '<br>' + infos.fn + '</td>'
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
    tree_menu =  document.getElementById('tree_menu')
    if tree_menu and tree_menu.contains(target):
        return
    attr = target.id
    if target.type == 'radio':
        if not target.checked:
            return
        value = target.id
        attr = target.name
        target = target.parentNode
    elif (not State['original_value'][attr]
          and State['original_value'][attr] != 0
          and State['original_value'][attr] != ''):
        return
    else:
        if target.parentNode.tagName == 'LABEL' and target.tagName != 'SELECT':
            if target.checked:
                value = '1'
            else:
                value = '0'
            target = target.parentNode
        else:
            value = target.value
    target.className = 'wait_answer'
    post(BASE + '/adm/session/' + COURSE + '/' + attr + '?ticket=' + TICKET, value, True)
    event.stopPropagation()

def nothing():
    """Do nothing"""
    return

def exam_mode(exam):
    """Modify parameters to be in examination mode of not"""
    i = 0
    for attr, value in [('checkpoint', 1), ('allow_copy_paste', 0),
                        ('forbid_question_copy', 1), ('allow_ip_change', 0)]:
        def do_later():
            """In a function so all the inputs have not the same value"""
            input = document.getElementById(attr)
            if exam:
                new_value = value == 1
            else:
                new_value = value == 0
            if input.checked == new_value:
                return nothing
            def fct():
                input.checked = new_value and True or False
                onchange({'target': input, 'stopPropagation': nothing})
            return fct
        setTimeout(do_later(), 200 * i)
        i += 1

def rename_session():
    """Rename the session"""
    name = prompt('New name?')
    if name and name != 'null':
        window.location = '/adm/rename/' + COURSE + '/' + name + '?ticket=' + TICKET

def git_pull():
    """Pull source update from GIT"""
    window.location = '/adm/git_pull/' + COURSE + '?ticket=' + TICKET

def force_grading_done():
    """Indicate that grading is done for all students with a complete grading."""
    window.location = '/adm/force_grading_done/' + COURSE + '?ticket=' + TICKET

def select_action(element):
    """Action on the select menu"""
    if element.selectedIndex > 0:
        eval(element.options[element.selectedIndex].getAttribute('action'))(element.parentNode)
    element.selectedIndex = 0

def select_tab(label):
    """Select the tab to display"""
    new_tab = document.getElementById(label)
    if not new_tab:
        return # Action menu
    if State['selected_tab']:
        State['selected_tab'].className = ''
    State['selected_tab'] = new_tab
    State['selected_tab'].className = "selected"

    if len(DEFAULT_COURSE_OPTIONS_DICT) == 0:
        for line in DEFAULT_COURSE_OPTIONS:
            if len(line) == 3:
                DEFAULT_COURSE_OPTIONS_DICT[line[0]] = line[2]

    if label == "Try A":
        content = '<iframe src="=' + COURSE + '/Va?ticket=' + TICKET + '"></iframe>'
    elif label == "Try B":
        content = '<iframe src="=' + COURSE + '/Vb?ticket=' + TICKET + '"></iframe>'
    elif label == "Place":
        content =  '<iframe src="checkpoint/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == 'Edit':
        content = '<iframe src="adm/editor/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == "Media":
        content = '<iframe src="adm/media/' + COURSE + '/list/*?ticket=' + TICKET + '"></iframe>'
    elif label == 'Results':
        content = '<iframe src="adm/course/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
    elif label == 'History':
        content = '<iframe src="adm/history/' + COURSE + '?ticket=' + TICKET + '"></iframe>'
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
    <tr><th><tt class="counter"></tt> Admins
        <td><textarea id="admins"></textarea>
    </tr>
    <tr><th><tt class="counter"></tt> Graders
        <td><textarea id="graders"></textarea>
    </tr>
    <tr><th><tt class="counter"></tt> Proctors
        <td><textarea id="proctors"></textarea>
    </tr>
    <tr><th><tt class="counter"></tt> Students
    <p>""" + DEFAULT_COURSE_OPTIONS_DICT['expected_students'] + """
        <td><textarea id="expected_students"></textarea>
    </tr>
    <tr><th><tt class="counter"></tt> Students
    <p>""" + DEFAULT_COURSE_OPTIONS_DICT['tt'] + """
        <td><textarea id="tt"></textarea>
    </tr>
    </table>"""
    elif label == 'Grading':
        content = """
    <div class="grading" style="display:grid; height: 100%; grid-template-rows: min-content auto">
    <div>
    <table><tr style="background:#F8F8F8"><td>
    <p>
    Example of grading definition for the «hello world» C program.<br>
    The grading part is right aligned with one button per grade.
    <pre>
#include &lt;stdio.h&gt;            {stdio.h:0,1}
int main()                    {main declaration:0,1}
{
   printf("Hello World\\n");   {printf:0,0.5,1,1.5,2}
}
// Malus                      {No comments:-1,0}
</pre>
    <p>
    Each grading definition line found in the student code<br>
    is clickable to scroll the student code to the right place.<br>
    To disable this, add a '▶' in the lines you want to be clickable.
    </p>
</td><td>
    <p>
    If the grading part is «{printf:Key:-1,-0.5,0,0.5,1,1.5,2}» then:
    </p>
    <ul>
    <li> «Key» will be automaticaly computed if there is none.</li>
    <li> «Key» uniquely identify the grade,<br>
        so it is possible to change the order
        of the grades without consequences.</li>
    <li> «Key» is not displayed to the graders.</li>
    <li> if «Key» is an integer, then the grade is a value positive or negative.</li>
    <li> if «Key» is not an integer then it is a competence key:
        <ul>
            <li> if the same competence is evaluated multiple times,<br>
            «'» are appended to the key to remove duplicates.</li>
            <li> «?» is for «Not Evaluated» and «0» for «Not Acquired».</li>
            <li> Competences are not used to compute the grade.</li>
        </ul></li>
    </ul>
</td></tr></table>

Grade maximum displayed to the students: <input id="notation_max" size="4">.
<div id="grading_sum" style="display: inline-block"></div>
<div style="width:100%; display:flex; text-align: center;"
><span style="flex:1">Gradings for session A</span> <span style="flex:1">Grading for session B if ≠ A</span></div>
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
            elif default_value in (0, 1) and key != 'max_time':
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
                '<tr><td style="width: 30em"><tt>' + key + '</tt>'
                + comment + '<td>' + tag + '</tr>')
        content.append('</table></div>')
        content = ''.join(content)
    elif label == 'Manage':
        content = '''
<div onclick="manage_click(event)" id="manage">
<div id="tree">
<p>
Choose the data to manage:
</p>
<label><input type="checkbox">All</label>
    <div><label><input type="checkbox">Exam parameters (reset before reopening for the next semester)</label>
        <div><label><input type="checkbox">Session config tab</label>
            <div><label><input type="checkbox" name="start"></label></div>
            <div><label><input type="checkbox" name="stop"></label></div>
            <div><label><input type="checkbox" name="state"></label></div>
            <div><label><input type="checkbox" name="checkpoint"></label></div>
            <div><label><input type="checkbox" name="allow_copy_paste"></label></div>
            <div><label><input type="checkbox" name="forbid_question_copy"></label></div>
            <div><label><input type="checkbox" name="allow_ip_change"></label></div>
            <div><label><input type="checkbox" name="feedback"></label></div>
            <div><label><input type="checkbox" name="force_grading_done"></label></div>
        </div>
        <div><label><input type="checkbox">Student lists</label>
            <div><label><input type="checkbox" name="expected_students"></label></div>
            <div><label><input type="checkbox" name="tt"></label></div>
        </div>
        <div><label><input type="checkbox">Students logs</label>
            <div><label><input type="checkbox" name="active_teacher_room">Placement</label></div>
            <div><label><input type="checkbox" name="Grades">Grading</label></div>
            <div><label><input type="checkbox" name="Journal">Work + teacher comment</label></div>
        </div>
    </div>
    <div><label><input type="checkbox" name="Config">Session config tab (except Exam parameters)</label></div>
    <div><label><input type="checkbox" name="Access">Session access tab (except Exam parameters): admins/proctors/graders lists</label></div>
    <div><label><input type="checkbox" name="Source">Session source tab</label></div>
    <div><label><input type="checkbox" name="Media">Session media tab</label></div>
    <div><label><input type="checkbox" name="Grading">Session grading tab</label></div>
    <div><label><input type="checkbox" name="messages">Session chat tab</label></div>
</div>
<div id="tree_menu">
<p>
Operation on the selected data:
<div>
<button id="manage_export">Export ZIP</button> of the selected data of the current session
or more if multiple sessions are edited.
</div>
<div>
<form method="POST" enctype="multipart/form-data" target="_top">
<button id="manage_import">Import ZIP</button>
containing one or <b>multiple</b> sessions.<br>
<input id="manage_file" type="file" name="zip" accept="application/zip" onchange="update_disabled()"><br>
Only the selected data will be imported.<br>
Sessions are created automaticaly.
<p class="radio">
<label><input id="manage_one" onchange="update_disabled()" type="radio" name="destination" value="one"
>Do not use session names from ZIP and import into</label>
<input id="manage_name" name="session" style="width:100%" onkeyup="update_disabled()"
 value="''' + COURSE + '''">
<p class="radio">
<label><input id="manage_multiple" onchange="update_disabled()" type="radio"
              name="destination" value="multiple" select
>Import into or create the sessions whose names are in the ZIP</label>
</form>
</div>
<div>
<b>Session copy</b>:<br>
Export and then import with another name.
</div>
<div id="manage_reset_all">
<b>Session delete</b>: the «Erase or reset to defaults» of<br>
«Session source tab» will fully destroy the session.<br>
«Students logs» will destroy students logs.<br>
«Session media tab» will erase media.<br>
</div>
<div>
<button id="manage_reset">Erase or reset to defaults</button> use defaults
defined by COURSE_OPTIONS in the source file or C5 defaults if not
defined in COURSE_OPTIONS.
<p id="manage_reset_log">
This may destroy all students logs, grading...<br>
So be really careful and get the ZIP before.
</div>
</div>
</div>
'''
        items = []
        for value in content.split('name="'):
            key = value.split('"')[0]
            if key in DEFAULT_COURSE_OPTIONS_DICT:
                left = key + '">'
                if key == 'state':
                    DEFAULT_COURSE_OPTIONS_DICT[key] = 'State'
                value = left + DEFAULT_COURSE_OPTIONS_DICT[key] + value[len(left):]
            items.append(value)
        content = 'name="'.join(items)
        setTimeout(update_disabled, 100)
    else:
        content = ''

    document.getElementById('content').innerHTML = content
    if len(State['original_value']):
        update_course_config(State.config, '')

def get_state():
    inputs = {}
    for element in document.getElementById('tree').getElementsByTagName('INPUT'):
        if element.name:
            inputs[element.name] = element.checked
    if inputs['Access']:
        for key in 'admins graders proctors'.split(' '):
            inputs[key] = True
        inputs['Access'] = False
    if inputs['Config']:
        for key in DEFAULT_COURSE_OPTIONS_DICT:
            if key not in inputs:
                inputs[key] = True
        inputs['Config'] = False
    if inputs['Grading']:
        inputs['notation'] = True
        inputs['notationB'] = True
        inputs['Grading'] = False
    inputs = [i for i in inputs if inputs[i]]
    return ' '.join(inputs)

def update_disabled():
    tree = document.getElementById('tree')
    if not tree:
        return
    tree_menu = document.getElementById('tree_menu')
    tree = tree.parentNode
    state = get_state()
    disabled = state == ''
    if disabled:
        tree_menu.style.opacity = 0.4
    else:
        tree_menu.style.opacity = 1
    for element in tree.getElementsByTagName('BUTTON'):
        element.disabled = disabled
    for element in tree.getElementsByTagName('INPUT'):
        if element.type != 'checkbox':
            element.disabled = disabled
    if not disabled:
        manage_import = document.getElementById('manage_import')
        manage_reset = document.getElementById('manage_reset')
        manage_reset_log = document.getElementById('manage_reset_log')
        manage_reset_all = document.getElementById('manage_reset_all')
        manage_file = document.getElementById('manage_file')
        manage_one = document.getElementById('manage_one')
        manage_multiple = document.getElementById('manage_multiple')
        manage_name = document.getElementById('manage_name')
        if not manage_one.checked:
            manage_name.disabled = True
        if (not manage_one.checked and not manage_multiple.checked
            or manage_one.checked and '=' not in manage_name.value
           ):
            manage_import.disabled = True
            manage_file.disabled = True
        if not manage_file.value:
            manage_import.disabled = True
        if 'Source' in state:
            manage_reset_all.style.color = '#F00'
        else:
            manage_reset_all.style.color = '#000'
        if 'Grades' in state or 'Journal' in state or 'Source' in state:
            manage_reset_log.style.color = '#F00'
        else:
            manage_reset_log.style.color = '#888'

def manage_click(event):
    if event.target.tagName == 'INPUT':
        if event.target.type == 'checkbox':
            value = event.target.checked
            for element in event.target.parentNode.parentNode.getElementsByTagName('INPUT'):
                element.checked = value
            update_disabled()
    elif event.target.tagName == 'BUTTON':
        if event.target.id == 'manage_export':
            window.open('adm/export/' + COURSE + '/' + get_state()
                + '/' + COURSE + '.zip?ticket=' + TICKET)
        elif event.target.id == 'manage_import':
            form = event.target
            while form.tagName != 'FORM':
                form = form.parentNode
            form.setAttribute('action', 'adm/import/' + get_state() + '?ticket=' + TICKET)
            form.submit()
        elif event.target.id == 'manage_reset':
            window.location = 'adm/reset/' + COURSE + '/' + get_state() + '?ticket=' + TICKET

def init():
    """Create the HTML"""
    div = document.createElement('DIV')
    div.style.display = 'none'
    update_course_config.div = div

    div.onchange = onchange
    title = html(COURSE)
    if title.startswith('^'):
        title = '<span style="background: #F00; color: #FFF">' + title + ' (session set)</span>'
    div.innerHTML = ('<h1 style="display: flex"><span>' + title + """</span>
     <div id="server_feedback">Problems and server feedbacks will be written here.</div>
    </h1>
    <title>""" + html(COURSE.replace(RegExp('.*=', ''), ' ')) + """</title>
    <link rel="stylesheet" href="CSS/adm_session.css?ticket=""" + TICKET + '''">
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
    <div id="History">History</div>
    <div id="Manage">Manage</div>
     <select onchange="select_action(this)" style="vertical-align: top;">
    <option>Actions</option>
    <option action="upload">Upload a new source</option>
    <option action="upload_media">Upload a new media</option>
    <option action="rename_session">Rename session</option>
    <option action="git_pull">GIT pull</option>
    <option action="force_grading_done">Force «Grading done» on finished gradings</option>
    </select>
    </div>
    <div id="content"></div>
    <form method="POST" enctype="multipart/form-data" style="display:none" target="script"
          action="''' + BASE + "/upload_course/" + COURSE.replace('=', '/') + "?ticket=" + TICKET + '''">
          <input id="file" type="file" name="course" onchange="do_submit(this)">
    </form>
    <form method="POST" enctype="multipart/form-data" style="display:none" target="script"
          action="''' + BASE + "/upload_media/" + COURSE.replace('=', '/') + "?ticket=" + TICKET + """">
          <input id="media" type="file" name="course" onchange="do_submit(this)">
    </form>
    """)
    add(div)
    setTimeout(load_config, 10) # Wait CSS loading
    setInterval(update_interface, 5000)

def count_words(element):
    """Search for duplicate student ID"""
    text = element.value.strip()
    if len(text) == 0:
        return '', text
    words = text.split(RegExp('[ \t\n\r]+'))

    uniq = {}
    for word in words:
        new_word = normalize_login(word)
        uniq[new_word] = True
        text = text.replace(word, new_word)
    message = str(len(uniq))
    if len(uniq) != len(words):
        message = ('<b style="background:#F88; font-size:200%">'
                   + (len(words) - len(uniq)) + ' duplicates</b><br>'
                   + message)
    return message, text

def update_interface():
    """Update grading"""
    grading_sum = document.getElementById('grading_sum')
    notation = document.getElementById("notation")
    notationB = document.getElementById("notationB")
    if grading_sum and notation:
        grade_a = Grades(notation.value)
        grade_b = Grades(notationB.value)

        if grade_a.max_grade or grade_b.max_grade:
            message = 'Maximum possible grade: <b>'
            if grade_a.max_grade == grade_b.max_grade or grade_b.max_grade == 0:
                message += grade_a.max_grade
            else:
                message += '<span style="background:#F88">' + grade_a.max_grade + '/' + grade_b.max_grade + '</span>'
            message += '</b>'

        if grade_a.nr_competences or grade_b.nr_competences:
            message += '. Nbr competences toggles: <b>'
            if grade_a.nr_competences == grade_b.nr_competences or grade_b.nr_competences == 0:
                message += grade_a.nr_competences
            else:
                message += '<span style="background:#F88">' + grade_a.nr_competences + '/' + grade_b.nr_competences + '</span>'
            message += '</b>'

        grading_sum.innerHTML = message
        if notation.value:
            notation.value = grade_a.with_keys()
        if notationB.value:
            notationB.value = grade_b.with_keys()

init()
