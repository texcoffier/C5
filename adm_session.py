
if False: # pylint: disable=using-constant-test
    # pylint: disable=undefined-variable,invalid-name,self-assigning-variable
    COURSE = COURSE
    TICKET = TICKET
    html = html
    RegExp = RegExp
    Date = Date
    document = document
    setTimeout = setTimeout
    encodeURIComponent = encodeURIComponent


THEMES = "a11y-dark a11y-light agate an-old-hope androidstudio arduino-light arta ascetic atom-one-dark-reasonable atom-one-dark atom-one-light brown-paper codepen-embed color-brewer dark default devibeans docco far felipec foundation github-dark-dimmed github-dark github gml googlecode gradient-dark gradient-light grayscale hybrid idea intellij-light ir-black isbl-editor-dark isbl-editor-light kimbie-dark kimbie-light lightfair lioshi magula mono-blue monokai-sublime monokai night-owl nnfx-dark nnfx-light nord obsidian panda-syntax-dark panda-syntax-light paraiso-dark paraiso-light pojoaque purebasic qtcreator-dark qtcreator-light rainbow routeros school-book shades-of-purple srcery stackoverflow-dark stackoverflow-light sunburst tokyo-night-dark tokyo-night-light tomorrow-night-blue tomorrow-night-bright vs vs2015 xcode xt256"


def add(element):
    """Add an element to the document BODY"""
    document.body.appendChild(element)

def load_config():
    """Retrieve the current configuration"""
    script = document.createElement('SCRIPT')
    script.src = '/course_config/' + COURSE + '?ticket=' + TICKET
    add(script)

def do_grade(login):
    window.open('/grade/' + COURSE + '/' + login + '?ticket=' + TICKET)

def update_course_config(config, feedback):
    """Update the HTML with the configuration.
    This function is called by server answer.
    """
    first_time = update_course_config.div.style.display == 'none'
    for attr in config:
        element = document.getElementById(attr)
        if element:
            value = config[attr]
            if first_time:
                element.original_value = value
            elif element.tagName != 'DIV':
                if element.original_value == value:
                    class_name = ''
                else:
                    class_name = 'changed'
                if element.parentNode.tagName == 'LABEL' and element.tagName != 'SELECT':
                    element.parentNode.className = class_name
                else:
                    element.className = class_name
            if element.tagName == 'TEXTAREA':
                element.value = value
            elif element.tagName == 'INPUT':
                if element.type == 'checkbox':
                    element.checked = value != '0'
                else:
                    element.value = value
            elif element.tagName == 'SELECT':
                element.value = value
            elif attr == 'messages':
                content = []
                for message in value:
                    date = Date()
                    date.setTime(1000 * message[1])
                    date = str(date)[:24]
                    content.append('<div>' + html(message[2])
                        + '<div>' + date + '<br>' + message[0] + '</div></div>')
                element.innerHTML = ''.join(content)
            elif attr == 'active_teacher_room':
                content = []
                for login in value:
                    (active, teacher, room, timestamp, nr_blurs, nr_questions, hostname, time_bonus, grade) = value[login]
                    date = Date()
                    date.setTime(1000 * timestamp)
                    more = ''
                    #if room:
                    #    more += '🗺️'
                    if teacher:
                        splited = teacher.split('.')
                        if len(splited) == 2:
                            more += '\t' + splited[0][0].upper() + splited[1][0].upper()
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
                    date = str(date)[:25]
                    content.append(
                        '<span style="width:' + 2*nr_blurs + 'px"></span>'
                        + '<div onclick="do_grade(\'' + login + '\')">'
                        + login + more
                        + '<div><table>'
                        + '<tr><td>closed<td>' + active + '</tr>'
                        + '<tr><td>teacher<td>' + teacher + '</tr>'
                        + '<tr><td>room<td>' + room + '</tr>'
                        + '<tr><td>last student action<td>' + date + '</tr>'
                        + '<tr><td>#blurs<td>' + nr_blurs + '</tr>'
                        + '<tr><td>#questions<td>' + nr_questions + '</tr>'
                        + '<tr><td>last hostname<td>' + hostname + '</tr>'
                        + '<tr><td>Time bonus<td>' + time_bonus + '</tr>'
                        + '<tr><td>Grade,#items graded<td>' + grade + '</tr>'
                        + '</table></div></div>')
                element.innerHTML = ''.join(content)
            else:
                element.innerHTML = value
    document.getElementById('invalid_date').style.display = config.start > config.stop and 'block' or 'none'

    update_course_config.div.style.display = 'block'
    if feedback:
        div = document.getElementById('feedback')
        div.innerHTML = feedback
        if feedback[-1] == '!':
            div.className = "error"
        else:
            div.className = ""

def upload(element):
    """Send the source file"""
    x = document.getElementById('script')
    if x:
        x.parentNode.removeChild(x)
    x = document.createElement('IFRAME')
    x.id = 'script'
    x.name = 'script'
    element.append(x)

    file = document.getElementById('file')
    event = eval("new MouseEvent('click', {'view': window, 'bubbles': true, 'cancelable': true})")
    file.dispatchEvent(event)

def upload_course(element):
    """Upload a course replacement"""
    element.parentNode.submit()

def onchange(event):
    """Send the change to the server"""
    target = event.target
    if not target.original_value and target.original_value != '':
        return
    attr = target.id
    if target.parentNode.tagName == 'LABEL' and target.tagName != 'SELECT':
        if target.checked:
            value = '1'
        else:
            value = '0'
        target = target.parentNode
    else:
        value = target.value
    target.className = 'wait_answer'
    script = document.createElement('SCRIPT')
    script.src = ('/adm/session/' + COURSE + '/' + attr
        + '/' + encodeURIComponent(value) + '?ticket=' + TICKET)
    add(script)
    event.stopPropagation()

def init():
    """Create the HTML"""
    div = document.createElement('DIV')
    div.style.display = 'none'
    update_course_config.div = div
    themes = []
    for theme in THEMES.split(' '):
        themes.append('<option>' + theme + '</option>')
    themes = ''.join(themes)
    div.onchange = onchange
    div.innerHTML = "<h1>" + html(COURSE.replace('=', '   ')) + """</h1>
    <title>""" + html(COURSE.split('=')[1]) + """</title>
    <link rel="stylesheet" href="/adm_session.css?ticket=""" + TICKET + """">
    <div class="boxed rights">
    <p class="title" style="margin-top: 0px">Creator</p>
    <p id="creator"></p>
    <p class="title">Admins</p>
    <textarea id="admins"></textarea>
    <p class="title">Graders</p>
    <textarea id="graders"></textarea>
    <p class="title">Proctors</p>
    <textarea id="proctors"></textarea>
    </div>
    <div class="configs">
    <input id="start">→<input id="stop"> <div id="invalid_date">START&gt;END</div><br>
    <label><input type="checkbox" id="copy_paste"> Allows copy/pastes from external source.</label>
    <label><input type="checkbox" id="checkpoint"> Requires students to be placed on the map.</label>
    <label><input type="checkbox" id="save_unlock"> Unlock the next question on save.</label>
    <label><input type="checkbox" id="sequential"> Question must be answered from first to last.</label>
    <label><input type="checkbox" id="coloring"> Syntaxic coloring of source code with <select id="theme">
    """ + themes + """</select></label>
    <label><input type="checkbox" id="highlight"> The session is greenly higlighted in sessions lists.</label>
    <p class="title"><b>Logins</b> of students with ⅓ more time to answer</p>
    <textarea id="tt"></textarea>
    <p class="title">Grading ladder</p>
    <pre style="margin-top: 0px">The grading part is right aligned and green with buttons
bla bla bla {It's working:0,0.5,1,1.5,2}
bla bla bla bla {Copy/Paste:-3,-2,-1,0}</pre>
    <textarea id="notation"></textarea>
    </div>
    <div class="state">
    <a target="_blank" onclick="javascript:upload(this)">Upload a new source</a>
    <a target="_blank" href="/adm/editor/""" + COURSE + '?ticket=' + TICKET + """"
    >Edit source with C5</a>
    <a target="_blank" href="=""" + COURSE + '?ticket=' + TICKET + """">Try the exercises</a>
    <br>
    <a target="_blank" href="/checkpoint/""" + COURSE + '?ticket=' + TICKET + """">Place students</a>
    <a target="_blank" href="/adm/course/""" + COURSE + '?ticket=' + TICKET + """">See students results</a>
    <a target="_blank" href="/adm/get/COMPILE_""" + COURSE.replace('=', '/') + '.zip?ticket=' + TICKET + """">Load full ZIP</a>
    <br>
    <a href="javascript:name=prompt('New name?');
            if (name && name != 'null')
                window.location = '/adm/session/' + COURSE + '/rename/' + name + '?ticket=' + TICKET;
            else
                undefined;
            ">
     Rename session</a>
    <a href="javascript:if(confirm('Really delete?'))window.location='/adm/session/""" + COURSE + '/delete/?ticket=' + TICKET + """'">
     Delete <b>ALL</b></a>
    <p class="title">Feedback</p>
    <div id="feedback"></div>
    <p class="title">Messages posted</p>
    <div id="messages" class="tips"></div>
    <p class="title">Students</p>
    <div id="active_teacher_room" class="tips"></div>
    </div>
    <form method="POST" enctype="multipart/form-data" style="display:none" target="script"
          action="/upload_course/""" + COURSE.replace('=', '/') + "?ticket=" + TICKET + """">
          <input id="file" type="file" name="course" onchange="upload_course(this)">
    </form>
    """
    add(div)
    setTimeout(load_config, 10) # Wait CSS loading

init()
