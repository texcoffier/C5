"""
Display checkpoint page

"""
# pylint: disable=chained-comparison

try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    LOGIN = LOGIN
    COURSE = COURSE
    STUDENTS = STUDENTS
    BUILDINGS = BUILDINGS
    CONFIG = CONFIG
    document = document
    window = window
    confirm = confirm
    Math = Math
    bind = bind
    Date = Date
    setInterval = setInterval
    setTimeout = setTimeout
except ValueError:
    pass

RELOAD_INTERVAL = 60 # Number of seconds between update data
LEFT = 10
TOP = 200
BOLD_TIME = 180 # In seconds for new students in checking room
BOLD_TIME_ACTIVE = 300 # In seconds for last activity
MENU_WIDTH = 9
MENU_HEIGHT = 10
MENU_LINE = 0.6
TOP_INACTIVE = 'linear-gradient(to bottom, #FFFF, #FFFE, #FFFE, #FFF0)'
TOP_ACTIVE = 'linear-gradient(to bottom, #8F8F, #8F87)'
ROOM_BORDER = ('d', 'w', '|', '-', '+', None)

def seconds():
    """Number of second as Unix"""
    return int(Date().getTime() / 1000)

def mouse_enter():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = True
def mouse_leave():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = False

class Room: # pylint: disable=too-many-instance-attributes
    """Graphic display off rooms"""
    drag_x_current = drag_x_start = drag_y_current = drag_y_start = None
    scale = min_scale = 0
    top = TOP
    left = LEFT
    x_max = 0
    moving = False
    students = []
    selected_computer = None
    selected_item = None
    moved = False
    transitions = []
    columns_x = []
    lines_y = []
    columns_width = []
    lines_height = []
    def __init__(self):
        self.change('Nautibus')
        window.onblur = mouse_leave
        window.onfocus = mouse_enter
        setInterval(reload_page, RELOAD_INTERVAL * 1000)
    def xys(self, column, line):
        """Change coordinates system"""
        return [self.left + self.scale * self.columns_x[2*column],
                self.top + self.scale * self.lines_y[2*line],
                self.scale * Math.min(self.columns_x[2*column] - self.columns_x[2*column-2],
                                      self.lines_y[2*line] - self.lines_y[2*line-2])]
    def get_column_row(self, event):
        """Return character position (float) in the character map"""
        if event.target.tagName != 'CANVAS':
            return [-1, -1]
        column = -1
        for i, position in enumerate(self.columns_x):
            if position > (event.clientX - self.left) / self.scale:
                column = int(i/2)
                break
        line = -1
        for i, position in enumerate(self.lines_y):
            if position > (event.clientY - self.top) / self.scale:
                line = int(i/2)
                break
        if column >= 0 and column <= self.x_max and line >= 0 and line < len(self.lines):
            return [column, line]
        return [-1, -1]
    def get_coord(self, event):
        """Get column line as integer"""
        column, line = self.get_column_row(event)
        column = Math.round(column)
        line = Math.round(line)
        return [column, line]
    def change(self, building):
        """Initialise with a new building"""
        self.building = building
        self.lines = BUILDINGS[building].split('\n')
        self.x_max = max([len(line) for line in self.lines]) + 1
        self.top = TOP
        self.left = LEFT
        self.drag_x_current = self.drag_x_start = None
        self.drag_y_current = self.drag_y_start = None
        self.moving = False
        self.update_sizes(0.5)
        self.update_visible()

    def update_sizes(self, size):
        """Fix the width and heights of all columns"""
        self.columns_width = [size for i in range(2 * self.x_max)]
        self.lines_height = [size for i in range(2 * len(self.lines))]

    def only_my_students(self):
        """Hide columns without my students"""
        self.update_sizes(0.1)
        for student in self.students:
            if student.active:
                (col_start, line_start, room_width, room_height, _center_x, _center_y
                ) = self.get_room(student.column, student.line)
                for i in range(2*col_start, 2*(col_start + room_width)):
                    self.columns_width[i] = 0.5
                for i in range(line_start, 2*(line_start + room_height)):
                    self.lines_height[i] = 0.5
        self.update_visible()

    def update_visible(self):
        """Update lines/columns positions from their heights/widths"""
        position = 0
        self.columns_x = []
        for width in self.columns_width:
            self.columns_x.append(position)
            position += width
        position = 0
        self.lines_y = []
        for height in self.lines_height:
            self.lines_y.append(position)
            position += height

    def get_room(self, column, line):
        """Get room position : col_min, lin_min, width, height, center_x, center_y"""
        col_end = column
        while self.lines[line][col_end] not in ROOM_BORDER:
            col_end += 1
        col_start = column
        while self.lines[line][col_start] not in ROOM_BORDER:
            col_start -= 1
        room_width = col_end - col_start
        center_x = self.columns_x[2*col_start + room_width]

        line_end = line
        while self.lines[line_end][column] not in ROOM_BORDER:
            line_end += 1
        line_start = line
        while self.lines[line_start][column] not in ROOM_BORDER:
            line_start -= 1
        room_height = line_end - line_start
        center_y = self.lines_y[2*line_start + room_height]
        return col_start, line_start, room_width, room_height, center_x, center_y

    def draw_horizontals(self, chars, min_size, draw_line):
        """Horizontal line"""
        for y_pos, line in enumerate(self.lines):
            line += ' ' # To simplify end testing
            start = -1
            for x_pos, char in enumerate(line):
                if char in chars:
                    if start == -1:
                        start = x_pos
                        if char == '+':
                            start += 0.5
                else:
                    if start == -1:
                        continue
                    if x_pos - start <= min_size:
                        start = -1
                        continue
                    if last_char == '+':
                        x_pos -= 0.5
                    draw_line(start-0.5, y_pos, x_pos-0.5, y_pos)
                    start = -1
                last_char = char
    def draw_verticals(self, chars, min_size, draw_line):
        """Vertical line"""
        for x_pos in range(self.x_max):
            start = -1
            for y_pos, line in enumerate(self.lines):
                char = line[x_pos]
                if char in chars:
                    if start == -1:
                        start = y_pos
                        if char == '+':
                            start += 0.5
                else:
                    if start == -1:
                        continue
                    if y_pos - start <= min_size:
                        start = -1
                        continue
                    if last_char == '+':
                        y_pos -= 0.5
                    draw_line(x_pos, start-0.5, x_pos, y_pos-0.5)
                    start = -1
                last_char = char
    def draw_computer_menu(self, ctx, event, messages):
        """The computer problems menu"""
        x_pos, y_pos, size = self.xys(self.selected_computer[1] - 0.5,
                                      self.selected_computer[2] - 0.5)
        ctx.fillStyle = "#FFF"
        ctx.globalAlpha = 0.9
        ctx.fillRect(x_pos, y_pos, size, size)
        ctx.fillRect(x_pos + self.scale, y_pos, MENU_WIDTH*self.scale, MENU_HEIGHT*self.scale)
        ctx.globalAlpha = 1
        ctx.fillStyle = "#000"
        self.selected_item = None
        for i, message in enumerate([
                "Les câbles sont branchés mais :",
                "",
                "Machine : ne se lance pas",
                "Machine : problème clavier",
                "Machine : problème souris",
                "Machine : problème écran",
                "",
                "Windows : ne se lance pas",
                "Windows : connexion impossible",
                "Windows : pas de fichiers",
                "",
                "Linux : ne se lance pas",
                "Linux : connexion impossible",
                "Linux : pas de fichiers",
                "",
                "Réparé : tout fonctionne !"
            ]):
            y_item = y_pos + MENU_LINE * size * i
            if message in messages:
                ctx.fillStyle = "#FDD"
                ctx.fillRect(x_pos + size, y_item,
                             MENU_WIDTH*size, MENU_LINE*size)
                ctx.fillStyle = "#000"
            if (event # pylint: disable=too-many-boolean-expressions
                    and i > 1
                    and message != ''
                    and event.clientX > x_pos + size
                    and event.clientX < x_pos + size + MENU_WIDTH*size
                    and event.clientY > y_item
                    and event.clientY < y_item + MENU_LINE * size
               ):
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos + size, y_item,
                             MENU_WIDTH*size, MENU_LINE*size)
                ctx.fillStyle = "#000"
                self.selected_item = message
            ctx.fillText(message, x_pos + size*1.5, y_item + (MENU_LINE - 0.1)*size)
    def draw_computer_problems(self, ctx):
        """Draw a red square on computer with problems"""
        ctx.fillStyle = "#F00"
        ctx.globalAlpha = 0.5
        messages = []
        for building, column, line, message, _time in CONFIG.computers:
            if building == self.building:
                x_pos, y_pos, size = self.xys(column - 0.5, line - 0.5)
                ctx.fillRect(x_pos, y_pos, size, size)
                if (self.selected_computer
                        and self.selected_computer[1] == column
                        and self.selected_computer[2] == line):
                    messages.append(message)
        ctx.globalAlpha = 1
        return messages
    def draw_students(self, ctx):
        """Draw students names"""
        now = seconds()
        for student in self.students:
            x_pos, y_pos, size = self.xys(student.column, student.line)
            x_pos -= self.scale / 2
            width = max(ctx.measureText(student.firstname).width,
                        ctx.measureText(student.surname).width)
            ctx.fillStyle = "#FFF"
            ctx.globalAlpha = 0.5
            ctx.fillRect(x_pos, y_pos - size/2, width + 2, size + 2)
            if student.active:
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos, y_pos - size/2, size, size + 2)
            if student.blur:
                ctx.fillStyle = "#F00"
                ctx.fillRect(x_pos, y_pos - size/2,
                             student.blur / 10 * size, size/2)
            if student.nr_questions_done:
                ctx.fillStyle = "#0C0"
                ctx.fillRect(x_pos, y_pos + 1,
                             student.nr_questions_done / 10 * size, size/2)
            if student.with_me():
                if student.active:
                    if now - student.checkpoint_time < BOLD_TIME_ACTIVE:
                        ctx.fillStyle = "#000"
                    else:
                        ctx.fillStyle = "#00F"
                else:
                    ctx.fillStyle = "#080"
            else:
                if now - student.checkpoint_time < BOLD_TIME_ACTIVE:
                    ctx.fillStyle = "#888"
                else:
                    ctx.fillStyle = "#88F"
            ctx.globalAlpha = 1
            ctx.fillText(student.firstname, x_pos, y_pos)
            ctx.fillText(student.surname, x_pos, y_pos + size/2)
    def draw_map(self, ctx, canvas):
        """Draw the character map"""
        width = canvas.offsetWidth
        height = canvas.offsetHeight
        canvas.setAttribute('width', width)
        canvas.setAttribute('height', height)
        ctx.fillStyle = "#EEE"
        ctx.fillRect(0, 0, width, height)

        def line(x_start, y_start, x_end, y_end):
            x_start, y_start, _ = self.xys(x_start, y_start)
            x_end, y_end, _ = self.xys(x_end, y_end)
            ctx.beginPath()
            ctx.moveTo(x_start, y_start)
            ctx.lineTo(x_end, y_end)
            ctx.stroke()

        ctx.lineCap = 'round'
        ctx.lineWidth = 2
        ctx.strokeStyle = "#000"
        self.draw_horizontals("+-wd", 1, line)
        self.draw_verticals("+|wd", 1, line)

        ctx.strokeStyle = "#4ffff6"
        self.draw_horizontals("w", 1, line)
        self.draw_verticals("w", 1, line)

        ctx.strokeStyle = "#ff0"
        self.draw_horizontals("d", 1, line)
        self.draw_verticals("d", 1, line)

        ctx.strokeStyle = "#000"
        ctx.fillStyle = "#000"
        ctx.font = self.scale + "px sans-serif,emoji"
        translate = {'c': '🪑', 's': '💻', 'p': '🖨', 'l': '🛗', 'r': '🚻', 'h': '♿',
                     'w': ' ', 'd': ' ', '+': ' ', '-': ' ', '|': ' '}
        for line, chars in enumerate(self.lines):
            if self.lines_height[2*line] < 0.5:
                # _x_pos, y_pos, size = self.xys(1, line)
                # ctx.fillStyle = "#DDD"
                # ctx.fillRect(0, y_pos, width, size)
                # ctx.fillStyle = "#000"
                continue
            for column, char in enumerate(chars):
                if self.columns_width[2*column] < 0.5:
                    continue
                if char in translate: # pylint: disable=consider-using-get
                    char = translate[char]
                if char == ' ':
                    continue
                char_size = ctx.measureText(char)
                x_pos, y_pos, size = self.xys(column, line)
                # ctx.font = size + "px sans-serif,emoji"
                ctx.fillText(char, x_pos - char_size.width/2, y_pos + size/2)
    def draw_square_feedback(self, ctx, event):
        """Single square feedback"""
        column, line = self.get_coord(event)
        x_pos, y_pos, size = self.xys(column - 0.5, line - 0.5)
        ctx.fillStyle = "#0F0"
        ctx.globalAlpha = 0.5
        ctx.fillRect(x_pos, y_pos, size, size)
        ctx.globalAlpha = 1
    def draw_help(self, ctx): # pylint: disable=too-many-statements
        """Display documentation"""
        size = self.scale * 1.5
        ctx.font = size + "px sans-serif"
        ctx.fillStyle = "#000"
        line_top = self.top - 2.7 * size * 2
        line = line_top
        column = self.left + 11 * size * 2
        ctx.fillText("Couleurs des noms d'étudiants : ", column, line)
        line += size
        column += self.scale
        ctx.fillStyle = "#888"
        ctx.fillText("Avec un autre enseignant.", column, line)
        line += size
        ctx.fillStyle = "#000"
        ctx.fillText("Travaille avec vous.", column, line)
        line += size
        ctx.fillStyle = "#00F"
        ctx.fillText("N'a rien fait depuis " + BOLD_TIME_ACTIVE/60 + " minutes.", column, line)
        line += size
        ctx.fillStyle = "#080"
        ctx.fillText("Examen terminé.", column, line)

        line = line_top
        column = self.left + 20 * size * 2
        ctx.fillStyle = "#000"
        ctx.fillText("Concernant les ordinateurs :", column, line)
        column += self.scale
        line += size
        ctx.fillText("Plus il est rouge, plus il y a des pannes.", column, line)
        line += size
        ctx.fillText("Cliquez dessus pour indiquer une panne.", column, line)
        line += size

        line = line_top
        column = self.left + 32 * size * 2
        ctx.fillText("Le carré jaune des étudiants :", column, line)
        column += self.scale
        line += size
        ctx.fillText("Tirez-le pour déplacer l'étudiant.", column, line)
        line += size
        ctx.fillText("Tirez-le tout en haut pour le remettre en salle d'attente.", column, line)
        line += size
        ctx.fillText("Cliquez dessus pour terminer l'examen.", column, line)
        line += size
        ctx.fillText("Il se remplit de rouge quand l'étudiant change de fenêtre.", column, line)
        line += size
        ctx.fillText("Il se remplit de vert avec les bonnes réponses.", column, line)

        line = line_top
        column = self.left + 0 * size * 2
        ctx.fillText("Navigation sur le plan :", column, line)
        column += self.scale
        line += size
        ctx.fillText("Utilisez la molette pour zoomer.", column, line)
        line += size
        ctx.fillText("Tirez le fond d'écran pour le déplacer.", column, line)
        line += size
        ctx.fillText("Cliquez sur le sol d'un salle pour zoomer.", column, line)
    def draw(self, event=None, square_feedback=False): # pylint: disable=too-many-locals,too-many-statements,too-many-branches
        """Display on canvas"""
        canvas = document.getElementById('canvas')
        if self.scale == 0:
            if document.getElementById('my_rooms').checked:
                self.only_my_students()
            else:
                self.update_sizes(0.5)
            self.update_visible()
            self.scale = self.min_scale = canvas.offsetWidth / self.columns_x[2 * self.x_max - 1]
            self.top = TOP
            self.left = LEFT
        ctx = canvas.getContext("2d")
        self.draw_map(ctx, canvas)
        ctx.font = self.scale/2 + "px sans-serif"
        self.draw_students(ctx)
        messages = self.draw_computer_problems(ctx)
        if self.selected_computer and self.selected_computer[0] == self.building:
            self.draw_computer_menu(ctx, event, messages)
        if square_feedback:
            self.draw_square_feedback(ctx, event)
        self.draw_help(ctx)
    def zoom(self, event):
        """Zooming on the map"""
        column, line = self.get_column_row(event)
        old_scale = self.scale
        self.scale *= (1000 - event.deltaY) / 1000
        self.left += column * (old_scale - self.scale)
        self.top += line * (old_scale - self.scale)
        self.draw()
        event.preventDefault()
    def drag_start(self, event):
        """Start moving the map"""
        window.onmousemove = bind(self.drag_move, self)
        window.onmouseup = bind(self.drag_stop, self)
        column, line = self.get_coord(event)
        self.moved = False
        for student in self.students:
            if student.column == column and student.line == line:
                self.moving = student
                student.column_start = student.column
                student.line_start = student.line
                return
        self.drag_x_start = self.drag_x_current = event.clientX
        self.drag_y_start = self.drag_y_current = event.clientY
        self.moving = True
    def drag_move(self, event):
        """Moving the map"""
        if not self.moving:
            if self.selected_computer:
                self.draw(event)
            return
        self.moved = self.moved or ((self.drag_x_start - event.clientX) ** 2
                                    + (self.drag_y_start - event.clientY) ** 2) > 10
        if self.moving == True: # pylint: disable=singleton-comparison
            self.left += event.clientX - self.drag_x_current
            self.top += event.clientY - self.drag_y_current
            self.drag_x_current = event.clientX
            self.drag_y_current = event.clientY
        else:
            column, line = self.get_coord(event)
            if column != -1:
                self.moving.line = line
                self.moving.column = column
                document.getElementById('top').style.background = TOP_INACTIVE
            else:
                document.getElementById('top').style.background = TOP_ACTIVE
        self.draw()
    def drag_stop(self, event): # pylint: disable=too-many-branches,too-many-locals,too-many-statements
        """Stop moving the map"""
        if not self.moving:
            print('bug')
            return
        document.getElementById('top').style.background = TOP_INACTIVE
        column, line = self.get_coord(event)
        if self.moving != True: # pylint: disable=singleton-comparison
            if column != -1:
                if self.moving.column_start != column or self.moving.line_start != line:
                    record('/checkpoint/' + COURSE + '/' + self.moving.login + '/'
                           + ROOM.building + ',' + column + ',' + line)
                elif not self.moved:
                    if self.moving.active:
                        if confirm("Terminer l'examen pour "
                                   + self.moving.firstname + ' ' + self.moving.surname):
                            record('/checkpoint/' + COURSE + '/' + self.moving.login + '/STOP')
                    else:
                        if confirm("Rouvrir l'examen pour "
                                   + self.moving.firstname + ' ' + self.moving.surname):
                            record('/checkpoint/' + COURSE + '/' + self.moving.login + '/RESTART')
            else:
                record('/checkpoint/' + COURSE + '/' + self.moving.login + '/EJECT')
        elif not self.moved:
            # Simple click
            if self.selected_item:
                if self.selected_item[-1] == '!':
                    self.selected_item = ''
                record('/computer/' + COURSE + '/'
                       + self.selected_computer[0] + '/'
                       + self.selected_computer[1] + '/'
                       + self.selected_computer[2] + '/'
                       + self.selected_item)
                self.selected_item = None
                self.draw()
            elif column != -1 and self.lines[line][column] == 's':
                select = [self.building, column, line]
                if self.selected_computer != select:
                    self.selected_computer = select
                    self.draw()
                    self.moving = False
                    return
            elif (column != -1
                  and self.lines[line][column] not in 'cs'
                  and self.scale < self.min_scale * 2):
                # Zoom on room
                (_col_start, _line_start, room_width, room_height, center_x, center_y
                ) = self.get_room(column, line)
                nr_frame = 10
                def linear(start, end, i):
                    return (start*i + end*(nr_frame-i)) / nr_frame
                final_scale = Math.min(event.target.offsetWidth / room_width,
                                       event.target.offsetHeight / room_height) / 2
                final_left = event.target.offsetWidth/2 - center_x * final_scale
                final_top = event.target.offsetHeight/2 - center_y * final_scale
                self.transitions = [
                    [
                        linear(self.scale, final_scale, i),
                        linear(self.left, final_left, i),
                        linear(self.top, final_top, i)
                    ]
                    for i in range(0, nr_frame + 1)
                ]
                setTimeout(bind(self.animate_zoom, self), 40)
                self.animate_zoom()

            if self.selected_computer:
                self.selected_computer = None
                self.draw()
        if not self.selected_computer:
            window.onmousemove = None
        window.onmouseup = None
        self.moving = False
    def animate_zoom(self):
        """Transition from zoom"""
        if len(self.transitions): # pylint: disable=len-as-condition
            self.scale, self.left, self.top = self.transitions.pop()
            self.draw()
            setTimeout(bind(self.animate_zoom, self), 50)


def start_move_student(event):
    """Move student bloc"""
    login = event.currentTarget.getAttribute('login')
    Student.moving_student = STUDENT_DICT[login]
    Student.moving_element = event.currentTarget
    Student.moving_element.style.position = 'absolute'
    document.body.onmousemove = move_student
    window.onmouseup = stop_move_student
    move_student(event)
def move_student(event):
    """To put the student on the map"""
    Student.moving_element.style.left = event.clientX + 'px'
    Student.moving_element.style.top = event.clientY + 'px'
    Student.moving_element.style.pointerEvents = 'none'
    pos = ROOM.get_column_row(event)
    if pos[0] != -1:
        Student.moving_element.style.background = "#0F0"
        document.getElementById('top').style.background = TOP_INACTIVE
    else:
        Student.moving_element.style.background = "#FFF"
        document.getElementById('top').style.background = TOP_ACTIVE
    ROOM.draw(event, square_feedback=True)
def stop_move_student(event):
    """Drop the student"""
    pos = ROOM.get_coord(event)
    if pos[0] != -1:
        record('/checkpoint/' + COURSE + '/' + Student.moving_student.login + '/'
               + ROOM.building + ',' + pos[0] + ',' + pos[1])

    document.body.onmousemove = None
    window.onmouseup = None
    del Student.moving_element.style.position
    del Student.moving_element.style.background
    del Student.moving_element.style.pointerEvents
    document.getElementById('top').style.background = TOP_INACTIVE
    Student.moving_student = None
    Student.moving_element = None
    if pos[0] == -1:
        update_page()
def record(action):
    """Do an action and get data"""
    script = document.createElement('SCRIPT')
    script.src = action + '?ticket=' + TICKET
    script.onload = update_page
    document.body.append(script)

STUDENT_DICT = {}

class Student: # pylint: disable=too-many-instance-attributes
    """To simplify code"""
    building = column = line = None
    def __init__(self, data):
        self.login = data[0]
        self.active = data[1][0]
        self.teacher = data[1][1]
        self.room = data[1][2]
        room = self.room.split(',')
        if len(room) == 3:
            self.building = room[0]
            self.column = int(room[1])
            self.line = int(room[2])
        self.checkpoint_time = data[1][3]
        self.blur = data[1][4]
        self.nr_questions_done = data[1][5] or 0
        self.firstname = data[2]['fn']
        self.surname = data[2]['sn']
        self.sort_key = self.surname + '\001' + self.firstname + '\001' + self.login
        STUDENT_DICT[self.login] = self

    def box(self):
        """A nice box clickable and draggable"""
        if seconds() - self.checkpoint_time < BOLD_TIME:
            more = ' style="font-weight: bold"'
        else:
            more = ''
        return ''.join([
            '<div class="name" onmousedown="start_move_student(event)" login="',
            self.login, '"', more, '>',
            # '<span>', self.login, '</span>',
            '<div>', self.firstname, '</div>',
            '<div>', self.surname, '</div>',
            # '<span>', self.room, '</span>',
            '</div>'])

    def with_me(self):
        """The student is in my room"""
        return self.teacher == LOGIN

def cmp_student(student_a, student_b):
    """Compare 2 students names"""
    if student_a.sort_key > student_b.sort_key:
        return 1
    return -1

def create_page():
    """Fill the page content"""
    content = [
        '''<style>
        .name, LABEL { display: inline-block; background: #EEE; vertical-align: top;
            cursor: pointer; user-select: none;
        }
        BODY { font-family: sans-serif }
        .name:hover { background: #FFF }
        .name SPAN { color: #888 }
        CANVAS { position: absolute; left: 0px; width: 100vw; top: 0px; height: 100vh }
        #waiting { display: inline }
        #top {z-index: 2; position: absolute;
              top: 0px; left: 0px; width: 100%; height: 5em;
              background: ''', TOP_INACTIVE, '''}
        #top * { vertical-align: middle }
        #top .course { font-size: 200%; }
        #top SELECT { font-size: 150%; }
        #top .drag_and_drop { display: inline-block }
        #top .reload { font-family: emoji; font-size: 300%; cursor: pointer; }
        </style>
        <div id="top"><span class="reload" onclick="reload_page()">⟳</span>''',

        '<span class="course">', COURSE, '</span>',
        ' <select onchange="ROOM.change(this.value); update_page(); ROOM.draw()">',
        ''.join(['<option'
                 + (building == ROOM.building and ' selected' or '')
                 + '>'+building+'</option>' for building in BUILDINGS]),
        '''</select>
        <label><input id="my_rooms" onchange="ROOM.scale = 0;ROOM.draw()" type="checkbox"
               >Seulement<br>mes salles</label>
        <div class="drag_and_drop">Faites glisser les noms<br>vers ou depuis le plan</div>
        <div id="waiting"></div>
        </div>
        <canvas
            id="canvas"
            onwheel="ROOM.zoom(event)"
            onmousedown="ROOM.drag_start(event)"
        ></canvas>
        ''']
    document.body.innerHTML = ''.join(content)
    update_page()

def update_page():
    """Update students"""
    students = [Student(student) for student in STUDENTS if student[0]]
    students.sort(cmp_student)

    content = []
    for student in students:
        if not student.active and not student.with_me():
            content.append(student.box())
    document.getElementById('waiting').innerHTML = ' '.join(content)

    ROOM.students = []
    for student in students:
        if student.building == ROOM.building:
            ROOM.students.append(student)

    ROOM.draw()

def reload_page():
    """Update data now"""
    if document.body.onmousemove is None and window.mouse_is_inside:
        record('/update/' + COURSE)

ROOM = Room()

create_page()
