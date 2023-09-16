"""Home page for students"""

HEIGHTS = {}

def home(sessions):
    """Display student home page"""
    content = [
        '''
<style>
    BODY { font-family: sans-serif }
    SPAN { opacity: 0.3 }
    A:hover SPAN { opacity: 1 }
    A { text-decoration: none }
    A:hover { text-decoration: underline }
    UL { margin-top: 0px ; margin-bottom: 0px; overflow: hidden; transition: 0.3s height }
    P { margin: 0.1em }
    P.root:before { content: '▶'; display: inline-block; transition: 0.3s transform }
    P.root.open:before { transform: rotate(90deg) }
</style>
<h1>C5 de  ''', LOGIN, '''</h1>
<p>
<a target="_blank" href="/zip/C5.zip?ticket=''', TICKET, '''">
💾 ZIP</a> contenant la dernière sauvegarde de toutes vos sessions.
<br> 
<p>
Cliquez pour ouvrir/fermer le cours qui vous intéresse :
''']
    tree = {}
    roots = []
    for course, highlight, expected, feedback in sessions:
        keys = course.split('=')[1].split('_')
        if len(keys) == 1:
            root = ' Autres'
        else:
            root = keys[0]
        text = ('<a href="/=' + course + '?ticket=' + TICKET
                + '" style="background:' + highlight + '"><span>'
                + course.replace('=','</span> ')
                + '</a>')
        if expected:
            text = '<b>' + text + '</b>'
        if feedback:
            text += ' Examen terminé : ' + [
                None,
                'Vos réponses.',
                'Une correction possible.',
                'Commentaire de votre travail.',
                'Votre note.',
                'Détails de votre note.'][feedback]
        if root not in tree:
            tree[root] = []
            roots.append(root)
        tree[root].append(text)

    roots.sort()
    for root in roots:
        content.append('<p class="root" onclick="toggle(\'' + root + '\')" style="')
        bold = False
        backgrounds = {}
        for item in tree[root]:
            if '<b>' in item:
                bold = True
            if '#FFF' not in item and 'background:' in item:
                backgrounds[item.split('background:')[1].split('"')[0]] = True
        if len(backgrounds) == 1:
            for background in backgrounds:
                break
            content.append('background:' + background + ';') # pylint: disable=undefined-loop-variable
        if bold:
            content.append('font-weight:bold;')
        content.append('">')
        content.append(root)
        content.append('</p>')
        content.append('<ul id="')
        content.append(root)
        content.append('">')
        for item in tree[root]:
            content.append('<li>' + item)
        content.append('</ul>')

    document.body.innerHTML += ''.join(content)

    for ul_elm in document.getElementsByTagName('UL'):
        HEIGHTS[ul_elm.id] = ul_elm.offsetHeight

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

    for ul_elm in document.getElementsByTagName('UL'):
        if ul_elm.id in opens:
            ul_elm.style.height = HEIGHTS[ul_elm.id] + 'px'
            ul_elm.previousSibling.className = 'root open'
        else:
            ul_elm.style.height = '0px'
            ul_elm.previousSibling.className = 'root'
