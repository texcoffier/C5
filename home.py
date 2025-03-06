"""Home page for students"""

def home(sessions, infos):
    """Display student home page"""
    content = [
        '''
<style>
    BODY { font-family: sans-serif }
    SPAN { opacity: 0.3 }
    P.node:hover, DIV[onclick]:hover { border: 1px solid black }
    P.node      , DIV[onclick]       { border: 1px solid #FFF; }
    P { margin: 0.1em; }
    P.node:before { content: '▶'; display: inline-block; transition: 0.3s transform }
    P.node.open:before { transform: rotate(90deg) }
    TT { color:  #00F }
    NODE { display: block; overflow: hidden; margin-left: 3em; margin-bottom: 0.2em }
    NODE.close { height: 0px;}
    KEY { display: inline-block; min-width: 12em; }
</style>
<title>C5 Home</title>
<h1>C5 de  ''', LOGIN, ' ', infos['fn'], ' ', infos['sn'], '''</h1>
<p>
<a target="_blank" href="zip/C5.zip?ticket=''', TICKET, '''">
💾 ZIP</a> contenant la dernière sauvegarde de toutes vos sessions.
<br> 
<p>
Cliquez pour plier/déplier les dossiers ou ouvrir le cours qui vous intéresse :
<p>
 
''']
    now = millisecs() / 1000
    now_text = nice_date(now)

    def hide_compiler(name):
        if '=' in name:
            name = name.split('=')
            return '<span>' + name[0] + '</span> ' + name[1]
        return name

    def display_session(session, remove):
        course, highlight, expected, feedback, title, start_timestamp, stop_timestamp, tt = session
        style = "background:" + highlight
        if expected:
            style += ';font-weight: bold'
        content.append('<div onclick="location = \'=' + course + '?ticket=' + TICKET
            + '&login=' + LOGIN
            + '\'" style="' + style + '"><key>' + hide_compiler(course.replace(remove, '')) + '</key> ')
        if title != '':
            content.append('« ' + html(title) + ' »')
        content.append('<tt>')
        if now < start_timestamp:
            date = nice_date(start_timestamp)
            content.append(" début à " + date[11:])
            if date[:10] != now_text[:10]:
                content.append(" le " + date[:10])
            minutes = (stop_timestamp - start_timestamp)/60
            if minutes <= 4*60:
                content.append(" durée " + minutes + ' minutes')
            else:
                content.append(" → " + nice_date(stop_timestamp))
            if tt:
                content.append(' +⅓ temps')
        if feedback:
            content.append(' Examen terminé : ' + [
                None,
                'Vos réponses.',
                'Une correction possible.',
                'Commentaire de votre travail.',
                'Votre note.',
                'Détails de votre note.'][feedback])
        content.append('</tt></div>')

    def bold_and_color(node):
        bold = False
        color = None
        # Direct session
        for session in node[2]:
            if session[2]:
                bold = True
            if session[1] and session[1] != '#FFF':
                color = session[1]
        for node in node[1]:
            bold_child, color_child = bold_and_color(node)
            bold = bold or bold_child
            color = color or color_child
        return bold, color or '#FFF'

    def display(node, remove):
        if node[0] != '':
            content.append('<p class="node" onclick="toggle(\'' + node[0] + '\')" style="')
            bold, color = bold_and_color(node)
            if color:
                content.append('background:' + color + ';')
            if bold:
                content.append('font-weight:bold;')
            content.append('">')
            content.append(hide_compiler(node[0].replace(remove, '')))
            content.append('</p>')
            content.append('<NODE id="')
            content.append(node[0])
            content.append('">')
        for child in node[1]:
            display(child, node[0] + '_')
        for session in node[2]:
            display_session(session, node[0] + '_')
        if node[0] != '':
            content.append('</NODE>')

    display(session_tree(sessions), '')

    document.body.innerHTML += ''.join(content)
    update_style()

def toggle(key):
    """Open close"""
    opens = JSON.parse(localStorage['opens'] or '[]')
    if key in opens:
        opens = [i for i in opens if i != key]
    else:
        opens.append(key)
    localStorage['opens'] = JSON.stringify(opens)
    update_style()

def update_style():
    """Update open/close from local storage"""
    opens = JSON.parse(localStorage['opens'] or '[]')

    for ul_elm in document.getElementsByTagName('NODE'):
        if ul_elm.id in opens:
            ul_elm.previousSibling.className = 'node open'
            ul_elm.className = 'open'
        else:
            ul_elm.previousSibling.className = 'node close'
            ul_elm.className = 'close'
