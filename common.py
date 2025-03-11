"""
Functions common to Python and Javascript

Overwrittable by xxx_local.py
"""

# pylint: disable=eval-used

def bind(fct, _obj):
    """Bind the function to the object: nothing to do in Python
    But Rapyd script do something.
    So this function is really needed!
    """
    return fct

try:
    Object # pylint: disable=pointless-statement
    def replace_all(txt, regexp, value):
        regexp = regexp.replace(RegExp("\\\\", "g"), "\\\\")
        return txt.replace(RegExp(regexp, "g"), value)
    PYTHON = False
except NameError:
    def replace_all(txt, regexp, value):
        return txt.replace(regexp, value)
    PYTHON = True

def normalize_login(login):
    """In order to have a uniq login string"""
    return login.lower()

def normalize_logins(logins):
    """Normalize logins in a string with separators [ \n\t]"""
    result = ''
    login = ''
    for char in logins:
        if char in ' \n\t':
            result += normalize_login(login) + char
            login = ''
        else:
            login += char
    return result + normalize_login(login)

def student_id(login):
    """Returns the student ID"""
    return login

def protect_crlf(text):
    """Normalize lines separators"""
    return replace_all(replace_all(text, '\r', ''), '\n', '\000')

def unprotect_crlf(text):
    """Recover lines separators"""
    return replace_all(text, '\000', '\n')

POSSIBLE_GRADES = ":([?],)?[-0-9,.]+$"
DELTA_T = 10

if PYTHON:
    import re
    re_match = re.match
    def re_sub(pattern, replacement, string):
        """Only first replacement"""
        return re.sub(pattern, replacement, string, 1)
else:
    def re_match(pattern, string):
        """As in Python"""
        return string.match(RegExp('^' + pattern))
    def re_sub(pattern, replacement, string):
        """Only first replacement"""
        return string.replace(RegExp(pattern), replacement)

def parse_notation(notation):
    """Returns a list or [text, grade_label, [grade_values]]"""
    content = []
    text = ''
    for i, item in enumerate(notation.split('{')):
        options = item.split('}')
        if len(options) == 1 or not re_match('.*' + POSSIBLE_GRADES, options[0]):
            if i != 0:
                text += '{'
            text += item
            continue
        grade_label = re_sub(POSSIBLE_GRADES, '', options[0])
        grade_values = re_sub('.*:', '', options[0]).split(',')
        content.append([text, grade_label, grade_values])
        text = '}'.join(options[1:])
    content.append([text, '', []])
    return content

# Journal management.
# Common between server and browser.
#
# <index> is a line number in the journal. 0 is before anything
# Journal content:
#    'T<seconds>     # Timestamp
#    'O<login> <IP>' # Open connection
#    'C'             # Close connection
#    'G<index>'      # Goto in the past
#    'Q<question>'   # Create question
#    'P<position>'   # Cursor position change in the text
#    'L<line>'       # Line number on screen top
#    'I<text>'       # Insert the text \\ and \n are specials
#    'D<number>'     # Delete the indicated number of characters.
#    '#<text>'       # Debugging information
#    'H<lines>'      # Number of displayed source lines
#    'F'             # Focus
#    'B'             # Blur
#    'S<name>'       # Student saved the source
#    'c<error>'      # 0 if compiled without error message
#    't<tag>'        # Add a tag
#    'g'             # Question passed (good)
#    'b<description> # A bubble comment

class QuestionStats:
    def __init__(self, start):
        self.start = start # <index> of the question creation
        self.head = None # <index> of the last version
        self.tags = [('', start+2)] # List[Tuple[<tag>, <index>]]
        self.good = False
        self.source_old = self.source = self.last_tagged_source = ''
        self.zoom = 6 # Maximum version tree zoom
    def dump(self):
        return f'start={self.start}, head={self.head}, good={self.good}, bytes={len(self.source)}, {self.tags}'

class Bubble:
    last_comment_change = None # Line number of the last comment change
    def __init__(self, description):
        items = description.split(' ')
        self.login = items[0]
        self.pos_start, self.pos_end, self.line, self.column, self.width, self.height = [float(i) for i in items[1:7]]
        self.comment = unprotect_crlf(' '.join(items[7:]))
    def str(self):
        return self.login+' '+self.pos_start+' '+self.pos_end+' '+self.line+' '+self.column+' '+self.width+' '+self.height+' '+self.comment
class Journal:
    position = content = scroll_line = height = remote_update = question = None
    _tree = _tree_question = last_event = None
    timestamp = 0
    def __init__(self, journal=''):
        self.actions = {
            'G': bind(self.action_G, self),
            'T': bind(self.action_T, self),
            'Q': bind(self.action_Q, self),
            'P': bind(self.action_P, self),
            'L': bind(self.action_L, self),
            'I': bind(self.action_I, self),
            'D': bind(self.action_D, self),
            'O': bind(self.action_O, self),
            'C': bind(self.action_C, self),
            'H': bind(self.action_H, self),
            'S': bind(self.action_S, self),
            '#': bind(self.action_debug, self),
            'c': bind(self.action_c, self),
            'g': bind(self.action_g, self),
            't': bind(self.action_t, self),
            'F': bind(self.action_F, self),
            'B': bind(self.action_B, self),
            'b': bind(self.action_b, self),
        }
        self.questions = {}
        self.cache = {}
        self.action_Q(-42, 0) # -1 does not work
        if journal == '' or journal == '\n':
            self.lines = []
        else:
            self.lines = journal.split('\n')
            self.lines.pop()
        self.children = []
        self.bubbles = []
        self.timestamps = []
        self.clear_pending_goto()
        self.evaluate(self.lines, 0)
    def clear_pending_goto(self):
        """No currently pending goto in the past"""
        self.pending_goto = False
        self.pending_goto_history = []
    def get_question(self, index):
        """Get journal position for a question"""
        return self.questions[index]
    def action_Q(self, value, start):
        """New question"""
        if start:
            self.children[start-1] = []
        self.content = ''
        self.position = 0
        self.scroll_line = 0
        self.question = int(value)
        if self.question not in self.questions:
            self.questions[self.question] = QuestionStats(start)
    def action_P(self, value, _start):
        """Cursor position, 0 is before first char"""
        self.position = int(value)
    def action_L(self, scroll_line, _start):
        """The line number at the screen top"""
        self.scroll_line = int(scroll_line)
    def action_H(self, height, _start):
        """Number of displayed source line"""
        self.height = int(height)
    def action_t(self, tag, start):
        """Tag"""
        self.questions[self.question].tags.append((tag, start + 1)) # overwrite Save position
        self.questions[self.question].last_tagged_source = self.content
    def action_I(self, value, _start):
        """Text insert"""
        string = unprotect_crlf(value)
        self.content = self.content[:self.position] + string + self.content[self.position:]
        size = len(string)
        for bubble in self.bubbles:
            if bubble.pos_end > self.position:
                bubble.pos_end += size
                if bubble.pos_start >= self.position:
                    bubble.pos_start += size
        self.position += size
    def action_D(self, value, _start):
        """Text delete"""
        value = int(value)
        for bubble in self.bubbles:
            if bubble.pos_end > self.position:
                bubble.pos_end -= value
                if bubble.pos_end < self.position:
                    bubble.pos_end = self.position
                if bubble.pos_start >= self.position:
                    bubble.pos_start -= value
                    if bubble.pos_start < self.position:
                        bubble.pos_start = self.position
        self.bubbles = [bubble
                        for bubble in self.bubbles
                        if bubble.pos_end > bubble.pos_start
                       ]
        self.content = self.content[:self.position] + self.content[self.position + value:]
    def update_tree(self, value, start):
        """Update tree"""
        if start is None:
            return
        self.children[start-1] = []
        self.children[int(value) - 1].append(start)
    def action_G(self, value, start):
        """Goto in the past.
        The value is index of the line after the goal"""
        if value in self.cache:
            self.position, self.content, self.scroll_line, self.height, self.question, bubbles = self.cache[value]
            self.bubbles = [Bubble(i) for i in bubbles]
            self.update_tree(value, start)
            return
        index = int(value) - 1
        lines = []
        while True:
            line = self.lines[index]
            action = line[0]
            if action in 'PIDLb': # Position/Insert/Delete/Line/Bubble
                lines.append(line)
                index -= 1
            elif action in 'TOC#HScgtFB':
                # Time/Open/Close/Debug/Height/compile/good/tag/Focus/Blur
                index -= 1
                if index < 0:
                    break
            elif action == 'G':
                index = int(line[1:]) - 1
                if index < 0:
                    break
            elif action == 'Q':
                lines.append(line)
                break
            else:
                raise ValueError('Unexpected :' + action)
        self.bubbles = []
        self.evaluate_fast(lines[::-1])
        self.cache[value] = (self.position, self.content, self.scroll_line, self.height, self.question, [i.str() for i in self.bubbles])
        self.update_tree(value, start)

    def action_T(self, value, _start):
        """Update time"""
        self.timestamp = value
    def action_O(self, _value, _start):
        """Session open login and IP"""
    def action_C(self, _value, _start):
        """Session close"""
    def action_F(self, _value, _start):
        """Focus"""
    def action_B(self, _value, _start):
        """Blur"""
    def action_debug(self, _value, _start):
        """Do nothing: debug message in the logs"""
    def action_S(self, _value, _start):
        """Student asked to save"""
    def action_c(self, _value, _start):
        """Last compilation result, currently unused"""
    def action_g(self, _value, _start):
        """Question passed test (no argument)"""
        self.questions[self.question].good = True
    def action_b(self, value, start):
        """Add a bubble or update it"""
        if value.startswith('+'):
            self.bubbles.append(Bubble(value[1:]))
            return
        changes = value[1:].split(' ')
        bubble_index = int(changes[0])
        bubble = self.bubbles[bubble_index]
        if value.startswith('P'):
            bubble.line = float(changes[1])
            bubble.column = float(changes[2])
        elif value.startswith('S'):
            bubble.width = float(changes[1])
            bubble.height = float(changes[2])
        elif value.startswith('C'):
            bubble.comment = unprotect_crlf(' '.join(changes[1:]))
            bubble.last_comment_change = start
        elif value.startswith('-'):
            bubble.login = ''
        else:
            raise ValueError('Bad journal')

    def evaluate_fast(self, lines):
        """Evaluate all these lines in the current state"""
        for line in lines:
            self.actions[line[0]](line[1:], None)

    def evaluate(self, lines, start):
        """Evaluate for the first time"""
        for line in lines:
            self.actions[line[0]](line[1:], start)
            start += 1
            question = self.questions[self.question]
            question.head = start
            question.source_old = question.source
            question.source = self.content
            self.children.append([start])
            self.timestamps.append(self.timestamp)

    def append(self, line):
        """Add a line in the journal"""
        self.lines.append(line)
        self.evaluate([line], len(self.lines)-1)
        self._tree = None

    def pop(self):
        """Remove the last action."""
        old = self.lines.pop()
        if old.startswith('G'):
            self.children[int(old[1:]) - 1].pop()
            self.children.pop()
            self.children[-1].append(len(self.lines))
            # The ^Z does not change the question and is always at the end.
            question = self.questions[self.question]
            question.head -= 1
            question.source = question.source_old
            self.action_G(len(self.lines), None) # Update content
            self.pending_goto = False
            self._tree = None
            return old
        raise ValueError('Unexpected pop')

    def compute_tree(self, start):
        """Return a version tree for human.
            [<index>, width, height, ...children...]
        """
        tree = [start, 0, 0]
        todo = [tree]
        nodes = [tree]

        def add(index):
            # Jump over not interesting things
            if index < len(self.lines) and self.lines[index][0] in 'GTBFLPH':
                for i in self.children[index]:
                    add(i)
                return
            if index == len(self.lines):
                todo.append([index, 0, 1])
            else:
                todo.append([index, 1, 1])
            item.append(todo[-1])
            nodes.append(todo[-1])

        while len(todo):
            item = todo.pop()
            if item[0] < len(self.children):
                for j in self.children[item[0]]:
                    add(j)

        # Compute sizes
        for node in nodes[::-1]: # From leaves to root
            if len(node) > 3:
                node[1] = 1 + node[3][1]
                height = 0
                for kid in node[3:]:
                    height += kid[2]
                node[2] = height

        # longuest firsts
        for node in nodes[::-1]: # From leaves to root
            if len(node) > 3:
                if len(node) > 4: # >= 2 children
                    swaped = True
                    while swaped:
                        swaped = False
                        for i in range(4, len(node)):
                            if node[i-1][1] < node[i][1]:
                                node[i], node[i-1] = node[i-1], node[i]
                                swaped = True
                node[1] = node[3][1] + 1

        return tree

    def parent_position(self, position):
        """Get the parent position"""
        for i, children in enumerate(self.children):
            if position in children:
                if self.lines[i][0] in 'GOTFB':
                    return self.parent_position(i)
                if self.lines[i][0] == 'Q':
                    return position
                return i
        if position:
            return position - 1
        return 0 # not beyond the root

    def tree(self):
        if not self._tree or self._tree_question != self.question:
            self._tree_question = self.question
            self._tree = self.compute_tree(self.questions[self.question].start)
        return self._tree

    def tree_text(self, tree=None):
        """Returns an ascii art for debugging"""
        if tree is None:
            tree = self.tree()
        if tree[0] < len(self.lines):
            action = self.lines[tree[0]][0]
        else:
            action = '*'
        if len(tree) == 3:
            return [action] # No child
        lines = []
        heads = []
        for child in tree[3:]:
            heads.append(len(lines))
            for line in self.tree_text(child):
                lines.append(line)
        lines[0] = action + lines[0]
        previous = 0
        for head in heads[1:]:
            for line in range(previous + 1, head):
                lines[line] = '|' + lines[line]
            lines[head] = '└' + lines[head]
            previous = head
        for line in range(heads[-1]+1, len(lines)):
            lines[line] = ' ' + lines[line]
        return lines

    def tree_dump(self, tree=None, texts=None, indent=None):
        """Returns an ascii art for debugging"""
        if tree is None:
            tree = self.tree()
            texts = []
            self.tree_dump(self.tree(), texts, '')
            return '\n'.join(texts)
        if tree[0] < len(self.lines):
            action = self.lines[tree[0]][0]
        else:
            action = '*'
        texts.append(indent + tree[0] + ' ' + tree[1] + ' ' + tree[2] + ' : ' + action)
        indent = '    ' + indent
        for child in tree[3:]:
            self.tree_dump(child, texts, indent)

    def explain(self, used_lines):
        """Explain the journal content for version feedback"""
        lines = []
        for line in used_lines:
            line = self.lines[line]
            if not line:
                continue
            if line.startswith('I'):
                text = 'Insertion de ' + (len(line)-1) + ' caractères'
            elif line.startswith('D'):
                text = 'Destruction de ' + line[1:] + ' caractères'
            elif line.startswith('b+'):
                text = 'Commentaire créé par «' + line[2:].split(' ')[0] + '»'
            elif line.startswith('bP'):
                text = 'Commentaire deplacé'
            elif line.startswith('bS'):
                text = 'Changement taille commentaire'
            elif line.startswith('b-'):
                text = 'Commentaire détruit'
            elif line.startswith('bC'):
                text = 'Changement du commentaire : «' + html(line[2:].replace(RegExp('[0-9]* '), '')) + '»'
            elif line.startswith('g'):
                text = "Objectif de l'exercice atteint"
            elif line.startswith('t') or line.startswith('S'):
                text = 'Sauvegarde'
            elif line.startswith('O'):
                infos = line[1:].split(' ')
                text = 'Connexion de «' + infos[0] + '»'
            elif line.startswith('c0'):
                text = 'Compilation sans aucun problème'
            elif line.startswith('c'):
                i = int(line[1:])
                text = 'Compilation avec ' + int(i/100) + ' erreurs et ' + i%100 + ' warnings'
            else:
                continue
            lines.append(text)
        lines = ['<br>'.join(lines)]
        if SESSION_LOGIN in CONFIG['roots']:
            lines.append('<pre style="font-size: 50%">')
            done = {}
            def line_text(i):
                done[i] = True
                return (str(i) + ' '
                    + self.timestamps[i] + ' '
                    + self.children[i] + ' '
                    + html(self.lines[i] or '')
                    + '\n')
            next_one = used_lines[0]
            for i in used_lines:
                if next_one != i:
                    lines.append(line_text(next_one))
                    if next_one+1 != i:
                        lines.append('...\n')
                if not done[i-1]:
                    lines.append(line_text(i-1))
                lines.append('<b>' + line_text(i) + '</b>')
                next_one = int(i)+1
            lines.append(line_text(next_one))
        return ('<div style="text-align:right">'
            + nice_date(self.timestamps[used_lines[0]], secs=True)
            + '</div>' + ''.join(lines))

    def tree_canvas(self, canvas, event=None):
        """Draw tree in canvas.
        Return selected item"""
        if canvas.parentNode.offsetWidth == 0 or canvas.parentNode.offsetHeight == 0:
            return
        tree = self.tree()
        zoom = max(2, min(int(canvas.parentNode.offsetWidth / tree[1]),
                          int(canvas.parentNode.offsetHeight / tree[2] / 12),
                          self.questions[self.question].zoom))
        self.questions[self.question].zoom = zoom
        font_size = zoom * 12 # Font size
        ascent = -font_size / 4
        descent = font_size / 10
        size = int(font_size + ascent + descent) # Full line height with font ascent and descent
        middle = int(size / 2) + 1
        center = zoom/2 - 0.5
        arrow = zoom * 1 # Arrow size
        padding = int(font_size / 2)
        def draw_ID(_action, x, y):
            """Some Insert and deletes"""
            znb_i = nb_i * zoom
            znb_d = nb_d * zoom
            nb_id = znb_i + znb_d
            if nb_id > middle:
                nb_id = zoom / nb_id * 2
                znb_i *= nb_id
                znb_d *= nb_id

            x += center
            y -= 0.5
            ctx.strokeStyle = '#F88'
            ctx.beginPath()
            ctx.moveTo(x, y)
            y -= znb_d
            ctx.lineTo(x, y)
            ctx.stroke()
            ctx.strokeStyle = '#8F8'
            ctx.beginPath()
            ctx.moveTo(x, y)
            y -= znb_i
            ctx.lineTo(x, y)
            ctx.stroke()
            return zoom
        def draw_c(action, x, y):
            "Compilation"
            value = int(action[1:])
            if value == 0:
                ctx.fillStyle = '#0F0'
            elif value < 100:
                ctx.fillStyle = '#FA0'
            else:
                ctx.fillStyle = '#F00'
            ctx.fillRect(x+center - 0.5*zoom, y - size + 0.5, 4*zoom, middle)
            return 4*zoom
        def draw_O(_action, x, y):
            "Connection"
            ctx.strokeStyle = '#88F'
            ctx.beginPath()
            ctx.moveTo(x+center, y - 3*size/4 + 0.5)
            ctx.lineTo(x+center, y - size/4 - 0.5)
            ctx.stroke()
            return zoom
        def draw_t(action, x, y):
            "Tag"
            ctx.font = font_size + "px sans"
            char = action[1:]
            width = ctx.measureText(char).width
            ctx.fillStyle = '#DDD'
            ctx.beginPath()
            ctx.rect(x - 0.5, y - size + 0.5, width + 1, size - 1)
            ctx.fill()
            ctx.fillStyle = '#00F'
            ctx.fillText(char, x, y - descent)
            return int(width) + 1
        def draw_char(char, x, y):
            """An icon"""
            ctx.font = font_size + "px emoji"
            ctx.fillStyle = '#000'
            ctx.fillText(char, x, y - descent - 1)
            return int(ctx.measureText(char).width)
        def draw_b(_action, x, y):
            return draw_char('#', x, y)
        def draw_S(_action, x, y):
            return draw_char('📩', x, y)
        def draw_g(_action, x, y):
            return draw_char('👍', x, y)
        def draw_hand(_action, x, y):
            return draw_char('✍', x, y)
        def draw_nothing(_action, x, y):
            return 0
        draw = {
            'D': draw_ID, 'I': draw_ID, 'c': draw_c, 't': draw_t,
            'Q': draw_nothing, 'L': draw_nothing, 'P': draw_nothing, 'T': draw_nothing,
            'H': draw_nothing, '#': draw_nothing, 'G': draw_nothing, 'F': draw_nothing,
            'B': draw_nothing,
            'b': draw_b, 'O': draw_O, 'S': draw_S, 'g': draw_g, '✍': draw_hand,
        }
        if canvas.width != canvas.offsetWidth:
            canvas.width = canvas.offsetWidth
        if canvas.height != canvas.offsetHeight:
            canvas.height = canvas.offsetHeight
        ctx = canvas.getContext("2d")
        ctx.fillStyle = '#FFF'
        ctx.strokeStyle = '#000'
        ctx.fillRect(0, 0, 10000, 10000)
        if event:
            buttons = event.buttons
        else:
            buttons = None
        if not event and self.last_event:
            # The box click trigger coloring, but the highlighted box
            # must stay highlighted on the next draw.
            event = self.last_event
        if event:
            rect = event.target.getBoundingClientRect()
            mouse_x = event.clientX - rect.x
            mouse_y = event.clientY - rect.y
        else:
            mouse_x = mouse_y = 0
        self.last_event = None
        feedback = [None]
        ctx.lineWidth = zoom

        todo = [[tree, 0.5, size + 0.5]]
        while len(todo):
            tree, x, y = todo.pop()
            action = self.lines[tree[0]] or '✍'
            if len(tree) == 4:
                # BEWARE timestamp are recorded every DELTA_T seconds
                # So checking a 1 second delta has no sense.
                # See: 'shared_worker_post'
                timestamp = self.timestamps[tree[0]]
            else:
                timestamp = 0
            char = action[0]
            lines = [tree[0]]
            if char == 'I':
                nb_i = 1
            else:
                nb_i = 0
            if char == 'D':
                nb_d = 1
            else:
                nb_d = 0
            if char in ('I', 'D', 'P', 'L', 'H'):
                while len(tree) == 4: # Merge only if there is no branch
                    next_line = tree[3][0]
                    if not self.lines[next_line]:
                        break
                    if self.timestamps[next_line] != timestamp:
                        break # Not same (DELTA_T) second
                    next_char = self.lines[next_line][0]
                    if next_char not in ('I', 'D', 'P', 'L', 'H'):
                        break # Only merge D and I and P
                    char = next_char
                    if char == 'I':
                        nb_i += 1
                    elif char == 'D':
                        nb_d += 1
                    tree = tree[3]
                    lines.append(tree[0])
            width = draw[char](action, x, y)
            if width > 0:
                if mouse_y < y and mouse_y >= y-size+1 and mouse_x >= x and char != '✍':
                    feedback[0] = (x, y, width, tree[0] + 1, lines)
                x += width
            for i, child in enumerate(tree[3:]):
                if i > 0:
                    x += padding - width/2
                    x = int(x) + 0.5
                todo.append([child, x, y])
                dy = child[2] * size
                if i > 0:
                    ctx.lineWidth = 1
                    startx = int(x - padding) - 0.5
                    endy = int(y - size/2) + 0.5
                    endx = startx + padding
                    ctx.strokeStyle = '#000'
                    ctx.beginPath()
                    ctx.moveTo(startx, y_start)
                    ctx.lineTo(startx, endy)
                    ctx.lineTo(endx, endy)
                    ctx.lineTo(endx, endy)
                    ctx.lineTo(endx - arrow, endy - arrow)
                    ctx.lineTo(endx - arrow, endy + arrow)
                    ctx.lineTo(endx, endy)
                    ctx.stroke()
                    ctx.lineWidth = zoom
                else:
                    y_start = y
                y += dy

        if feedback[0]:
            x, y, width, line, lines = feedback[0]
            ctx.lineWidth = 1
            ctx.strokeStyle = '#000'
            ctx.beginPath()
            ctx.rect(x-1, y-size, width+1, size)
            ctx.stroke()
            ccccc.version_feedback.innerHTML = self.explain(lines)
            ccccc.version_feedback.style.display = 'block'
            if buttons:
                # if (mouse_x < x+width or len(tree[3:])==0):
                self.last_event = event
                ccccc.goto_line(line)
        else:
            ccccc.version_feedback.style.display = 'none'
        return x

    def see_past(self, index):
        """Look in the past, but will come back to present"""
        if self.pending_goto:
            # Remove the previous see_past
            self.pop()
        if index == len(self.lines):
            # The asked past is the present
            # So we are not in the past
            return
        # if index < 3:
        #     index = 3 # Not before the question
        line = 'G' + str(index)
        if self.lines[-1] != line: # Not coming back to present
            self.pending_goto = index
            self.append(line)

    def infos(self):
        """Generic info about journal"""
        texts = [
            'position ' + str(self.position),
            'content ' + repr(self.content)[:50],
            'scroll_line ' + str(self.scroll_line),
            'height ' + str(self.height),
            'remote_update ' + str(self.remote_update),
            'question ' + str(self.question),
            'timestamp ' + str(self.timestamp)
        ]
        for i, question in sorted(self.questions.items()):
            if i >= 0:
                texts.append(str(i) + ' ' + question.dump())
        for line in self.tree_text():
            texts.append(line)
        return texts

    def dump(self):
        """Display journal content"""
        all_left = list(self.lines)
        all_right = list(self.infos())
        lines = max(len(all_left), len(all_right))
        while len(all_left) < lines:
            all_left.append('')
        while len(all_right) < lines:
            all_right.append('')

        i = 0
        for left, right in zip(all_left, all_right):
            print(('   ' + str(i))[-3:] + ' '
                  + repr(left+'                                  ')[1:20]
                  + ' ' + right)
            i += 1

def journal_regtest():
    try:
        Math.floor
    except:
        class JSON:
            pass
        json = __import__('json')
        JSON.stringify = lambda x: json.dumps(x)
    test = """
               line   content position question
             0 'Q0'     ''       '0'     '0' # Create question Q0
          ┌─>1 'Ib'     'b'      '1'     '0' # Insert a character at the current position
     ┌───>│  2 'Q1'     ''       '0'     '1' # Create question Q1
     │    │  3 'Ic'     'c'      '1'     '1'
┌───>|>┌─>└─ 4 'G1'     ''       '0'     '0' # Returns to Q0 but not last version
│    │ │     5 'Id'     'd'      '1'     '0'
│ ┌─>│>└──── 6 'G4'     'c'      '1'     '1' # Returns to Q1
│ │  └────── 7 'G2'     'b'      '1'     '0' # Returns to Q0 "last" version
│ │          8 'Ie'     'be'     '2'     '0'
│ └───────── 9 'G6'     'd'      '1'     '0' # Returns to Q0 "alternative" version
│           10 'I\\000' 'd\\n'   '2'     '0' # \\n are replaced by NUL in the journal
│           11 'P0'     'd\\n'   '0'     '0' # Change cursor position
│           12 'Ifg'    'fgd\\n' '2'     '0'
│        ┌─>13 'D1'     'fg\\n'  '2'     '0' # Delete 1 char
│        │  14 'P3'     'fg\\n'  '3'     '0'
│        │  15 'Ih'     'fg\\nh' '4'     '0'
│        └─ 16 'G13'    'fgd\\n' '2'     '0'
│           17 'P0'     'fgd\\n' '0'     '0' # Change cursor position
└────────── 18 'G4'     'c'      '1'     '1'
            19 'I+'     'c+'     '2'     '1'
            20 'I+'     'c++'    '3'     '1'
            21 'I+'     'c+++'   '4'     '1'
"""

    journa = Journal()
    for line in test.strip().split('\n')[1:]:
        _, line, _, expect_content, _, expect_position, _, expect_question, _ = line.split("'")
        journa.append(eval("'" + line + "'"))
        expect_content = "'" + expect_content +  "'"
        if journa.content != eval(expect_content):
            print('Computed content', journa.content)
            print('Expected content', expect_content)
            raise ValueError("Bad content")
        if journa.position != int(expect_position):
            print('Computed position', journa.position)
            print('Expected position', expect_position)
            raise ValueError("Bad position")
        if journa.question != int(expect_question):
            print('Computed question', journa.question)
            print('Expected question', expect_question)
            raise ValueError("Bad question")

    if journa.children != [[1,4],[7],[3],[6,18],[5],[9],[],[8],[],[10],[11],[12],[13,16],[14],[15],[],[17],[],[19],[20],[21],[22]]:
        print(journa.children)
        raise ValueError("Bad children")

    for lines, expect in [
[["Q0"], [
  [[0, 1, 1, [1, 0, 1]],
   "Q*\n"
  ],
 ]],
[["Q0", "Ia"], [
  [[0, 2, 1, [1, 1, 1, [2, 0, 1]]],
   "QI*\n"
  ],
 ]],
[["Q0", "Ia", "Ib"], [
  [[0, 3, 1, [1, 2, 1, [2, 1, 1, [3, 0, 1]]]],
   "QII*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Q1"], [
  [[0, 3, 1, [1, 2, 1, [2, 1, 1]]],
   "QII\n"
  ],
  [[3, 1, 1, [4, 0, 1]],
   "Q*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Q1", "Ic"], [
  [[0, 3, 1, [1, 2, 1, [2, 1, 1]]],
   "QII\n"
  ],
  [[3, 2, 1, [4, 1, 1, [5, 0, 1]]],
   "QI*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Q1", "Ic", "G3", "Id"], [
  [[0, 4, 1, [1, 3, 1, [2, 2, 1, [6, 1, 1, [7, 0, 1]]]]],
   "QIII*\n"
  ],
  [[3, 2, 1, [4, 1, 1]],
   "QI\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Q1", "Ic", "G3", "Id", "G5", "Ie"], [
  [[0, 4, 1, [1, 3, 1, [2, 2, 1, [6, 1, 1]]]],
   "QIII\n"
  ],
  [[3, 3, 1, [4, 2, 1, [8, 1, 1, [9, 0, 1]]]],
   "QII*\n"
  ],
 ]],
[["Q0", "Ia", "G1", "Ib"], [
  [[0, 2, 2, [1, 1, 1], [3, 1, 1, [4, 0, 1]]],
   "QI\n" +
   "└I*\n"
  ],
 ]],
[["Q0", "Ia", "G1", "Ib", "Ic"], [
  [[0, 3, 2, [3, 2, 1, [4, 1, 1, [5, 0, 1]]], [1, 1, 1]],
   "QII*\n" +
   "└I\n"
  ],
 ]],
[["Q0", "Ia", "G1", "Ib", "Ic", "Id"], [
  [[0, 4, 2, [3, 3, 1, [4, 2, 1, [5, 1, 1, [6, 0, 1]]]], [1, 1, 1]],
   "QIII*\n" +
   "└I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G1", "Ic", "Id"], [
  [[0, 3, 2, [1, 2, 1, [2, 1, 1]], [4, 2, 1, [5, 1, 1, [6, 0, 1]]]],
   "QII\n" +
   "└II*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G1", "Ic", "Id", "G1", "Ie"], [
  [[0, 3, 3, [1, 2, 1, [2, 1, 1]], [4, 2, 1, [5, 1, 1]], [7, 1, 1, [8, 0, 1]]],
   "QII\n" +
   "└II\n" +
   "└I*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G1", "Ic", "Id", "G1", "Ie", "G3", "If"], [
  [[0, 4, 3, [1, 3, 1, [2, 2, 1, [9, 1, 1, [10, 0, 1]]]], [4, 2, 1, [5, 1, 1]], [7, 1, 1]],
   "QIII*\n" +
   "└II\n" +
   "└I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G1", "Ic", "Id", "G1", "Ie", "G6", "If"], [
  [[0, 4, 3, [4, 3, 1, [5, 2, 1, [9, 1, 1, [10, 0, 1]]]], [1, 2, 1, [2, 1, 1]], [7, 1, 1]],
   "QIII*\n" +
   "└II\n" +
   "└I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G1", "Ic", "Id", "G1", "Ie", "G8", "If"], [
  [[0, 3, 3, [1, 2, 1, [2, 1, 1]], [4, 2, 1, [5, 1, 1]], [7, 2, 1, [9, 1, 1, [10, 0, 1]]]],
   "QII\n" +
   "└II\n" +
   "└II*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "G2", "Id"], [
  [[0, 4, 2, [1, 3, 2, [2, 2, 1, [3, 1, 1]], [5, 1, 1, [6, 0, 1]]]],
   "QIII\n" +
   " └I*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "G3", "Id"], [
  [[0, 4, 2, [1, 3, 2, [2, 2, 2, [3, 1, 1], [5, 1, 1, [6, 0, 1]]]]],
   "QIII\n" +
   "  └I*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "G2", "Ic", "Id", "Ie", "If"], [
  [[0, 6, 2, [1, 5, 2, [4, 4, 1, [5, 3, 1, [6, 2, 1, [7, 1, 1, [8, 0, 1]]]]], [2, 1, 1]]],
   "QIIIII*\n" +
   " └I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "G2", "Id", "G3", "Ie", "If"], [
  [[0, 5, 3, [1, 4, 3, [2, 3, 2, [7, 2, 1, [8, 1, 1, [9, 0, 1]]], [3, 1, 1]], [5, 1, 1]]],
   "QIIII*\n" +
   " |└I\n" +
   " └I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "G3", "Id", "G2", "Ie", "If"], [
  [[0, 4, 3, [1, 3, 3, [2, 2, 2, [3, 1, 1], [5, 1, 1]], [7, 2, 1, [8, 1, 1, [9, 0, 1]]]]],
   "QIII\n" +
   " |└I\n" +
   " └II*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "Id", "G2", "Ie", "If", "G3", "Ig"], [
  [[0, 5, 3, [1, 4, 3, [2, 3, 2, [3, 2, 1, [4, 1, 1]], [9, 1, 1, [10, 0, 1]]], [6, 2, 1, [7, 1, 1]]]],
   "QIIII\n" +
   " |└I*\n" +
   " └II\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "P0", "G4", "P0", "G3", "If", "P0", "G9", "P0", "G2", "Ii", "Ij", "P0", "G15", "P0", "G14", "Im", "P0"], [
  [[0, 4, 4, [1, 3, 4, [2, 2, 2, [3, 1, 1], [8, 1, 1]], [13, 2, 2, [14, 1, 1], [19, 1, 1, [21, 0, 1]]]]],
   "QIII\n" +
   " |└I\n" +
   " └II\n" +
   "  └I*\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "Id", "G2", "Ie", "G4", "If"], [
  [[0, 5, 3, [1, 4, 3, [2, 3, 2, [3, 2, 2, [4, 1, 1], [8, 1, 1, [9, 0, 1]]]], [6, 1, 1]]],
   "QIIII\n" +
   " | └I*\n" +
   " └I\n"
  ],
 ]],
[["Q0", "Ia", "Ib", "Ic", "Id", "G4", "Ie", "G2", "If"], [
  [[0, 5, 3, [1, 4, 3, [2, 3, 2, [3, 2, 2, [4, 1, 1], [6, 1, 1]]], [8, 1, 1, [9, 0, 1]]]],
   "QIIII\n" +
   " | └I\n" +
   " └I*\n"
  ],
 ]],
[["Q0", "Ia", "g", "Q1", "Id", "G3", "G2"], [
  [[0, 3, 2, [1, 2, 2, [2, 1, 1], [7, 0, 1]]],
   "QIg\n" +
   " └*\n"
  ],
  [[3, 2, 1, [4, 1, 1]],
   "QI\n"
  ],
 ]],
[["Q0", "tA", "G1", "tB", "G3", "tC"], [
  [[0, 2, 3, [1, 1, 1], [3, 1, 1], [5, 1, 1, [6, 0, 1]]],
   "Qt\n" +
   "└t\n" +
   "└t*\n"
  ],
 ]],
        ]:
        journa = Journal()
        journa.lines = lines
        journa.evaluate(lines, 0)
        if False: # Make it True to update resulats of all tests above
            text = '[' + JSON.stringify(lines) + ', [\n'
            for i in range(len(journa.questions)-1):
                journa.question = i
                text += '  [' + JSON.stringify(journa.tree()) + ',\n'
                remove = False
                for line in journa.tree_text():
                    text += '   ' + JSON.stringify(line)[:-1].replace('\\u2514', '└') + '\\n" +\n'
                    remove = True
                if remove:
                    text = text[:-3] + '\n'
                text += '  ],\n'
            text += ' ]],'
            print(text)
            continue
        for i, item in enumerate(expect):
            tree, tree2 = item
            journa.question = i
            if journa.tree() != tree:
                print('journal:', JSON.stringify(lines))
                print('children:', JSON.stringify(journa.children))
                print('expected:', JSON.stringify(tree))
                print('computed:', JSON.stringify(journa.tree()))
                raise ValueError('Bad tree')

            if journa.tree_text() != tree2[:-1].split('\n'):
                print('journal:', JSON.stringify(lines))
                print('children:', JSON.stringify(journa.children))
                print('lines:', JSON.stringify(journa.tree()))
                print('expected:', JSON.stringify(tree2))
                print('computed:', JSON.stringify(journa.tree_text()))
                raise ValueError('Bad tree')
    original_children = str(journa.children)
    for i in [5, 4, 3, 4, 5, 4, 4, 5, 5]:
        journa.see_past(i)
    journa.see_past(len(journa.lines)-1)
    if original_children != str(journa.children):
        raise ValueError('bug')

    for lines, expected_parents in [
        [["Q0","Ia","Ib","Ic","Id","G4","Ie","G2","If"],
         [ 0,   1,   1,   2,   3,   3,   3,   1,   1 ]
        ],
        [["Q0","Ia","Q1","Ib","G2","IA","G4","IB", "G6"],
         [ 0,   1,   1,   3,   1,   1,   3,   3,   5]
        ],
    ]:
        journa = Journal()
        journa.lines = lines
        journa.evaluate(journa.lines, 0)
        parents = [journa.parent_position(i) for i in range(len(journa.lines))]
        if expected_parents != parents:
            print("children", JSON.stringify(journa.children))
            print("expected", JSON.stringify(expected_parents))
            print("computed", JSON.stringify(parents))
            raise ValueError('bug')

journal_regtest()

def create_shared_worker(login='', hook=None):
    print("Start shared worker for communication")
    journal = Journal()
    print(millisecs())
    shared_worker = eval('new SharedWorker("live_link.js' + window.location.search + '")')
    def reload_page(message):
        # Firefox 129 bug? The alert function does not returns
        setTimeout(bind(window.location.reload, window.location), 5000)
        shared_worker.port.close()
        alert(message + "\nLa page va être rechargée.")
        window.location.reload()
    def shared_worker_message(event):
        """Message from the shared worker"""
        if event.data.startswith('J'):
            journal.__init__(event.data[1:])
            print('Init journal: ' + len(journal.lines) + ' lines')
            journal.remote_update = True
            if hook:
                hook(journal)
            try:
                ccccc.init()
            except ReferenceError:
                pass # ccccc does not exist (checkpoint spy)
        elif event.data.startswith('M'):
            print("SHARED WORKER SAYS:", event.data[1:])
        elif event.data.startswith('R'):
            reload_page("Le serveur a été arrêté pour une maintenance.")
        else:
            try:
                ccccc.save_button.setAttribute('state', 'ok')
            except: # pylint: disable=bare-except
                pass # ccccc does not exist (checkpoint spy)
            msg_id = event.data.split(' ')[0]
            message = event.data.replace(RegExp('[0-9]* '), '')
            if journal.lines[msg_id] == message:
                print("Local change")
                return
            try:
                if journal.pending_goto:
                    journal.pop() # The local history is in the past
                    journal.clear_pending_goto()
            except ReferenceError:
                pass # ccccc does not exist (checkpoint spy)
            if window.GRADING and ccccc.add_comments == 0 and ccccc.editmode:
                ccccc.set_editmode(1) # Keep commented version synchronized
                ccccc.editmode.selectedIndex = 1
            if int(msg_id) != len(journal.lines):
                ccccc.record_error('DESYNC')
                reload_page("Désynchronisation avec le serveur. " + msg_id + ' != ' + len(journal.lines))
                window.location.reload()
            print("Add line to journal: " + message)
            if message.startswith('#bonus_time '):
                ccccc.stop_timestamp = int(message.split(' ')[2])
            journal.append(message)
            journal.remote_update = True
            if hook:
                hook(journal)
    def shared_worker_post(message):
        """Send a message to the journal"""
        if GRADING and not (ccccc.add_comments and message[0] in 'GbTtLH'):
            print('Not recording ' + message)
            journal.append(message)
            return # To keep journals in sync
        else:
            print('Post ' + message)
            if not message.startswith('T'):
                t = int(millisecs() / 1000)
                if t - journal.timestamp > DELTA_T: # Record a timestamp sometime
                    shared_worker.timestamp(t)
            shared_worker.port.postMessage(len(journal.lines) + ' ' + message)
        journal.append(message)
    shared_worker.post = shared_worker_post
    def shared_worker_timestamp(seconds):
        """Record current time"""
        shared_worker.post('T' + seconds)
    shared_worker.timestamp = shared_worker_timestamp
    def shared_worker_focus():
        """Record current time"""
        shared_worker_timestamp(int(millisecs() / 1000))
        shared_worker.post('F')
    shared_worker.focus = shared_worker_focus
    def shared_worker_blur():
        """Record current time"""
        shared_worker_timestamp(int(millisecs() / 1000))
        shared_worker.post('B')
    shared_worker.blur = shared_worker_blur
    def shared_worker_insert(position, text):
        """Insert text"""
        if journal.position != position:
            shared_worker.post('P' + position)
        shared_worker.post('I' + protect_crlf(text))
    shared_worker.insert = shared_worker_insert
    def shared_worker_delete(position, length):
        """Delete text"""
        if journal.position != position:
            shared_worker.post('P' + position)
        shared_worker.post('D' + length)
    shared_worker.delete_nr = shared_worker_delete
    def shared_worker_question(index):
        """Change question.
        Returns True if it is NOT the first time"""
        question = journal.get_question(index)
        if question:
            if question.head != len(journal.lines):
                shared_worker.post('G' + question.head)
            return True
        shared_worker.post('Q' + index)
        journal.get_question(index).created_now = True
        return False
    shared_worker.question = shared_worker_question
    def shared_worker_scroll_line(line, height):
        """Scroll position"""
        shared_worker.post('L' + line)
        if height != journal.height:
            shared_worker.post('H' + height)
    shared_worker.scroll_line = shared_worker_scroll_line
    def shared_worker_save(what):
        """Student explicit Save"""
        shared_worker.post('S' + what)
    shared_worker.save = shared_worker_save
    def shared_worker_tag(tag):
        """Student explicit tag"""
        shared_worker.post('t' + tag)
    shared_worker.tag = shared_worker_tag
    def shared_worker_goto(index):
        """Goto in the past"""
        shared_worker.post('G' + index)
    shared_worker.goto = shared_worker_goto
    def shared_worker_compile(error):
        """Record a compilation result"""
        if error:
            shared_worker.post('c1')
        else:
            shared_worker.post('c0')
    shared_worker.compile = shared_worker_compile
    def shared_worker_good():
        """Goto in the past"""
        shared_worker.post('g')
    shared_worker.good = shared_worker_good
    def shared_worker_bubble(login, pos_start, pos_end, line, column, width, height, comment):
        """bubble text"""
        shared_worker.post('b+' + login + ' ' + pos_start + ' ' + pos_end + ' ' + line + ' ' + column
            + ' ' + width + ' ' + height + ' ' + protect_crlf(comment))
    shared_worker.bubble = shared_worker_bubble
    def shared_worker_bubble_position(index, line, column):
        """bubble change position"""
        shared_worker.post('bP' + index + ' ' + line + ' ' + column)
    shared_worker.bubble_position = shared_worker_bubble_position
    def shared_worker_bubble_size(index, width, height):
        """bubble change size"""
        shared_worker.post('bS' + index + ' ' + width + ' ' + height)
    shared_worker.bubble_size = shared_worker_bubble_size
    def shared_worker_bubble_comment(index, comment):
        """bubble change comment"""
        shared_worker.post('bC' + index + ' ' + protect_crlf(comment))
    shared_worker.bubble_comment = shared_worker_bubble_comment
    def shared_worker_bubble_delete(index):
        """bubble delete"""
        shared_worker.post('b-' + index)
    shared_worker.bubble_delete = shared_worker_bubble_delete

    def shared_worker_close():
        ccccc.editor.focus() # To blur focused comment to save it
        if window.ccccc and not ccccc.options['allow_copy_paste']:
            shared_worker.blur()
        shared_worker.port.postMessage(['CLOSE'])
    shared_worker.close = shared_worker_close
    def shared_worker_debug(text):
        """Debug text"""
        # shared_worker.post('#' + text.replace(RegExp('\n', 'g'), '\000'))
        print(text)
    shared_worker.debug = shared_worker_debug
    shared_worker.port.onmessage = shared_worker_message
    shared_worker.port.start()
    if REAL_COURSE != COURSE:
        course = REAL_COURSE
        login = '_FOR_EDITOR_' + login
    else:
        course = COURSE
    shared_worker.port.postMessage(['TICKET', window.location.search, course, login, BASE])
    window.onbeforeunload = shared_worker_close
    return shared_worker, journal

def compute_diffs(old, rep):
    """Returns a list of change to change text from 'old' to 'rep'
    """
    diffs = []
    position = 0
    while old != '' or rep != '':
        if old == '':
            diffs.append([True, position, rep])
            break
        if rep == '':
            diffs.append([False, position, len(old)])
            break
        if old == rep:
            break
        if old.startswith(rep):
            position += len(rep)
            old = old[len(rep):]
            rep = ''
            continue
        if rep.startswith(old):
            position += len(old)
            rep = rep[len(old):]
            old = ''
            continue
        i = 0
        while old[i] == rep[i]:
            i += 1
        old = old[i:]
        rep = rep[i:]
        position += i
        if old == '' or rep == '':
            continue
        # Test a big delete or a big insert
        i = len(rep) - len(old)
        if i > 0:
            if old == rep[i:]:
                diffs.append([True, position, rep[:i]])
                break
        elif i < 0:
            if old[-i:] == rep:
                diffs.append([False, position, -i])
                break
        # Test a big replace
        # Bad idea : the indent operation will trigger a replace all
        # Think about it later.

        # Generic case (many deleted and inserts)
        # Should not test one character at a time but larger chunk.
        insert_pos = 999999
        search = old[0]
        for i, char in enumerate(rep):
            if char == search:
                insert_pos = i
                break
        delete_pos = 999999
        search = rep[0]
        for i, char in enumerate(old):
            if char == search:
                delete_pos = i
                break
        if insert_pos > delete_pos:
            diffs.append([False, position, delete_pos])
            old = old[delete_pos:]
            continue
        if insert_pos == 999999 and delete_pos == 999999:
            diffs.append([False, position, len(old)])
            diffs.append([True, position, rep])
            break
        if rep[:insert_pos] == old[delete_pos:delete_pos+insert_pos]:
            diffs.append([False, position, delete_pos])
            old = old[delete_pos:]
            continue
        diffs.append([True, position, rep[:insert_pos]])
        rep = rep[insert_pos:]
        position += insert_pos
    return diffs

def compute_diffs_regtest():
    """Check if compute_diff works"""
    initials = []
    def strings(depth, prefix):
        if depth == 0:
            return
        initials.append(prefix)
        depth -= 1
        strings(depth, prefix + 'a')
        strings(depth, prefix + 'b')
    strings(6, '')

    def check_diff(initial, after):
        for insert, pos, val in compute_diffs(initial, after):
            if insert:
                initial = initial[:pos] + val + initial[pos:]
                if val == '':
                    raise ValueError('empty_insert')
            else:
                initial = initial[:pos] + initial[pos+val:]
        if initial != after:
            raise ValueError('bug')

    def change(initial, current, depth):
        if depth == 0:
            check_diff(initial, current)
            return
        depth -= 1
        for i in range(len(current)):
            change(initial, current[:i] + current[i:], depth)
        for i in range(len(current)+1):
            change(initial, current[:i] + 'a' + current[i:], depth)
        for i in range(len(current)+1):
            change(initial, current[:i] + 'b' + current[i:], depth)
   
    for initial in initials:
        change(initial, initial, 4)
    print('ok')

# compute_diffs_regtest()

def session_tree(sessions, remove=0):
    """
    sessions : List[session, ...]
    returns  : List[node_name, List[nodes], List[sessions]]
    """
    keys = {'': []}
    for session in sessions:
        key = session[0][remove:]
        if '_' not in key:
            key = ''
        else:
            key = key.split('_')[0]
        if key not in keys:
            keys[key] = []
        keys[key].append(session)

    for key in keys:
        if key != '' and len(keys[key]) == 1:
            keys[''].append(keys[key][0])
            del keys[key]

    sorted_keys = list(keys)
    sorted_keys.sort()
    keys[''].sort()
    return [
        sessions[0][0][:max(0, remove-1)],
        [session_tree(keys[key], remove=remove+len(key)+1)
         for key in sorted_keys
         if key
        ],
        keys['']
        ]
