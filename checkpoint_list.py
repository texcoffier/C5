"""
Tools the sessions list
"""

def edit():
    """Launch editor on a set of session"""
    session_filter = document.getElementById('edit')
    window.open('/adm/session/^'
                + encodeURIComponent(session_filter.value).replace(RegExp(r'\.', 'g'), '%2E')
                + '?ticket=' + TICKET)

def update(value):
    """Update display status"""
    path = window.location.toString().replace(RegExp(r'/\*/[^?]*'), '/*/' + value)
    window.history.replaceState('_a_', '', path)
    session_filter = RegExp('^' + value)
    rows = document.getElementsByTagName('TR')
    for row in rows:
        if row.cells and row.cells[0] and row.cells[13]:
            found = session_filter.exec(row.cells[0].textContent)
            if value == '' or value == '^':
                found = False
            if (row.cells[12].textContent.indexOf(LOGIN) == -1
                and row.cells[13].textContent.indexOf(LOGIN) == -1
                and CONFIG.roots.indexOf(LOGIN) == -1
                and CONFIG.masters.indexOf(LOGIN) == -1):
                found = False
            if value == '' or value == '^':
                found = True
            if row.cells[0].tagName == 'TH' or found:
                row.style.display = "table-row"
            else:
                row.style.display = "none"
