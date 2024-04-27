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
    TABLE { margin-top: 0px ; margin-bottom: 0px; overflow: hidden;
            border-spacing: 0px;
            table-layout: fixed }
    P { margin: 0.1em }
    P.root:before { content: '▶'; display: inline-block; transition: 0.3s transform }
    P.root.open:before { transform: rotate(90deg) }
    TABLE TD:nth-child(2), TABLE TD:nth-child(3) { padding-left: 0.5em ; padding-right: 0.5em }
    TABLE TR:hover TD { text-decoration: underline }
    TABLE TD:first-child { text-align: right; }
    TABLE TD { padding: 0px; overflow: hidden }
    TABLE P { white-space: nowrap; margin: 0px; max-width: 45vw; height: 1.1em; transition: 0.3s height }
    TABLE.close P { height: 0px;}
    TABLE TR { cursor: pointer; transition: 0.3s opacity; }
    TABLE.close TR { opacity: 0 }
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
    now = millisecs() / 1000
    now_text = nice_date(now)
    for course, highlight, expected, feedback, title, start_timestamp, stop_timestamp, tt in sessions:
        keys = course.split('=')[1].split('_')
        if len(keys) == 1:
            root = ' Autres'
        else:
            root = keys[0]
        text = course.split('=')
        text = '<span style="opacity: 0.3">' + text[0] + '</span> ' + text[1]
        style = "background:" + highlight
        if expected:
            style = ';font-weight: bold'
        text = ('<tr onclick="location = \'/=' + course + '?ticket=' + TICKET
                + '&login=' + LOGIN
                + '\'" style="' + style + '"><td><p>' + text + '<td><p>')
        if title != '':
            text += html(title)
        text += '<td><p>'
        if now < start_timestamp:
            date = nice_date(start_timestamp)
            text += " début à " + date[11:]
            if date[:10] != now_text[:10]:
                text += " le " + date[:10]
            minutes = (stop_timestamp - start_timestamp)/60
            if minutes <= 4*60:
                text += " durée " + minutes + ' minutes'
            else:
                text += " → " + nice_date(stop_timestamp)
            if tt:
                text += ' +⅓ temps'
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
        content.append('<table id="')
        content.append(root)
        content.append('">')
        for item in tree[root]:
            content.append(item)
        content.append('</table>')

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

    for ul_elm in document.getElementsByTagName('TABLE'):
        if ul_elm.id in opens:
            ul_elm.previousSibling.className = 'root open'
            ul_elm.className = 'open'
        else:
            ul_elm.previousSibling.className = 'root close'
            ul_elm.className = 'close'
