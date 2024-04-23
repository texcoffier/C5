"""
Tools the sessions list
"""

class INTERFACE:
    filter = None          # The filter value
    filter_element = None  # The INPUT containing the filter

def edit():
    """Launch editor on a set of session"""
    session_filter = get_regexp_from_filter(INTERFACE.filter)
    window.open('/adm/session/^'
                + encodeURIComponent(session_filter).replace(RegExp('\\.', 'g'), '%2E')
                + '?ticket=' + TICKET)

def get_regexp_from_filter(value):
    """Translate"""
    if value == 'Mes sessions':
        return my_sessions()
    if value == 'Toutes les sessions':
        return ''
    return value

def filter_change(event):
    """Option selected"""
    INTERFACE.filter = event.target.value
    if INTERFACE.filter_element:
        INTERFACE.filter_element.value = INTERFACE.filter
    update(INTERFACE.filter)
    localStorage['checkpoint_list'] = INTERFACE.filter

def init_filters(the_filter):
    """Fill the options of the select filter"""
    filters = document.getElementById('filters')
    filters.onchange = filter_change
    filters.className = 'sticky'
    filters.style.zIndex = 2
    options = []
    rows = document.getElementsByTagName('TR')
    for row in rows:
        if row.cells and row.cells[0]:
            key = row.cells[0].textContent
            if '_' not in key:
                continue
            key = key.split('_')[0]
            if key in options:
                continue
            options.append(key)
    options.sort()
    options.append('Mes sessions')
    options.append('Toutes les sessions')
    options = ''.join(['<option>' + option + '</option>' for option in options])
    filters.innerHTML = options
    filters.value = the_filter

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
            else:
                row.style.display = "none"
            if row.cells[4].textContent != '':
                nr_actives += Number(row.cells[4].textContent)
    change_header_visibility(header, one_visible)
    document.getElementById('nr_actives').innerHTML = nr_actives

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

def init_interface():
    """Use location to get filter"""
    url = window.location.toString()
    try:
        INTERFACE.filter = localStorage['checkpoint_list']
    except: # pylint: disable=bare-except
        INTERFACE.filter = ''
    if url.indexOf('/*/') != -1:
        INTERFACE.filter = decodeURIComponent(url.replace(RegExp('.*/'), '').split('?')[0])
    if not INTERFACE.filter or INTERFACE.filter == '':
        INTERFACE.filter = 'Toutes les sessions'
    update(INTERFACE.filter)
    init_filters(INTERFACE.filter)
    INTERFACE.filter_element = document.getElementById('edit')
    if INTERFACE.filter_element:
        INTERFACE.filter_element.value = INTERFACE.filter
