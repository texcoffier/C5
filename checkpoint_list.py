"""
Tools the sessions list
"""

class INTERFACE:
    filter = None            # The filter value
    filter_element = None    # The INPUT containing the filter
    nr_sessions_filtered = 0 # Number of sessions displayed on screen
    titles = None            # Column title (init from HTML content)
    visible_columns = []      # Titles of the columns to hide (init from localStorage)

def edit():
    """Launch editor on a set of session"""
    session_filter = get_regexp_from_filter(INTERFACE.filter)
    if session_filter == '':
        alert("Je refuse d'éditer toutes les sessions à la fois...")
        return
    if confirm("Vous allez modifier " + INTERFACE.nr_sessions_filtered
        + " sessions en même temps, vous voulez vraiment le faire ?"):
        window.open(
            BASE + '/adm/session/^'
            + encodeURIComponent(session_filter).replace(RegExp('\\.', 'g'), '%2E')
            + '?ticket=' + TICKET)

def edit_ticked():
    """Launch editor on a set of session"""
    names = []
    for row in document.getElementsByTagName('TR'):
        if row.style.display != "none":
            if (row.cells[1]
                    and row.cells[1].firstChild.tagName == 'INPUT'
                    and row.cells[1].firstChild.checked
                    ):
                names.append(row.cells[2].firstChild.textContent.upper()
                    + '=' + row.cells[0].firstChild.textContent)
    if len(names):
        window.open(
            BASE + '/adm/session/^(' + encodeURIComponent('|'.join(names))
            + ')?ticket=' + TICKET)
    else:
        alert("Tick some boxes before clicking here")

def get_regexp_from_filter(value):
    """Translate"""
    if value == 'Mes sessions':
        return my_sessions()
    if value == 'Toutes les sessions':
        return ''
    return value

def filter_change(_event):
    """DATALIST Option selected or key stroked"""
    hide_filter_menu() # User is typing into the INPUT
    INTERFACE.filter = INTERFACE.filter_element.value.strip()
    update(INTERFACE.filter)
    localStorage['checkpoint_list'] = INTERFACE.filter

def filter_focus():
    INTERFACE.filter_element.select()

def init_filters(the_filter):
    """Fill the options of the select filter"""
    INTERFACE.filter_element.onkeyup = filter_change
    INTERFACE.filter_element.onfocus = filter_focus
    INTERFACE.filter_element.onblur = hide_filter_menu_later
    sessions = []
    for row in document.getElementsByTagName('TR'):
        if row.cells and row.cells[0]:
            key = row.cells[0].textContent
            sessions.append(key)
    sessions.sort()
    tree = session_tree([[i] for i in sessions])
    options = []
    def flat(node, remove=0):
        if remove==0 or len(node[1]) + len(node[2]) > 4:
            if node[0] != '':
                options.append((node[0], '                        '[:remove] + node[0][remove:]))
            remove = len(node[0])
            if remove:
                remove += 1
            for i in node[1]:
                flat(i, remove=remove)
    flat(tree)
    options.append(('Mes sessions', 'Mes sessions'))
    options.append(('Toutes les sessions', 'Toutes les sessions'))
    options = ''.join(['<option value="' + value + '" onclick="select_filter_menu(this)">'
                       + text + '</option>'
                       for value, text in options])
    INTERFACE.filter_menu.innerHTML = options
    INTERFACE.filter_element.value = the_filter

def change_header_visibility(header, visible):
    """Hide or show headers"""
    if not header:
        return
    header.style.display = visible and "table-row" or "none"
    if header.nextSibling:
        header.nextSibling.style.display = visible and "table-row" or "none"

def update(value):
    """Update display status"""
    location = window.location.toString()
    if 'checkpoint' in location:
        path = location.replace(RegExp('/\\*[^?]*'), '/*/' + encodeURIComponent(value))
    else:
        path = location.replace('?', 'checkpoint/*/' + encodeURIComponent(value) + '?')
    window.history.replaceState('_a_', '', path)
    value = get_regexp_from_filter(value)
    session_filter = RegExp('^' + value)
    rows = document.getElementsByTagName('TR')
    header = None
    nr_actives = 0
    INTERFACE.nr_sessions_filtered = 0
    for row in rows:
        if row.className == 'sticky':
            change_header_visibility(header, one_visible)
            header = row
            one_visible = False
            continue
        if row.className == 'sticky2':
            continue
        if row.cells and row.cells[0] and row.cells[13]:
            found = session_filter.exec(row.cells[0].textContent)
            if value == '' or value == '^':
                found = False
            # if (row.cells[12].textContent.indexOf(LOGIN) == -1
            #     and row.cells[13].textContent.indexOf(LOGIN) == -1
            #     and CONFIG.roots.indexOf(LOGIN) == -1
            #     and CONFIG.masters.indexOf(LOGIN) == -1):
            #     found = False
            if value == '' or value == '^':
                found = True
            if row.cells[0].tagName == 'TH' or found:
                row.style.display = "table-row"
                one_visible = True
                INTERFACE.nr_sessions_filtered += 1
            else:
                row.style.display = "none"
            if row.cells[6].textContent.strip() != '':
                nr_actives += Number(row.cells[6].textContent)
    change_header_visibility(header, one_visible)
    document.getElementById('nr_actives').innerHTML = nr_actives
    document.getElementById('nr_doing_grading').innerHTML = INTERFACE.nr_doing_grading

def my_sessions():
    sessions = []
    rows = document.getElementsByTagName('TR')
    for row in rows:
        if not row.cells or not row.cells[0]:
            continue
        for i in range(12, 16):
            if row.cells[i] and LOGIN in row.cells[i].textContent:
                sessions.append(row.cells[0].textContent.split(' «')[0])
                break
    return '(' + '|'.join(sessions) + ')'

def go_student():
    """Display as student"""
    student = document.getElementById('student').value
    localStorage['student'] = student
    student = normalize_login(student)
    window.open(BASE + '/?ticket=' + TICKET + '&login=' + student)

def show_filter_menu():
    INTERFACE.filter_menu.className = 'filter_menu'

def select_filter_menu(option):
    INTERFACE.filter_element.value = option.value
    INTERFACE.filter_element.onkeyup()

def hide_filter_menu():
    INTERFACE.filter_menu.className = ''

def hide_filter_menu_later():
    setTimeout(hide_filter_menu, 200)

def init_interface(nr_doing_grading):
    """Use location to get filter"""
    INTERFACE.nr_doing_grading = nr_doing_grading
    url = window.location.toString()
    try:
        INTERFACE.filter = localStorage['checkpoint_list']
    except: # pylint: disable=bare-except
        INTERFACE.filter = ''
    try:
        columns = localStorage['columns']
    except: # pylint: disable=bare-except
        columns = None
    if not columns:
        columns = '["Title","Students","Start date","Duration","Options","Edit","👁","Waiting Room"]'
    INTERFACE.visible_columns = [clean_title(title) for title in JSON.parse(columns)]
    if url.indexOf('/*/') != -1:
        INTERFACE.filter = decodeURIComponent(url.replace(RegExp('.*/'), '').split('?')[0])
    if not INTERFACE.filter or INTERFACE.filter == '':
        INTERFACE.filter = 'Toutes les sessions'

    value = localStorage['student'] or ''
    element = document.createElement('DIV')
    element.innerHTML = '''
    <p>
    <button onclick="go_student()">Display</button>
    <INPUT id="student" value="''' + value + '"> student page.'
    document.body.appendChild(element)

    top = ['''<title>SESSIONS</title>
<input id="filter" onclick="show_filter_menu()"> ← filter only what matters to you.
<datalist id="filter_menu"></datalist>''']
    if window.IS_AUTHOR:
        top.append('<button onclick="edit()">Edit all sessions</button> ')
        top.append('<button onclick="edit_ticked()">Edit ☑ sessions</button>')
    top.append('''
<div style="float: right">
<span id="nr_doing_grading"></span> active graders</span>,
<span id="nr_actives"></span> active students</span>
</div>''')
    document.getElementById('header').innerHTML = ''.join(top)

    update(INTERFACE.filter)
    INTERFACE.filter_element = document.getElementById('filter')
    if INTERFACE.filter_element:
        INTERFACE.filter_element.value = INTERFACE.filter
    INTERFACE.filter_menu = document.getElementById('filter_menu')
    init_filters(INTERFACE.filter_element.value)

    for tr in document.getElementsByTagName('TR'):
        if tr.className == 'sticky2':
            INTERFACE.titles = [clean_title(th.textContent) for th in tr.cells]
            break

    update_body_class()

def clean_title(txt):
    return txt.replace(RegExp('[  \n]*', 'g'), '').lower().replace('waitingroom', 'waitroom')

def column_toggle(event):
    """Show Hide column"""
    cell = event.target
    if cell.tagName == 'A':
        return
    while cell and not cell.cellIndex:
        cell = cell.parentNode
    if not cell:
        return
    if cell.cellIndex <= 1: # Session and toggle
        return
    table = cell.parentNode.parentNode
    titles = table.childNodes[1]
    column = clean_title(titles.childNodes[cell.cellIndex].textContent)
    checked = column not in INTERFACE.visible_columns
    if checked:
        INTERFACE.visible_columns.append(column)
    else:
        INTERFACE.visible_columns = [i for i in INTERFACE.visible_columns if i != column]
    update_body_class()
    localStorage['columns'] = JSON.stringify(INTERFACE.visible_columns)

def update_body_class():
    """To hide columns"""
    hidden = []
    for i, title in enumerate(INTERFACE.titles):
        if i and title not in INTERFACE.visible_columns:
            hidden.append('hide' + (i+1))
    document.body.className = ' '.join(hidden)
