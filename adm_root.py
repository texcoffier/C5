"""Home page for the C5 administrator"""

try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    MORE = MORE
    LOGIN = LOGIN
    CONFIG = CONFIG
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
    clean = url.replace(RegExp('(.*)/(adm|upload).*([?]ticket=.*)'), "$1/adm/root$3")
    history.replaceState('_a_', '_t_', clean)

def display(): # pylint: disable=too-many-statements
    """Display adm home page"""
    update_url()
    text = [
        '<title>Root</title>',
        MORE,
        '<h1>Root (goto <a href="/adm/home?ticket=', TICKET, '">Adm page</a>)</h1>',
    '''
    <style>
        BODY { font-family: sans-serif }
        BODY > TEXTAREA { width: 100%; height: 10em }
        #more { border: 1px solid black ; background: #FFE;
        padding: 0.3em ; margin: 0.1em ;
        position: absolute;
        right: 0px;
        top: 0px;
        transform: scale(5, 5);
        transform-origin: top right;
        transition: transform 1s;
        pointer-events: none;
        }
    </style>
    ''']
    def add_input(url, value, name='', disable=False):
        text.append(
            '<input onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'"'
            + ' value="' + value + '" class="' + name + '"'
            + (disable and ' disabled' or '')
            + '>')
    def add_textarea(url, value, disable=False, name=''):
        text.append(
            '<textarea onchange="window.location = \''
            + url + "'+encodeURIComponent(this.value)+" + '\'?ticket=' + TICKET + '\'" '
            + (disable and ' disabled' or '')
            + (name and ' class="' + name + '"' or '')
            + '>'
            + html(value) + '</textarea>')
    def add_button(url, label, name='', new_window=False):
        url = "'" + url + '?ticket=' + TICKET + "'"
        if new_window:
            action = 'window.open(' + url + ')'
        else:
            action = 'window.location = ' + url
        text.append('<button onclick="' + action + '" class="' + name + '">'
                    + label + '</button>')
    text.append('Roots: ')
    for root in CONFIG.roots:
        add_button('/adm/c5/del_root/' + root, '🗑',
                   name='del_root_' + root.replace('.', '_')) # For regtests
        text.append(' ' + root + ', ')
    add_input('/adm/c5/add_root/', '', name="add_root")
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
    text.append('For each room indicate the computers IP:')
    content = []
    for room in CONFIG.ips_per_room:
        content.append(room + ' ' + CONFIG.ips_per_room[room])
    add_textarea('/adm/c5/ips_per_room/', '\n'.join(content))
    text.append('<hr>')
    text.append('It is a student if the login match regexp: ')
    add_input('/adm/c5/student/', CONFIG.student, name="student")
    text.append('<hr>')
    text.append('User messages:')
    content = []
    for message in CONFIG.messages:
        content.append(message + ' ' + CONFIG.messages[message])
    add_textarea('/adm/c5/messages/', '\n'.join(content))
    document.body.innerHTML = text.join('') # pylint: disable=no-member
    def anime():
        more = document.getElementById('more')
        if more:
            more.style.transform = 'scale(1,1)'
    setTimeout(anime, 100)

display()
