"""
Display checkpoint page

"""
try:
    # pylint: disable=undefined-variable,self-assigning-variable,invalid-name
    TICKET = TICKET
    LOGIN = LOGIN
    COURSE = COURSE
    STUDENTS = STUDENTS
    BUILDINGS = BUILDINGS
    document = document
    window = window
    Math = Math
    bind = bind
    Date = Date
except ValueError:
    pass

SCALE = 25
LEFT = 10
TOP = 120
BOLD_TIME = 180 # In seconds for new students in checking room

def seconds():
    """Number of second as Unix"""
    return int(Date().getTime() / 1000)

class Room: # pylint: disable=too-many-instance-attributes
    """Graphic display off rooms"""
    drag_x_current = drag_x_start = drag_y_current = drag_y_start = None
    scale = SCALE
    top = TOP
    left = LEFT
    x_max = 0
    moving = False
    students = []
    def __init__(self):
        self.change('Nautibus_1er')
    def change(self, building):
        """Initialise with a new building"""
        self.building = building
        self.lines = BUILDINGS[building].split('\n')
        self.x_max = 0
        self.top = TOP
        self.left = LEFT
        self.scale = SCALE
        self.drag_x_current = self.drag_x_start = None
        self.drag_y_current = self.drag_y_start = None
        self.moving = False
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
                    if x_pos >= self.x_max:
                        self.x_max = x_pos + 1
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
    def draw(self):
        """Display on canvas"""
        canvas = document.getElementById('canvas')
        ctx = canvas.getContext("2d")
        width = canvas.offsetWidth
        height = canvas.offsetHeight
        canvas.setAttribute('width', width)
        canvas.setAttribute('height', height)

        ctx.fillStyle = "#EEE"
        ctx.fillRect(0, 0, width, height)

        def line(x_start, y_start, x_end, y_end):
            ctx.beginPath()
            ctx.moveTo(self.left + self.scale*x_start, self.top + self.scale*y_start)
            ctx.lineTo(self.left + self.scale*x_end, self.top + self.scale*y_end)
            ctx.stroke()

        ctx.lineCap = 'round'
        ctx.lineWidth = self.scale / 4
        ctx.strokeStyle = "#000"
        self.draw_horizontals("+-wd", 1, line)
        self.draw_verticals("+|wd", 1, line)

        ctx.strokeStyle = "#4ffff6"
        self.draw_horizontals("w", 1, line)
        self.draw_verticals("w", 1, line)

        ctx.strokeStyle = "#fff"
        self.draw_horizontals("d", 1, line)
        self.draw_verticals("d", 1, line)

        ctx.strokeStyle = "#000"
        ctx.fillStyle = "#000"
        ctx.font = self.scale + "px sans-serif,emoji"
        translate = {'c': '🪑', 's': '💻',
                     'w': ' ', 'd': ' ', '+': ' ', '-': ' ', '|': ' '}
        for y_pos, line in enumerate(self.lines):
            for x_pos, char in enumerate(line):
                if char in translate:
                    char = translate[char]
                if char == ' ':
                    continue
                size = ctx.measureText(char)
                ctx.fillText(
                    char,
                    self.left + self.scale*x_pos - size.width/2,
                    self.top + self.scale*y_pos + size.actualBoundingBoxAscent/2)

        ctx.font = self.scale/2 + "px sans-serif"
        for student in self.students:
            x_pos = self.left + self.scale * (student.column - 0.5)
            y_pos = self.top + self.scale * student.line + 2
            size = max(ctx.measureText(student.firstname).width,
                       ctx.measureText(student.surname).width)
            ctx.fillStyle = "#FFF"
            ctx.globalAlpha = 0.5
            ctx.fillRect(x_pos, y_pos - self.scale/2, size + 2, self.scale + 2)
            ctx.fillStyle = "#8F8"
            ctx.fillRect(x_pos, y_pos - self.scale/2, self.scale, self.scale + 2)
            if student.with_me():
                ctx.fillStyle = "#000"
            else:
                ctx.fillStyle = "#888"
            ctx.globalAlpha = 1
            ctx.fillText(student.firstname, x_pos, y_pos)
            ctx.fillText(student.surname, x_pos, y_pos + self.scale/2)

    def get_column_row(self, event):
        """Return character position (float) in the character map"""
        if event.target.tagName != 'CANVAS':
            return [-1, -1]
        column = (event.clientX - event.target.offsetLeft - self.left) / self.scale
        line = (event.clientY - event.target.offsetTop - self.top) / self.scale
        if 0 <= column and column <= self.x_max and 0 <= line and line < len(self.lines):
            return [column, line]
        return [-1, -1]
    def get_coord(self, event):
        """Get column line as integer"""
        column, line = self.get_column_row(event)
        column = Math.round(column)
        line = Math.round(line)
        return [column, line]
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
        for student in self.students:
            if student.column == column and student.line == line:
                self.moving = student
                return
        self.drag_x_start = self.drag_x_current = event.clientX
        self.drag_y_start = self.drag_y_current = event.clientY
        self.moving = True
    def drag_move(self, event):
        """Moving the map"""
        if not self.moving:
            return
        if self.moving == True:
            self.left += event.clientX - self.drag_x_current
            self.top += event.clientY - self.drag_y_current
            self.drag_x_current = event.clientX
            self.drag_y_current = event.clientY
        else:
            column, line = self.get_coord(event)
            if column != -1:
                self.moving.line = line
                self.moving.column = column
                document.getElementById('top').style.background = "#EEE"
            else:
                document.getElementById('top').style.background = "#8F8"
        self.draw()
    def drag_stop(self, event):
        """Stop moving the map"""
        window.onmousemove = None
        window.onmouseup = None
        document.getElementById('top').style.background = "#EEE"
        if self.moving != True:
            column, line = self.get_coord(event)
            if column != -1:
                record('/checkpoint/' + COURSE + '/' + self.moving.login + '/'
                       + ROOM.building + ',' + column + ',' + line
                       + '?ticket=' + TICKET)
            else:
                record('/checkpoint/' + COURSE + '/' + self.moving.login
                       + '/EJECT?ticket=' + TICKET)
                #record('/checkpoint/' + COURSE + '/' + self.moving.login
                #       + '/STOP?ticket=' + TICKET)

        self.moving = False


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
        document.getElementById('top').style.background = "#EEE"
    else:
        Student.moving_element.style.background = "#FFF"
        document.getElementById('top').style.background = "#8F8"

def stop_move_student(event):
    """Drop the student"""
    pos = ROOM.get_coord(event)
    if pos[0] != -1:
        record('/checkpoint/' + COURSE + '/' + Student.moving_student.login + '/'
               + ROOM.building + ',' + pos[0] + ',' + pos[1]
               + '?ticket=' + TICKET)

    document.body.onmousemove = None
    window.onmouseup = None
    del Student.moving_element.style.position
    del Student.moving_element.style.background
    del Student.moving_element.style.pointerEvents
    document.getElementById('top').style.background = "#EEE"
    Student.moving_student = None
    Student.moving_element = None
    update_page()

def record(action):
    """Do an action and get data"""
    script = document.createElement('SCRIPT')
    script.src = action
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
        return self.teacher == LOGIN and self.active

def cmp_student(student_a, student_b):
    """Compare 2 students names"""
    if student_a.sort_key > student_b.sort_key:
        return 1
    return -1

def create_page():
    """Fill the page content"""
    content = [
        '''<style>
        .name { display: inline-block; background: #EEE; vertical-align: top;
            cursor: pointer; user-select: none;
        }
        .name:hover { background: #FFF }
        .name SPAN { color: #888 }
        CANVAS { position: absolute; left: 0px; width: 100vw; top: 0px; height: 100vh }
        #waiting { display: inline-block }
        #top {z-index: 2; position: absolute;
              top: 0px; left: 0px; width: 100%; height: 5em;
              background: #EEE; opacity: 0.95}
        </style>
        <div id="top">''',
        COURSE,
        ' <select onchange="ROOM.change(this.value); update_page(); ROOM.draw()">',
        ''.join(['<option'
                 + (building == ROOM.building and ' selected' or '')
                 + '>'+building+'</option>' for building in BUILDINGS]),
        '''</select>
        Drag and drop: <div id="waiting"></div>
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

ROOM = Room()

create_page()
