"""Home page for students"""

THEMES = {
    "default" : 'Thème recommandé',
    "ascetic" : 'Monochrome',
    "grayscale" : 'Monochrome/Fond',
    "idea" : 'Gras/Vert/bleu',
    }

def home_key_down(event):
    if event.key == 'F11':
        alert("Vous passerez en plein écran en cliquant sur "
            + "le bouton «Plein écran» une fois l'examen lancé")
        event.preventDefault()

window.onkeydown = home_key_down

def theme_focus():
    code = document.getElementById('code')
    hljs.highlightElement(code)
    code.style.display = 'block'

def theme_blur():
    document.getElementById('code').style.display = 'none'

def theme_update(theme):
    if theme == 'default':
        theme = "a11y-light"
    document.getElementById('theme').href = "HIGHLIGHT/" + theme + ".css?ticket=" + TICKET

def theme_change(s):
    theme_update(s.value)
    localStorage['theme'] = s.value
    theme_focus()

def home(sessions, infos):
    """Display student home page"""

    themes = [ # Uncomment to see all the themes
    # '1c-light', 'a11y-dark', 'a11y-light', 'agate', 'an-old-hope', 'androidstudio',
    # 'arduino-light', 'arta', 'ascetic', 'atom-one-dark-reasonable', 'atom-one-dark',
    # 'atom-one-light', 'brown-paper', 'codepen-embed', 'color-brewer',
    # 'cybertopia-cherry', 'cybertopia-dimmer', 'cybertopia-icecap',
    # 'cybertopia-saturated', 'dark', 'default', 'devibeans', 'docco', 'far',
    # 'felipec', 'foundation', 'github-dark-dimmed', 'github-dark', 'github', 'gml',
    # 'googlecode', 'gradient-dark', 'gradient-light', 'grayscale', 'hybrid', 'idea',
    # 'intellij-light', 'ir-black', 'isbl-editor-dark', 'isbl-editor-light',
    # 'kimbie-dark', 'kimbie-light', 'lightfair', 'lioshi', 'magula', 'mono-blue',
    # 'monokai-sublime', 'monokai', 'night-owl', 'nnfx-dark', 'nnfx-light', 'nord',
    # 'obsidian', 'panda-syntax-dark', 'panda-syntax-light', 'paraiso-dark',
    # 'paraiso-light', 'pojoaque', 'purebasic', 'qtcreator-dark', 'qtcreator-light',
    # 'rainbow', 'rose-pine-dawn', 'rose-pine-moon', 'rose-pine', 'routeros',
    # 'school-book', 'shades-of-purple', 'srcery', 'stackoverflow-dark',
    # 'stackoverflow-light', 'sunburst', 'tokyo-night-dark', 'tokyo-night-light',
    # 'tomorrow-night-blue', 'tomorrow-night-bright', 'vs-dark', 'vs', 'vs2015',
    # 'xcode', 'xt256'
    ]
    theme = localStorage['theme'] or 'default'

    content = [
        '''
<style>
    BODY { font-family: sans-serif }
    .compiler { opacity: 0.3 }
    P.node:hover, DIV[onclick]:hover { border: 1px solid black }
    P.node      , DIV[onclick]       { border: 1px solid #FFF; }
    P { margin: 0.1em; }
    P.node:before { content: '▶'; display: inline-block; transition: 0.3s transform }
    P.node.open:before { transform: rotate(90deg) }
    TT { color:  #00F }
    NODE { display: block; overflow: hidden; margin-left: 3em; margin-bottom: 0.2em }
    NODE.close { height: 0px;}
    KEY { display: inline-block; min-width: 12em; }
    .code { display: none; position: fixed; top:0; left:0 ; background: #FFF;
        white-space: pre; border: 2px solid #888; padding: 1em; margin: 1em;
        font-family: monospace, monospace }
</style>
<link rel="stylesheet" id="theme" href="HIGHLIGHT/a11y-light.css?ticket=''', TICKET, '''">
<title>C5 Home</title>
<h1>C5 de  ''', LOGIN, ' ', infos['fn'], ' ', infos['sn'], '''</h1>
<p>
<a target="_blank" href="zip/C5.zip?ticket=''', TICKET, '''">
💾 ZIP</a> contenant la dernière sauvegarde de toutes vos sessions.
<p>
Vous pouvez changer le thème coloration syntaxique :
<select onfocus="theme_focus()" onblur="theme_blur()" onkeydown="theme_change(this)" onchange="theme_change(this)">''',
''.join(['<option value="' + i + '"' + (theme == i and 'selected ' or '') + '>'
        + THEMES[i] + '</option>' for i in THEMES]),
''.join(['<option value="' + i + '">' + i + '</option>' for i in themes]),
'''</select>
<div id="code" class="code language-cpp" >
int main() { // Commentaire
    for(int a = 0; a != 'C'; a++)
        cout << a;
    cout << "Fini\\n";
}</div>

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
            return '<span class="compiler">' + name[0] + '</span> ' + name[1]
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
    theme_update(theme)

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
