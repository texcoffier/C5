"""Home page for the C5 administrator"""
def update_url():
    """Hide the last action from URL"""
    url = location.toString() # pylint: disable=undefined-variable
    clean = url.replace(RegExp('(.*)/(adm|upload).*([?]ticket=.*)'), "$1/adm/root$3")
    history.replaceState('_a_', '_t_', clean)

def post(url, value):
    """POST a dictionnary"""
    form = document.createElement("form")
    form.setAttribute("method", "post")
    form.setAttribute("action", url)
    form.setAttribute("enctype", "multipart/form-data")
    form.setAttribute("encoding", "multipart/form-data") # For IE
    data = document.createElement("input")
    data.setAttribute("type", "hidden")
    data.setAttribute("name", "value")
    data.setAttribute("value", value)
    form.appendChild(data)
    document.body.appendChild(form)
    form.submit()

def display(): # pylint: disable=too-many-statements
    """Display adm home page"""
    update_url()
    text = [
        '<title>Root</title>',
        MORE,
        '<h1>Root (goto <a href="/checkpoint/*?ticket=', TICKET, '">Sessions</a>)</h1>',
    '''
    <style>
        BODY { font-family: sans-serif; background: #EEE }
        BODY > TEXTAREA { width: 100%; height: 10em }
        #more { border: 1px solid black ; background: #FFE;
        padding: 0.3em ; margin: 0.1em ;
        position: absolute;
        right: 0px;
        top: 0px;
        transform: scale(5, 5);
        transform-origin: top right;
        transition: transform 1s;
        }
    INPUT { font-size: 100% }
    </style>
    ''']
    def add_input(url, value, name='', disable=False):
        text.append(
            '<input onchange="post(\'' + url + '?ticket=' + TICKET + '\',this.value)"'
            + ' value="' + value + '" class="' + name + '"'
            + (disable and ' disabled' or '')
            + '>')
    def add_textarea(url, value, disable=False, name=''):
        text.append(
            '<textarea onchange="post(\'' + url + '?ticket=' + TICKET + '\',this.value)"'
            + (disable and ' disabled' or '')
            + (name and ' class="' + name + '"' or '')
            + '>'
            + html(value) + '</textarea>')
    def add_button(url, value, label, name=''):
        action = "post('" + url + '?ticket=' + TICKET + "','" + value + "')"
        text.append('<button onclick="' + action + '" class="' + name + '">'
                    + label + '</button>')
    text.append('Roots: ')
    for root in CONFIG.roots:
        add_button('/adm/c5/del_root', root, '🗑',
                   name='del_root_' + root.replace('.', '_')) # For regtests
        text.append(' ' + root + ', ')
    add_input('/adm/c5/add_root', '', name="add_root")
    text.append('<hr>')
    text.append('Masters: ')
    for master in CONFIG.masters:
        add_button('/adm/c5/del_master', master, '🗑',
                   name='del_master_' + master.replace('.', '_')) # For regtests
        text.append(' ' + master + ', ')
    add_input('/adm/c5/add_master', '', name="add_master")
    text.append('<hr>')
    text.append('Authors are allowed to create session: ')
    for author in CONFIG.authors:
        add_button('/adm/c5/del_author', author, '🗑',
                   name='del_author_' + author.replace('.', '_')) # For regtests
        text.append(' ' + author + ', ')
    add_input('/adm/c5/add_author', '', name="add_author")
    text.append('<hr>')
    text.append('Mappers are allowed to edit building maps: ')
    for mapper in CONFIG.mappers:
        add_button('/adm/c5/del_mapper', mapper, '🗑',
                   name='del_mapper_' + mapper.replace('.', '_')) # For regtests
        text.append(' ' + mapper + ', ')
    add_input('/adm/c5/add_mapper', '', name="add_mapper")
    text.append('<hr>')
    text.append('Session ticket time to live in seconds: ')
    add_input('/adm/c5/ticket_ttl', CONFIG.ticket_ttl, name="ticket_ttl")
    text.append(' ')
    add_button('/adm/c5/remove_old_tickets', '0', 'Remove old tickets now', name="remove_olds")
    text.append('<hr>')
    text.append('For each room indicate the computers IP:')
    content = []
    for room in CONFIG.ips_per_room:
        content.append(room + ' ' + CONFIG.ips_per_room[room])
    add_textarea('/adm/c5/ips_per_room', '\n'.join(content))
    text.append('<a href="/checkpoint/HOSTS/*?ticket=' + TICKET + '">Check IP usage per room</a>')
    text.append('<hr>')
    text.append('Sessions disabled by creators:')
    content = []
    for session in CONFIG.disabled:
        content.append(session + ' ' + CONFIG.disabled[session])
    add_textarea('/adm/c5/disabled', '\n'.join(content))
    text.append('<hr>')
    text.append('It is a student if the login match regexp: ')
    add_input('/adm/c5/student', CONFIG.student, name="student")
    text.append('<hr>')
    text.append('User messages:')
    content = []
    for message in CONFIG.messages:
        content.append(message + ' ' + CONFIG.messages[message])
    add_textarea('/adm/c5/messages', '\n'.join(content))
    text.append('''Enter a Python expression to evaluate as:
    <ul>
    <li> utilities.CONFIG.is_admin("thierry.excoffier")
    <li> utilities.CONFIG.load()
    <li> _session.is_proctor(utilities.CourseConfig.get("COMPILE_PYTHON/editor"))
    </ul>
    ''')
    add_textarea('/adm/c5/eval', '')
    document.body.innerHTML = text.join('') # pylint: disable=no-member
    def anime():
        more = document.getElementById('more')
        if more:
            more.style.transform = 'scale(1,1)'
            def hide():
                more.style.display = 'none'
            more.onclick = hide
    setTimeout(anime, 100)

display()
