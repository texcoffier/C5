"""
Display checkpoint page

"""
# pylint: disable=chained-comparison,singleton-comparison,use-implicit-booleaness-not-len

HELP_LINES = 10
BOLD_TIME = 300 # In seconds for new students in checking room
BOLD_TIME_ACTIVE = 300 # In seconds for last activity
DECAL_Y = 0.15
TOP_INACTIVE = '#FFFD'
TOP_ACTIVE = '#8F8D'
ROOM_BORDER = ('d', 'w', '|', '-', '+', None)
MESSAGES_TO_HIDE = {}
LONG_CLICK = 500
MENU_FONT = "18px sans-serif"
SPY_FONT = 12

if COURSE in ('=MAPS', '=IPS'):
    del BUILDINGS['empty']

BUILDINGS_SORTED = list(BUILDINGS)
BUILDINGS_SORTED.sort()

MAPPER = COURSE in ("=IPS", "=MAPS")

SIMILARITIES = {} # student_id ->  {student_id: similarity}
SOURCES = {} # student_id -> [ line -> true, line -> true, ...]
SOURCES_ORIG = {} # student_id -> [ [line, ...], [line, ...], ...]
GRAPH = {} # student_id -> [ student_id, ...]
LINES = {} # line -> number of time this line was found for all students

def filters(element):
    """Update student filter"""
    logins = {}
    for login in element.value.split(' '):
        logins[login] = True
    filters.logins = logins
    ROOM.update_waiting_room()

filters.logins = {}

def sort_integer(a, b):
    return b - a

def highlight_buttons():
    if not document.getElementById("checkpoint_time_buttons"):
        return
    start = nice_date(ROOM.time_span[0])
    end = nice_date(ROOM.time_span[1])
    for child in document.getElementById("checkpoint_time_buttons").childNodes:
        date = child.getAttribute('value')
        if date >= start and date <= end:
            child.style.background = '#8F8'
        else:
            child.style.background = '#DDD'
        nr_students = 0
        nr_total_students = 0
        date = date.split(' ')[0]
        for student in STUDENTS:
            if nice_date(student[1][3]).split(' ')[0] == date:
                nr_total_students += 1
                if student[1][2].split(',')[0] == ROOM.building:
                    nr_students += 1
        child.innerHTML = (
            child.innerHTML.split('<div>')[0]
            + '<div>' + nr_students + '</div>'
            + '<div>' + nr_total_students + '</div>')

def update_checkpoint_time(element, keep=False):
    """Set a nice time_span"""
    timestamp = strptime(element.value + ':00')
    element.style.background = ''
    if isNaN(timestamp):
        ROOM.time_span = [0, 1e10]
        if element.value != '':
            element.style.background = '#FDD'
        update_page()
        return

    if not keep:
        after = 1e99
        before = 0
        for student in STUDENTS:
            if student[1][2].split(',')[0] == ROOM.building:
                t = student[1][3]
                if t > timestamp and t < after:
                    after = t
                if t < timestamp and t > before:
                    before = t
        if timestamp - before < after - timestamp:
            timestamp = before
        else:
            timestamp = after
    ROOM.time_span = [timestamp - 12*3600, timestamp + 12 * 3600]
    element.value = nice_date(timestamp)
    update_page()
    ROOM.force_update_waiting_room = True
    ROOM.update_waiting_room()

def button_checkpoint_time(element):
    checkpoint_time = document.getElementById('checkpoint_time')
    checkpoint_time.value = element.getAttribute('value')
    update_checkpoint_time(checkpoint_time, True)

def seconds():
    """Number of second as Unix"""
    return int(Date().getTime() / 1000)

def mouse_enter():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = True
def mouse_leave():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = False

window.mouse_is_inside = True

def distance2(x_1, y_1, x_2, y_2):
    """Squared distance beween 2 points"""
    return (x_1 - x_2) ** 2 + (y_1 - y_2) ** 2
def distance(x_1, y_1, x_2, y_2):
    """Distance beween 2 points"""
    return distance2(x_1, y_1, x_2, y_2) ** 0.5

STUDENT_DICT = {}

class Student: # pylint: disable=too-many-instance-attributes
    """To simplify code"""
    building = column = line = None
    def __init__(self, data):
        self.data = data
        self.login = data[0]
        self.active = data[1][0]
        self.teacher = data[1][1]
        self.room = data[1][2]
        room = self.room.split(',')
        self.checkpoint_time = data[1][3]
        # Show placed students only if
        #  * It is an exam session
        #  * or it is in a time span
        #    The default time span is NOW
        if (OPTIONS.checkpoint
            or self.checkpoint_time >= ROOM.time_span[0]
               and self.checkpoint_time <= ROOM.time_span[1]
           ):
            if len(room) >= 3:
                self.building = room[0]
                self.column = int(room[1])
                self.line = int(room[2])
                self.version = room[3]
        self.blur = data[1][4]
        self.nr_questions_done = data[1][5] or 0
        self.hostname = data[1][6]
        self.bonus_time = data[1][7]
        self.grade = data[1][8]
        self.blur_time = data[1][9]
        self.feedback = data[1][10]
        self.fullscreen = data[1][11]
        self.firstname = data[2]['fn'] or '?'
        self.surname = data[2]['sn'] or '?'
        self.mail = data[2]['mail'] or ''
        if self.hostname in ROOM.ips:
            unknown_room = 0
        else:
            unknown_room = 1
        self.sort_key = unknown_room + self.surname + '\001' + self.firstname + '\001' + self.login
        STUDENT_DICT[self.login] = self
        self.update()

    def is_good_room(self, room_name):
        """Use IP to compute if the student is in the good room"""
        if self.hostname not in ROOM.ips: # Unknown IP
            return True
        if ROOM.building not in BUILDINGS: # Virtual room
            return True
        return ROOM.ips[self.hostname] == ROOM.building + ',' + room_name

    def update(self):
        """Compute some values for placed students"""
        self.full_room_name = None
        self.short_room_name = None
        self.good_room = None
        if self.building != ROOM.building:
            # Not on this map
            return
        room_name = ROOM.get_room_name(self.column, self.line)
        if room_name:
            self.full_room_name = ROOM.building + ',' + room_name
            self.short_room_name = room_name
        self.good_room = self.is_good_room(self.short_room_name)

    def box(self, style=''):
        """A nice box clickable and draggable"""
        if seconds() - self.checkpoint_time < BOLD_TIME:
            style += ';font-weight: bold'
        if self.filtered():
            style += ';background: #FF0'
        return ''.join([
            '<div class="name" onmousedown="ROOM.start_move_student(event)"',
            ' onmouseenter="highlight_student(this)"',
            ' onmouseleave="highlight_student()"',
            ' style="', style, '"',
            ' ontouchstart="ROOM.start_move_student(event)" login="',
            self.login, '">',
            # '<span>', self.login, '</span>',
            '<div>', self.surname, ' ', self.firstname, ' ', self.login, '</div>',
            # '<span>', self.room, '</span>',
            '</div>'])

    def with_me(self):
        """The student is in my room"""
        return self.teacher == LOGIN

    def filtered(self):
        """THe student must be highlighted"""
        return filters.logins[self.login]

    def __str__(self):
        return self.surname + ' ' + self.firstname

    def initials(self):
        return (self.firstname+'___')[:4] + '.' + (self.surname+'___')[:4]

    def distance(self, student):
        """Distance to another student. 1e9 if not same building"""
        if self.building != student.building or len(self.room) < 3:
            return 1e9
        return Math.sqrt(Math.pow(self.line - student.line, 2) + Math.pow(self.column - student.column, 2))

class Menu:
    line = column = model = reds = activate = None
    def __init__(self, room):
        self.opened = False
        self.room = room
        self.selected = None
    def open(self, line, column, model, reds, activate):
        self.line = line
        self.column = column
        self.model = [item for item in model if item is not None]
        self.reds = reds
        self.activate = activate
        self.opened = True
        scheduler.draw = "menu open"
    def close(self):
        if self.opened:
            self.opened = False
            self.selected = None
            scheduler.draw = "menu close"
    def select_and_close(self):
        self.activate(self.selected)
        self.close()
    def opened_at(self, line, column):
        return self.opened and self.line == line and self.column == column
    def draw(self, ctx):
        """
        Draw menu and highlighted hovered item.
        Store highlighted item value in self.selected
        """
        if not self.opened:
            return
        def set_font(message):
            if message.startswith('*'):
                ctx.font = "bold " + MENU_FONT
                message = message[1:]
            elif message.startswith('→'):
                ctx.font = MENU_FONT.replace('sans-serif', 'monospace')
            else:
                ctx.font = MENU_FONT
            return message
        scale = self.room.scale
        x_pos, y_pos, _x_size, _y_size = self.room.xys(self.column - 0.5, self.line - 0.5)
        if self.room.rotate_180:
            x_pos -= scale
            y_pos -= scale
        padding = 10
        menu_width = 0
        y_size = 0
        for message in self.model:
            set_font(message)
            box = ctx.measureText(message)
            menu_width = max(box.width, menu_width)
            descent = box.fontBoundingBoxDescent
            y_size = max(box.fontBoundingBoxAscent + descent, y_size)
        menu_width += 2 * padding
        menu_line = y_size * 1.1
        menu_height = len(self.model) * menu_line

        ctx.fillStyle = "#FFC"
        ctx.globalAlpha = 0.9
        ctx.fillRect(x_pos + scale, y_pos, menu_width, menu_height)

        ctx.strokeStyle = "#000"
        ctx.lineWidth = 2
        ctx.lineCap = 'round'
        ctx.beginPath()
        ctx.moveTo(x_pos, y_pos)
        ctx.lineTo(x_pos + scale + menu_width, y_pos)
        ctx.lineTo(x_pos + scale + menu_width, y_pos + menu_height)
        ctx.lineTo(x_pos + scale, y_pos + menu_height)
        ctx.lineTo(x_pos + scale, y_pos + scale)
        ctx.lineTo(x_pos, y_pos + scale)
        ctx.lineTo(x_pos, y_pos)
        ctx.stroke()

        x_pos += scale + padding
        ctx.globalAlpha = 1
        ctx.fillStyle = "#000"
        self.selected = None
        for i, message in enumerate(self.model):
            message = set_font(message)
            y_item = y_pos + menu_line * i
            if message in self.reds:
                ctx.fillStyle = "#FDD"
                ctx.fillRect(x_pos, y_item, menu_width - 2 * padding, menu_line)
                ctx.fillStyle = "#000"
            if (i > 1 # pylint: disable=too-many-boolean-expressions
                    and message != ''
                    and not message.startswith(' ')
                    and self.room.event_x > x_pos
                    and self.room.event_x < x_pos + menu_width
                    and self.room.event_y > y_item
                    and self.room.event_y < y_item + menu_line
               ):
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos, y_item, menu_width - 2 * padding, menu_line)
                ctx.fillStyle = "#000"
                self.selected = message
            ctx.fillText(message, x_pos, y_item + menu_line - descent)

class Room: # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Graphic display off rooms"""
    drag_x_current = drag_x_start = drag_y_current = drag_y_start = None
    scale = min_scale = 0
    top = 0
    left = 0
    x_max = 0
    moving = False
    students = []
    selected_student = None
    moved = False
    transitions = []
    columns_x = []
    lines_y = []
    columns_width = []
    lines_height = []
    rooms = {}
    rooms_on_screen = {}
    width = height = 0
    waiting_students = []
    zooming = scale_start = zooming_x = zooming_y = 0
    event_x = event_y = 0
    walls = windows = doors = chars = []
    left_column = right_column = top_line = bottom_line = 0
    highlight_disk = None
    all_ips = {}
    pointer_on_student_list = False # If True disable list update
    force_update_waiting_room = False
    drag_millisec_start = 0 # To compute static clic duration
    student_clicked = None # The student that may be moved
    ctrl = False # Control key pressed
    time_span = [0, 1e50]
    rotate_180 = False
    nr_max_grade = {'a':0, 'b': 0}
    state = 'nostate'
    similarity_todo_pending = 0
    similarities = []
    def __init__(self, info):
        self.menu = document.getElementById('top')
        self.the_menu = Menu(self)
        self.ips = {}
        self.positions = {}
        for room_name in CONFIG.ips_per_room:
            for hostname in CONFIG.ips_per_room[room_name].split(' '):
                if hostname != '':
                    host, pos_x, pos_y = (hostname + ',,').split(',')[:3]
                    self.ips[host] = room_name
                    self.positions[host] = [pos_x, pos_y]
        self.change(info)
        window.onblur = mouse_leave
        window.onfocus = mouse_enter
        window.onresize = update_page
        self.draw_times = []
        self.start_timestamp = strptime(OPTIONS['start'])
        self.stop_timestamp = strptime(OPTIONS['stop'])
    def xys(self, column, line):
        """Change coordinates system"""
        return [self.left + self.scale * self.columns_x[2*column],
                self.top + self.scale * self.lines_y[2*line],
                2 * self.scale * self.columns_width[2*column],
                2 * self.scale * self.lines_height[2*line]]
    def get_column_row(self, pos_x, pos_y):
        """Return character position in the character map"""
        if pos_y < self.real_top or pos_x < self.real_left:
            return [-1, -1]
        column = -1
        for i, position in enumerate(self.columns_x):
            if self.rotate_180:
                if position <= (pos_x - self.left) / self.scale:
                    column = int(i/2)
                    break
            else:
                if position > (pos_x - self.left) / self.scale:
                    column = int(i/2)
                    break
        line = -1
        for i, position in enumerate(self.lines_y):
            if self.rotate_180:
                if position <= (pos_y - self.top) / self.scale:
                    line = int(i/2)
                    break
            else:
                if position > (pos_y - self.top) / self.scale:
                    line = int(i/2)
                    break
        if column >= 0 and column <= self.x_max and line >= 0 and line < len(self.lines):
            return [column, line]
        return [-1, -1]
    def do_rotate_180(self):
        """Rotate the display"""
        self.rotate_180 = not self.rotate_180
        self.left = -self.left + self.width + self.menu.offsetWidth - (self.x_max+1) * self.scale
        self.top = -self.top + self.height - (len(self.lines)+1) * self.scale
        self.update_visible()
        scheduler.update_page = True
    def get_event(self, event):
        """Get event coordinates"""
        self.ctrl = event.ctrlKey
        if event.touches:
            if len(event.touches):
                self.event_x = event.touches[0].pageX
                self.event_y = event.touches[0].pageY
            # else: 'ontouchend' : return the last coordinates
        else:
            self.event_x = event.clientX
            self.event_y = event.clientY
    def get_coord(self, event_x, event_y, free_slot=False):
        """Get column line as integer"""
        if event_y < self.real_top or event_x < self.real_left:
            return [-1, -1]
        col, lin = self.get_column_row(event_x, event_y)
        if (lin >= 0 and col >= 0
                and self.lines[lin][col] in ' cab'
                and self.columns_width[2*col] == 0.5
                and self.lines_height[2*lin] == 0.5
           ):
            if not free_slot or self.student_from_column_line(col, lin) is None:
                return [col, lin] # Not 2 students at the same place
        if free_slot:
            # Current slot is not free: search around
            distances = []
            for radius in range(1, 10):
                for dir_x in range(-radius, radius + 1):
                    for dir_y in range(-radius, radius + 1):
                        event_x2 = event_x + dir_x*self.scale/2
                        event_y2 = event_y + dir_y*self.scale/2
                        col2, lin2 = self.get_column_row(event_x2, event_y2)
                        if (lin2 >= 0 and col2 >= 0 and self.lines[lin2][col2] in ' cab'
                               and self.columns_width[2*col2] == 0.5
                               and self.lines_height[2*lin2] == 0.5
                           ):
                            if not self.student_from_column_line(col2, lin2):
                                distances.append([
                                    # +1000 because of string javascript sort
                                    1000 + distance(event_x, event_y, event_x2, event_y2), col2, lin2])
                if len(distances): # pylint: disable=len-as-condition
                    break
            if len(distances): # pylint: disable=len-as-condition
                distances.sort()
                return [distances[0][1], distances[0][2]]
        return [col, lin]
    def get_room_name(self, column, line):
        """Return the short room name"""
        for room_name, room in self.rooms.Items():
            left, top, width, height = room.position
            if (column >= left and column <= left + width
                    and line >= top and line <= top + height
                ):
                return room_name
        return None
    def change(self, info):
        """Initialise with a new building"""
        document.getElementById('buildings').value = info.building
        self.similarity_todo = [] # Student list
        self.building = info.building
        if info.building not in BUILDINGS: # It is a teacher login
            info.building = 'empty'
        self.lines = BUILDINGS[info.building].split('\n')
        self.x_max = max(*[len(line) for line in self.lines]) + 1
        self.real_left = self.menu.offsetWidth
        self.real_top = document.getElementById('canvas').offsetTop
        self.left = info.left or self.real_left
        self.top = info.top or self.real_top
        self.drag_x_current = self.drag_x_start = None
        self.drag_y_current = self.drag_y_start = None
        self.moving = False
        self.scale = info.scale or 0
        self.update_sizes(0.5)
        self.update_visible()
        self.search_rooms()
        self.prepare_draw()
        try:
            self.prepare_ips()
        except: # pylint: disable=bare-except
            self.all_ips = {}
        self.force_update_waiting_room = True
        scheduler.update_messages = True
        self.the_menu.close()
        self.time_span = [0, 1e10]
        self.write_location()
    def prepare_draw(self):
        """Compile information to draw quickly the map"""
        self.walls = []
        self.prepare_horizontals("+-wd", 1, self.walls)
        self.prepare_verticals("+|wd", 1, self.walls)

        self.windows = []
        self.prepare_horizontals("w", 1, self.windows)
        self.prepare_verticals("w", 1, self.windows)

        self.doors = []
        self.prepare_horizontals("d", 1, self.doors)
        self.prepare_verticals("d", 1, self.doors)

        self.prepare_map()
    def get_room_by_name(self, name):
        """From the room name, compute its top left and size"""
        spaced = name + ' '
        for line, chars in enumerate(self.lines):
            column = chars.indexOf(spaced)
            if column != -1:
                return self.get_room(column, line)
        return None
    def search_rooms(self):
        """Extract [room] positions"""
        self.rooms = {}
        for line, chars in enumerate(self.lines):
            column = 0
            length = len(chars)
            while column < length:
                while column < length and chars[column] != '[':
                    column += 1
                if column == length:
                    break
                start = column
                replace = ' '
                while column < length and chars[column] != ']':
                    column += 1
                    replace += ' '
                if column == length:
                    break
                name = chars[start+1:column]
                position = self.get_room_by_name(name)
                if position:
                    self.rooms[name] = {'label': [start, line],
                                        'position': position[:4]
                                       }
                else:
                    alert("Can't find room named «" + name + "»")
                chars = chars[:start] + replace + chars[column+1:]
            self.lines[line] = chars
    def put_students_in_rooms(self):
        """Create the list of student per room"""
        for room in self.rooms.Values():
            room['students'] = []
            room['teachers'] = []
        for student in self.students:
            if student.short_room_name and student.short_room_name in self.rooms:
                self.rooms[student.short_room_name]['students'].append(student)
                teachers = self.rooms[student.short_room_name]['teachers']
                if student.teacher not in teachers:
                    teachers.append(student.teacher)
        for room in self.rooms.Values():
            room['teachers'].sort()
            room['teachers'] = ' '.join(room['teachers'])
    def update_sizes(self, size):
        """Fix the width and heights of all columns"""
        self.columns_width = [size for i in range(2 * self.x_max)]
        self.lines_height = [size for i in range(2 * len(self.lines))]
    def only_my_students(self):
        """Hide columns without my students"""
        self.update_sizes(0.05)
        for student in self.students:
            if student.column and student.with_me():
                (col_start, line_start, room_width, room_height, _center_x, _center_y
                ) = self.get_room(student.column, student.line)
                for i in range(2*col_start, 2*(col_start + room_width)):
                    self.columns_width[i] = 0.5
                for i in range(2*line_start, 2*(line_start + room_height)):
                    self.lines_height[i] = 0.5
        self.left = self.real_left
        self.top = self.real_top
        self.update_visible()
    def update_visible(self):
        """Update lines/columns positions from their heights/widths"""
        position = 0
        self.columns_x = []
        width = height = 0
        for width in self.columns_width:
            self.columns_x.append(position)
            position += width
        if self.rotate_180:
            for i, _value in enumerate(self.columns_x):
                self.columns_x[i] = position - self.columns_x[i] + width
        position = 0
        self.lines_y = []
        for height in self.lines_height:
            self.lines_y.append(position)
            position += height
        if self.rotate_180:
            for i in range(len(self.lines_y)): # pylint: disable=consider-using-enumerate
                self.lines_y[i] = position - self.lines_y[i] + height
    def get_room(self, column, line):
        """Get room position : col_min, lin_min, width, height, center_x, center_y"""
        if not self.lines[line] or not self.lines[line][column]: # Called outside the map
            return [0, 0, -1, -1, 0, 0]
        done = []
        for orig_line in self.lines:
            done.append([])
            for _char in orig_line:
                done[-1].append(False)
        col_start = line_start = 1000
        col_end = line_end = 0
        todo = [[line, column]]
        while len(todo):
            new_todo = []
            for lin, col in todo:
                if not done[lin] or col < 0 or col >= self.x_max:
                    return [0, 0, -1, -1, 0, 0]
                if done[lin][col]:
                    continue
                done[lin][col] = True
                if self.lines[lin][col] in ROOM_BORDER:
                    continue
                if col < col_start:
                    col_start = col
                if col > col_end:
                    col_end = col
                if lin < line_start:
                    line_start = lin
                if lin > line_end:
                    line_end = lin
                for delta_y in [-1, 0, 1]:
                    for delta_x in [-1, 0, 1]:
                        new_todo.append([lin+delta_y, col+delta_x])
            todo = new_todo

        line_start -= 1
        line_end += 1
        col_start -= 1
        col_end += 1
        room_width = col_end - col_start
        center_x = self.columns_x[2*col_start + room_width]
        room_height = line_end - line_start
        center_y = self.lines_y[2*line_start + room_height]
        return col_start, line_start, room_width, room_height, center_x, center_y
    def prepare_horizontals(self, chars, min_size, lines):
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
                    lines.append([start-0.5, y_pos, x_pos-0.5, y_pos])
                    start = -1
                last_char = char
    def prepare_verticals(self, chars, min_size, lines):
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
                    lines.append([x_pos, start-0.5, x_pos, y_pos-0.5])
                    start = -1
                last_char = char
    def prepare_map(self):
        """Create list of chars to display"""
        # 🪑 🛗 not working on phone
        translate = {'c': '⑁', 's': '💻', 'p': '🖨', 'l': '↕', 'r': '🚻', 'h': '♿',
                     'w': ' ', 'd': ' ', '+': ' ', '-': ' ', '|': ' ', 'a': 'Ⓐ', 'b': 'Ⓑ',
                     'g': '📝'}
        if MAPPER:
            translate['g'] = ' '
        self.chars = {}
        for line, chars in enumerate(self.lines):
            for column, char in enumerate(chars):
                if char in translate: # pylint: disable=consider-using-get
                    char = translate[char]
                if char == ' ':
                    continue
                if char not in self.chars:
                    self.chars[char] = []
                self.chars[char].append([column, line])
    def prepare_ips(self):
        """Compute ips per room"""
        ips = {}
        for key, value in IPS.Items():
            building, col, row = key.split(',')
            if building != self.building:
                continue
            room = self.get_room_name(col, row)
            if not room:
                continue
            if room not in ips:
                ips[room] = {}
            for hostip, nbr in value.Items():
                if self.ips[hostip] == self.building + ',' + room:
                    continue # Good room
                if hostip not in ips[room]:
                    ips[room][hostip] = 0
                ips[room][hostip] += nbr
        for key, value in ips.Items():
            lines = []
            for hostip, nbr in value.Items():
                lines.append(hostip + ' ' + nbr)
            lines.sort()
            ips[key] = lines
        self.all_ips = ips
    def draw_computer_problems(self, ctx):
        """Draw a red square on computer with problems"""
        ctx.fillStyle = "#F00"
        ctx.globalAlpha = 0.5
        for building, column, line, _message, _time in CONFIG.computers:
            if building == self.building:
                x_pos, y_pos, x_size, y_size = self.xys(column - 0.5, line - 0.5)
                ctx.fillRect(x_pos, y_pos, x_size, y_size)
        ctx.globalAlpha = 1
    def draw_students(self, ctx): # pylint: disable=too-many-branches
        """Draw students names"""
        now = seconds()
        line_height = self.scale/4
        ctx.font = line_height + "px sans-serif"
        if self.rotate_180:
            self.students.sort(cmp_student_position_reverse)
        else:
            self.students.sort(cmp_student_position)
        char_size = ctx.measureText('x')
        max_question_done = 0
        for student in self.students:
            max_question_done = max(max_question_done, student.question_done)

        students_onscreen = []
        for student in self.students:
            if (student.column >= self.left_column and student.column <= self.right_column
                    and student.line >= self.top_line and student.line <= self.bottom_line):
                x_pos, y_pos, x_size, y_size = self.xys(student.column, student.line)
                students_onscreen.append([student, x_pos, y_pos, x_size, y_size])

        for student, x_pos, y_pos, x_size, y_size in students_onscreen:
            x_pos -= self.scale / 2
            # Lighten the draw zone
            ctx.globalAlpha = 0.8
            ctx.fillStyle = "#FFF"
            ctx.fillRect(x_pos, y_pos - y_size/2, x_size, y_size)
            ctx.globalAlpha = 0.6

            # Square border
            if student.with_me():
                ctx.lineWidth = 0.1 * self.scale
            else:
                ctx.lineWidth = 0.05 * self.scale

            # Draw square border
            if student.good_room:
                if student.active:
                    color = "0123456789ABCDEF"[
                        min(15, max(0, Math.round((now - student.checkpoint_time)/BOLD_TIME_ACTIVE)))]
                    border_color = "#" + color + color + color
                else:
                    border_color = "#0F0" # Examen done
            else:
                # Not good room
                if student.active:
                    border_color = "#F00"
                else:
                    border_color = "#F90"
            ctx.strokeStyle = border_color
            ctx.beginPath()
            ctx.rect(x_pos + ctx.lineWidth/2, y_pos - y_size/2 + ctx.lineWidth/2,
                     x_size - ctx.lineWidth, y_size - ctx.lineWidth)
            ctx.closePath()
            ctx.stroke()

            # Following graphics must be in the square
            left = x_pos + ctx.lineWidth
            top = y_pos - y_size/2 + ctx.lineWidth
            width = x_size - 2*ctx.lineWidth
            height = y_size - 2*ctx.lineWidth

            # Draw focus lost time
            if student.blur_time: # student.blur contains the number of blur
                ctx.fillStyle = "#F44"
                ctx.fillRect(left, top, min(2*width, student.blur_time*self.scale/20), height/2)

            # Draw question done correctly
            if student.nr_questions_done and max_question_done:
                ctx.fillStyle = "#0DD"
                ctx.fillRect(left, top + height/2,
                             width/2, student.nr_questions_done / max_question_done * height/2)

            # Draw grading (2 triangles: done and visible)
            if student.grade[1]:
                ctx.fillStyle = "#0F0"
                if student.grade[1] == ROOM.nr_max_grade[student.version]:
                    ctx.beginPath()
                    ctx.moveTo(left + width/2, top + height)
                    ctx.lineTo(left + width  , top + height)
                    ctx.lineTo(left + width  , top + height/2)
                    ctx.closePath()
                    ctx.fill()
                    if student.feedback >= 3:
                        ctx.beginPath()
                        ctx.moveTo(left + width/2, top + height)
                        ctx.lineTo(left + width/2, top + height/2)
                        ctx.lineTo(left + width  , top + height/2)
                        ctx.closePath()
                        ctx.fill()

            # Draw instant focus lost
            if student.data.blurred and student.active:
                ctx.fillStyle = "#F0F"
                ctx.fillRect(x_pos - x_size/2, y_pos - y_size, 2*x_size, 2*y_size)

            # Draw student name
            if (self.lines_height[2*student.line] < 0.5
                    or self.columns_width[2*student.column] < 0.5):
                continue # Only my rooms are displayed.
            width = max(ctx.measureText(student.firstname).width,
                        ctx.measureText(student.surname).width)

            ctx.globalAlpha = 1
            ctx.fillStyle = "#000"
            y_pos = y_pos - char_size.fontBoundingBoxDescent
            if student.login in OPTIONS['tt']:
                bonus = '⅓'
            else:
                bonus = ''
            if student.bonus_time:
                bonus += '+' + (student.bonus_time//60) + 'm'
            if bonus:
                y_pos -= line_height / 2
                ctx.fillText(bonus, x_pos, y_pos)
                y_pos += line_height
            ctx.fillText(student.firstname, x_pos, y_pos)
            y_pos += line_height
            ctx.fillText(student.surname, x_pos, y_pos)

        if len(SIMILARITIES) == 0:
            return
        ctx.globalAlpha = 1
        hide, normal, orange, red = self.color_span()
        for student, x_pos, y_pos, x_size, y_size in students_onscreen:
            similarities = SIMILARITIES[student.login]
            if not similarities:
                continue
            for close_student, similarity in similarities.Items():
                close_student = STUDENT_DICT[close_student]
                if similarity <= hide or student.login < close_student.login:
                    continue
                x_pos2, y_pos2, _x_size2, _y_size2 = self.xys(close_student.column, close_student.line)
                vec_x = x_pos - x_pos2
                vec_y = y_pos - y_pos2
                length = (vec_x**2 + vec_y**2)**0.5 / self.scale * 3
                vec_x /= length
                vec_y /= length
                coord_x = x_pos - vec_x
                coord_y = y_pos - vec_y
                x_pos2 += vec_x
                y_pos2 += vec_y
                if student.column == close_student.column  and abs(student.line - close_student.line) != 1:
                    decal = (y_pos - y_pos2 - 1) / 8
                    coord_x -= decal
                    x_pos2 -= decal
                elif student.line == close_student.line and abs(student.column - close_student.column) != 1:
                    decal = (x_pos - x_pos2 - 1) / 8
                    coord_y -= decal
                    y_pos2 -= decal
                if similarity > red:
                    ctx.strokeStyle = '#F00'
                elif similarity > orange:
                    ctx.strokeStyle = '#FB4'
                elif similarity > normal:
                    ctx.strokeStyle = '#880'
                else:
                    ctx.strokeStyle = '#DDD'
                ctx.lineWidth = self.scale * 0.08
                ctx.beginPath()
                ctx.moveTo(coord_x, coord_y)
                ctx.lineTo(x_pos2, y_pos2)
                ctx.stroke()

                center_x = (coord_x + x_pos2) / 2
                center_y = (coord_y + y_pos2) / 2
                for student_source, student_source2 in zip(SOURCES[student.login], SOURCES[close_student.login]):
                    for line in student_source:
                        if line in student_source2:
                            if LINES[line] <= 5:
                                ctx.globalAlpha = 0.5
                                ctx.fillStyle = '#FF0'
                                ctx.beginPath()
                                ctx.arc(center_x, center_y, x_size/5, 0, Math.PI*2)
                                ctx.fill()
                                ctx.globalAlpha = 1

                ctx.fillStyle = '#00F'
                similarity = str(similarity)
                box = ctx.measureText(similarity)
                ctx.fillText(similarity, center_x - box.width/2,
                    center_y + (box.fontBoundingBoxAscent - box.fontBoundingBoxDescent)/2)

        # Similarity stats
        histogram = []
        for i in self.similarities:
            histogram[i] = (histogram[i] or 0) + 1
        left = self.menu.offsetWidth + 5
        top = 300
        ctx = document.getElementById('canvas').getContext("2d")
        ctx.fillStyle = "#00F"
        ctx.font = "16px sans-serif"
        ctx.fillText("X : Nbr lignes identiques. Y : Nbr de paires d'étudiants proches avec ce nombre de lignes", left, top + 50)
        ctx.font = "10px sans-serif"
        ctx.globalAlpha = 1
        width = 25
        hide, normal, orange, red = self.color_span()
        for i, nbr in enumerate(histogram):
            if nbr:
                if i > red:
                    ctx.fillStyle = "#F00"
                elif i > orange:
                    ctx.fillStyle = '#FB4'
                elif i > normal:
                    ctx.fillStyle = '#880'
                elif i > hide:
                    ctx.fillStyle = '#CCC'
                else:
                    ctx.fillStyle = '#EEE'
                ctx.fillRect(left + width*i, top - nbr, width-2, nbr)
                ctx.fillStyle = "#00F"
                ctx.fillText(str(i), left + width*i, top + 10)
                ctx.fillText(str(nbr), left + width*i, top + 25)

    def color_span(self):
        return [self.similarities[int(len(self.similarities)//6)],
            self.similarities[int(len(self.similarities)//10)],
            self.similarities[int(len(self.similarities)//50)],
            self.similarities[int(len(self.similarities)//100)]]

    def draw_map(self, ctx, canvas): # pylint: disable=too-many-locals
        """Draw the character map"""
        canvas.setAttribute('width', self.width)
        canvas.setAttribute('height', self.height)
        #ctx.fillStyle = "#EEE"
        #ctx.fillRect(0, 0, self.width, self.height)

        def line(x_start, y_start, x_end, y_end):
            if x_start == x_end:
                if (x_start < self.left_column or x_start > self.right_column):
                    return
            else:
                if y_start < self.top_line or y_start > self.bottom_line:
                    return
            x_start, y_start, _, _ = self.xys(x_start, y_start)
            x_end, y_end, _, _ = self.xys(x_end, y_end)
            ctx.beginPath()
            ctx.moveTo(x_start, y_start)
            ctx.lineTo(x_end, y_end)
            ctx.stroke()

        if LOGIN in CONFIG.roots:
            ctx.strokeStyle = "#DDD"
            for room in self.rooms.Values():
                coord_x, coord_y, width, height = room.position
                line(coord_x, coord_y, coord_x + width, coord_y + height)
                line(coord_x + width, coord_y, coord_x, coord_y + height)

        if self.highlight_disk:
            age = millisecs() - self.highlight_disk[2]
            max_age = 10000
            if age > max_age:
                self.highlight_disk = None
            else:
                ctx.fillStyle = "#00FFFF"
                ctx.globalAlpha = (max_age - age) / max_age
                ctx.beginPath()
                pos_x, pos_y, scalex, _scaley = self.xys(
                    self.highlight_disk[0], self.highlight_disk[1])
                ctx.arc(pos_x, pos_y, 2*scalex, 0, 2*Math.PI)
                ctx.fill()
                ctx.globalAlpha = 1

        if self.moving and self.moving != True and not self.the_menu.opened:
            self.draw_move_timer()

        ctx.lineCap = 'round'
        ctx.lineWidth = self.scale / 4
        ctx.strokeStyle = "#999"
        for coords in self.walls:
            line(*coords)

        ctx.lineCap = 'butt'
        ctx.strokeStyle = "#4ffff6"
        for coords in self.windows:
            line(*coords)

        ctx.strokeStyle = "#ee0"
        for coords in self.doors:
            line(*coords)

        ctx.strokeStyle = "#000"
        ctx.fillStyle = "#000"
        ctx.font = self.scale + "px sans-serif,emoji"
        for char, chars in self.chars.Items():
            char_size = ctx.measureText(char)
            for column, line in chars:
                if (column < self.left_column or column > self.right_column
                        or line < self.top_line or line > self.bottom_line):
                    continue
                if self.lines_height[2*line] < 0.5:
                    # _x_pos, y_pos, size = self.xys(1, line)
                    # ctx.fillStyle = "#DDD"
                    # ctx.fillRect(0, y_pos, width, size)
                    # ctx.fillStyle = "#000"
                    continue
                if self.columns_width[2*column] < 0.5:
                    continue
                x_pos, y_pos, _x_size, y_size = self.xys(column, line)
                rotate = self.rotate_180 and char.charCodeAt() < 256
                if rotate:
                    ctx.save()
                    ctx.translate(x_pos, y_pos)
                    ctx.rotate(Math.PI)
                    ctx.translate(-x_pos, -y_pos)
                ctx.fillText(char, x_pos - char_size.width/2, y_pos + y_size/2 - char_size.fontBoundingBoxDescent)
                if rotate:
                    ctx.restore()
    def draw_square_feedback(self, ctx):
        """Single square feedback"""
        column, line = self.get_coord(self.event_x, self.event_y, True)
        if self.rotate_180:
            x_pos, y_pos, x_size, y_size = self.xys(column + 0.5, line + 0.5)
        else:
            x_pos, y_pos, x_size, y_size = self.xys(column - 0.5, line - 0.5)
        ctx.fillStyle = "#0F0"
        ctx.globalAlpha = 0.5
        ctx.fillRect(x_pos, y_pos, x_size, y_size)
        ctx.globalAlpha = 1
    def draw_help(self, ctx): # pylint: disable=too-many-statements
        """Display documentation"""
        size = self.scale * 1.5
        indent = 2 * self.scale
        ctx.font = size + "px sans-serif"
        ctx.fillStyle = "#000"
        line_top = self.top - 2.7 * size * 2

        def draw_messages(column, texts):
            line = line_top
            first = True
            max_width = 0
            for text in texts:
                if text.startswith('#'):
                    ctx.fillStyle = text[:4]
                    text = text[4:]
                else:
                    ctx.fillStyle = "#000"
                ctx.fillText(text, column, line)
                width = ctx.measureText(text).width
                if width > max_width:
                    max_width = width
                if first:
                    column += indent
                    first = False
                line += size
            return max_width + 2*size

        column = self.left
        column += draw_messages(column, [
            "Navigation sur le plan :",
            "Utilisez la molette pour zoomer.",
            "Tirez le fond d'écran pour le déplacer.",
            "Cliquez sur le sol d'un salle pour zoomer.",
            "📝 : actions sur la salle"])
        column += draw_messages(column, [
            "Les carrés des étudiants :",
            " Appuyez longtemps et tirez pour déplacer l'étudiant.",
            " Tirez tout à gauche pour remettre en salle d'attente.",
            "#800 Rouge en haut : nombre de secondes sans focus.",
            "#088 Cyan en bas gauche : nombre de bonnes réponses.",
            "#080 Vert en bas droit : triangle si noté, carré si affiché.",
            ])
        column += draw_messages(column, [
            "Cadre autour de l'étudiant : ",
            " Épais : vous l'avez placé.",
            "#080 Vert : examen terminé.",
            "#800 Rouge : dans la mauvaise salle.",
            " Blanc : n'a rien fait depuis " + BOLD_TIME_ACTIVE/60 + " minutes.",
            "#888 Gris → noir s'il est actif récemment.",
            ])
        column += draw_messages(column, [
            "#000 Concernant les ordinateurs :",
            "Plus il est rouge, plus il y a des pannes.",
            "Cliquez dessus pour indiquer une panne."])
    def draw_teachers(self, ctx):
        """Display teacher names in front of rooms"""
        ctx.fillStyle = "#000"
        size = self.scale * 0.5
        ctx.font = size + "px sans-serif"
        for room in self.rooms.Values():
            if room['teachers']:
                column, line = room['label']
                if (self.lines_height[2*line] < 0.5
                    or self.columns_width[2*column] < 0.5):
                    continue
                x_pos, y_pos, _x_size, _y_size = self.xys(column, line)
                if self.rotate_180:
                    x_pos -= ctx.measureText(room['teachers']).width
                ctx.fillText(room['teachers'], x_pos, y_pos)
    def draw_ips(self, ctx):
        """Display used IP in room"""
        if not MAPPER:
            return
        ctx.font = self.scale/3 + "px sans-serif"
        if self.ctrl or COURSE == "=MAPS":
            for room, hosts in CONFIG.ips_per_room.Items():
                if room.split(',')[0] == self.building:
                    for host in hosts.split(RegExp(' +')):
                        place = host.split(',')
                        if len(place) == 3:
                            x_pos, y_pos, _x_size, y_size = self.xys(place[1]-0.5, place[2])
                            ip_addr = place[0].split('.')[0]
                            ctx.fillStyle = "#FFF"
                            ctx.globalAlpha = 0.8
                            ctx.beginPath()
                            ctx.rect(x_pos, y_pos - y_size/2, ctx.measureText(ip_addr).width, y_size)
                            ctx.fill()
                            ctx.fillStyle = "#000"
                            ctx.globalAlpha = 1
                            ctx.fillText(ip_addr, x_pos, y_pos)
            return
        for room, ips in self.all_ips.Items():
            if room not in self.rooms:
                continue
            left, top, _width, _left = self.rooms[room]['position'][:4]
            for line in ips:
                top += 0.5
                x_pos, y_pos, _x_size, _y_size = self.xys(left, top)
                ctx.fillText(line, x_pos, y_pos)
        ctx.fillStyle = "#F00"
        for i_y, line in enumerate(self.lines):
            for i_x, char in enumerate(line):
                if char in ('a', 'b'):
                    x_pos, y_pos, _x_size, _y_size = self.xys(i_x, i_y)
                    ctx.fillText(i_x + ',' + i_y, x_pos, y_pos)
        for full_ip, places_nr in IP_TO_PLACE.Items():
            if len(places_nr[0]) != 1:
                continue
            building_x_y = places_nr[0][0].split(',')
            if building_x_y[0] != self.building:
                continue
            ip_addr = full_ip.split('.')[0]
            x_pos, y_pos, x_size, y_size = self.xys(building_x_y[1], building_x_y[2])
            x_pos -= x_size/2
            y_pos -= 0.25 * y_size
            ctx.fillStyle = "#FFF"
            ctx.globalAlpha = 0.7
            ctx.fillRect(x_pos, y_pos, ctx.measureText(ip_addr).width, y_size * 0.8)
            ctx.globalAlpha = 1
            if self.positions[full_ip] == [building_x_y[1], building_x_y[2]]:
                ctx.fillStyle = "#080"
            else:
                ctx.fillStyle = "#000"
            ctx.fillText(ip_addr, x_pos, y_pos + y_size/2)
    def draw(self, square_feedback=False):
        """Display on canvas"""
        start = Date().getTime()
        canvas = document.getElementById('canvas')
        self.width = canvas.offsetWidth
        self.height = canvas.offsetHeight
        if self.scale == 0:
            my_rooms = False
            if document.getElementById('my_rooms') and document.getElementById('my_rooms').checked:
                my_rooms = True
            if my_rooms:
                self.only_my_students()
            else:
                self.update_sizes(0.5)
            self.update_visible()
            if MAPPER:
                help_lines = 2
            else:
                help_lines = HELP_LINES
            self.scale = self.min_scale = min(
                (self.width - self.real_left) / max(self.columns_x[0], self.columns_x[2 * self.x_max - 1]),
                (self.height - self.real_top) / max(self.lines_y[0], self.lines_y[2 * len(self.lines) - 1 - help_lines]))
            self.top = self.real_top
            if not my_rooms:
                self.top += help_lines * self.scale
            self.write_location()
        ctx = canvas.getContext("2d")
        self.left_column, self.top_line = self.get_column_row(0, self.real_top+1)
        self.right_column, self.bottom_line = self.get_column_row(self.width, self.height)
        if self.rotate_180:
            self.left_column, self.top_line, self.right_column, self.bottom_line = (
                self.right_column, self.bottom_line, self.left_column, self.top_line)
        self.left_column = max(self.left_column, 0) - 1
        self.top_line = max(self.top_line, 0) - 2
        if self.right_column == -1:
            self.right_column = self.x_max
        if self.bottom_line == -1:
            self.bottom_line = len(self.lines)
        self.draw_map(ctx, canvas)
        self.draw_students(ctx)
        ctx.font = self.scale/2 + "px sans-serif"
        self.draw_teachers(ctx)
        if square_feedback:
            self.draw_square_feedback(ctx)
        if not MAPPER:
            self.draw_help(ctx)
        self.draw_times.append(Date().getTime() - start)
        ctx.font = "16px sans-serif"
        if LOGIN == 'thierry.excoffier' and len(self.draw_times) > 10:
            self.draw_times = self.draw_times[1:]
            ctx.fillText(int(sum(self.draw_times) / len(self.draw_times)) + 'ms',
                         self.width - 70, 50)
        self.draw_computer_problems(ctx)
        self.draw_ips(ctx)
        self.the_menu.draw(ctx)
    def do_zoom(self, pos_x, pos_y, new_scale):
        """Do zoom"""
        self.left += (pos_x - self.left) * (1 - new_scale/self.scale)
        self.top += (pos_y - self.top) * (1 - new_scale/self.scale)
        self.scale = new_scale
        self.compute_rooms_on_screen()
        self.update_waiting_room()
        scheduler.draw = "do_zoom"
        self.write_location()
    def zoom(self, event):
        """Zooming on the map"""
        self.do_zoom(event.clientX, event.clientY,
                     self.scale * (1000 - event.deltaY) / 1000)
        event.preventDefault()
    def student_from_column_line(self, column, line):
        """Get the student at the indicated position"""
        for student in self.students:
            if student.column == column and student.line == line:
                if self.moving and self.moving['login'] == student.login:
                    return None
                return student
        return None
    def drag_start(self, event):
        """Start moving the map"""
        if event.button != 0:
            return
        self.get_event(event)
        window.onmousemove = window.ontouchmove = bind(self.drag_move, self)
        window.onmouseup = window.ontouchend = bind(self.drag_stop, self)
        if event.touches:
            event.preventDefault()
            if len(event.touches) == 2:
                self.zooming = distance(self.event_x, self.event_y,
                                        event.touches[1].pageX, event.touches[1].pageY)
                self.zooming_x = (self.event_x + event.touches[1].pageX) / 2
                self.zooming_y = (self.event_y + event.touches[1].pageY) / 2
                self.scale_start = self.scale
                return
        self.student_clicked = None
        column, line = self.get_coord(self.event_x, self.event_y)
        student = self.student_from_column_line(column, line)
        if student:
            self.student_clicked = {'login': student.login,
                                    'column': student.column,
                                    'line': student.line}
        self.moved = False
        self.drag_x_start = self.drag_x_current = self.event_x
        self.drag_y_start = self.drag_y_current = self.event_y
        self.drag_millisec_start = millisecs()
        self.moving = True
        scheduler.draw = "drag_start"
    def drag_move(self, event):
        """Moving the map"""
        self.get_event(event)
        column, line = self.get_coord(self.event_x, self.event_y)
        time_since_click = millisecs() - self.drag_millisec_start
        if (self.moving == True # Student no moving
            and not self.moved # Nothing yet moved
            and not self.zooming
            and time_since_click > LONG_CLICK # Long clic
            and not self.the_menu.opened
            and distance2(self.drag_x_start, self.drag_y_start,
                          self.event_x, self.event_y) > 5
        ):
            if self.student_clicked:
                self.moving = self.student_clicked
        if self.zooming:
            if len(event.touches) == 2:
                zooming = distance(self.event_x, self.event_y,
                                   event.touches[1].pageX, event.touches[1].pageY)
                self.do_zoom(self.zooming_x, self.zooming_y,
                             self.scale_start * zooming / self.zooming)
                scheduler.draw = "drag_move zooming"
                return
            self.zooming = 0
            window.onmousemove = window.ontouchmove = None
            window.onmouseup = window.ontouchend = None
            return
        if not self.moving:
            if self.the_menu.opened:
                scheduler.draw = "drag_move moving"
            return
        self.moved = self.moved or distance2(self.drag_x_start, self.drag_y_start,
                                             self.event_x, self.event_y) > 10
        if self.moving == True: # pylint: disable=singleton-comparison
            self.left += self.event_x - self.drag_x_current
            self.top += self.event_y - self.drag_y_current
            self.drag_x_current = self.event_x
            self.drag_y_current = self.event_y
        else:
            if column != -1:
                column, line = self.get_coord(self.event_x, self.event_y, True)
                student = STUDENT_DICT[self.moving['login']]
                if student.grade == '':
                    student.line = line
                    student.column = column
                    student.update()
                document.getElementById('top').style.background = TOP_INACTIVE
            else:
                document.getElementById('top').style.background = TOP_ACTIVE
        scheduler.draw = "drag_move default"
    def drag_stop_student(self, column, line):
        """Stop moving a student"""
        if column != -1:
            if self.moving['column'] != column or self.moving['line'] != line:
                if STUDENT_DICT[self.moving['login']].grade == '':
                    self.move_student_to(self.moving, column, line)
        else:
            # Move the student from map to waiting room.
            self.highlight_disk = None
            record('checkpoint/' + COURSE + '/' + self.moving['login'] + '/EJECT')
            self.force_update_waiting_room = True

    def drag_stop_click_on_room(self, event, column, line):
        """Click on a room to zoom"""
        (_col_start, _line_start, room_width, room_height, center_x, center_y
        ) = self.get_room(column, line)
        if room_width < 0 or room_height < 0:
            return
        nr_frame = 10
        def linear(start, end, i):
            return (start*i + end*(nr_frame-i)) / nr_frame
        final_scale = Math.min(event.target.offsetWidth / room_width,
                                event.target.offsetHeight / room_height) / 2
        final_left = (event.target.offsetWidth + self.menu.offsetWidth)/2 - center_x * final_scale
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
    def write_location(self):
        """Add the current location in the URL"""
        location.hash = '#' + JSON.stringify(
            {'building':self.building,
             'scale': Math.round(self.scale),
             'left': Math.round(self.left),
             'top': Math.round(self.top)})
    def open_computer_menu(self, line, column):
        def select(item):
            if item[-1] == '!':
                item = ''
            record('computer/' + COURSE + '/' + self.building + '/'
                + column + '/' + line + '/' + item)
        reds = []
        for building, col, lin, message, _time in CONFIG.computers:
            if building == self.building and col == column and lin == line:
                reds.append(message)
        self.the_menu.open(line, column,
            [
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
            ], reds, select)
    def open_room_menu(self, line, column):
        room = self.rooms[self.get_room_name(column, line)]
        logins = []
        mails = []
        for student in room.students:
            logins.append(student.login)
            mails.append((student.mail or (student.login + '@?.?')))
        mails = '\n'.join(mails)
        def select(item):
            if item.startswith('Noter'):
                for login in logins:
                    if ': A' in item and STUDENT_DICT[login].version != 'a':
                        continue
                    if ': B' in item and STUDENT_DICT[login].version != 'b':
                        continue
                    window.open(BASE + '/grade/' + COURSE + '/' + login
                        + '?ticket=' + TICKET)
            elif item.startswith('Espionner'):
                for student in room.students:
                    create_realtime_spy(student)
            elif item.startswith('Récupérer'):
                window.open(BASE + '/adm/answers/' + COURSE + '/'
                    + ','.join(logins) + '/' + COURSE + '__'
                    + self.building + '_' + self.get_room_name(column, line) + '.zip')
            elif item.startswith('Similarité'):
                for student in STUDENTS:
                    student = Student(student) # Fill STUDENT_DICT
                    self.similarity_todo.append(student.login)
            elif item.startswith('Copier'):
                def ok():
                    alert("Vous pouvez maintenant coller les " 
                          + len(room.students) + " adresses mails")
                def bad():
                    alert(mails)
                navigator.clipboard.writeText(mails).then(ok).catch(bad)
            elif item.startswith('→'):
                window.open(BASE + '/grade/' + COURSE + '/' + item.split(' ')[0][1:]
                        + '?ticket=' + TICKET)
        items = [
            "Pour les " + len(room.students) + " étudiants de cette pièce",
            "",
            "Espionner les écrans en temps réel",
            "Similarité du code avec les voisins",
            "Noter et commenter leur travail",
            "Noter et commenter leur travail (sujet : A)",
            "Noter et commenter leur travail (sujet : B)",
            "Récupérer un ZIP de leur travail",
            "Copier toutes les adresses mails",
            ""
            ]
        items.append(' Login BonusTime Grade[#Grades] BlurTime[#Blur] FeedBack')
        for student in room.students:
            items.append('→' + student.login + ' '
                + str(student.bonus_time).rjust(2) + ' '
                + str(student.grade[1] and student.grade[0].toFixed(2) or '?').rjust(5) + '['
                + str(student.grade[1] or '?').rjust(2) + '] '
                + str(student.blur_time).rjust(4) + '['
                + str(student.blur).rjust(2) + '] '
                + str(student.feedback).rjust(1) + ' '
                + student.firstname + ' ' + student.surname)
        self.the_menu.open(line, column, items, [], select)
    def open_student_menu(self, line, column, student):
        login = student.login
        def select(item):
            if item.startswith("Espionner"):
                create_realtime_spy(student)
            elif item.startswith("Naviguer"):
                create_timetravel(login)
            elif item.startswith("Clôturer"):
                close_exam(login)
            elif item.startswith("Rouvrir"):
                open_exam(login)
            elif item.startswith("Lignes"):
                name = student.login + ' ' + student.__str__()
                txt = ['<title>' + name + '</title>',
                       '<style>',
                       '.tipped { display: inline-block; position: relative}',
                       '.tipped PRE { display: none;',
                       '              position: absolute; right:5em; top: -8em;',
                       '              background: #FFE; border: 1px solid #000;',
                       '              z-index:10; max-width:50em; overflow: auto;}',
                       '.tipped:hover PRE { display: block;}',
                       '.tipped:hover { background: #FF0 }',
                       '.pairs { max-width: 60em; overflow: auto; }',
                       'HR { margin: 0px }',
                       '</style>',
                       '<h1>Voisins de ' + name + '</h1>',
                       'Le nombre indiqué est le nombre de fois que la ligne a été ',
                       "tapée par l'ensemble des étudiants. ",
                       "<ul>",
                       "<li>Les lignes présentes dans le code initial ont été enlevées.",
                       "<li>Les « »  «:»  «;»  «,»  «.»  «{»  «}» ont été supprimés des lignes.",
                       "<li>Les commentaires ont été enlevés.",
                       "<li>Les lignes ont été passées en minuscules.",
                       "</ul>"
                      ]
                txt.append('<table><tr><td style="vertical-align:top">')
                for other, similarity in SIMILARITIES[student.login].Items():
                    other = STUDENT_DICT[other]
                    txt.append('<h2>' + other.login + ' [' + similarity + ' lignes] '
                        + other.firstname + ' ' + other.surname + '</h2><pre class="pairs">')
                    empty = True
                    for question in range(len(SOURCES[student.login] or [])):
                        student_source2 = SOURCES[other.login][question]
                        student_source_orig = SOURCES_ORIG[student.login][question].split('\n')
                        student_source2_orig = SOURCES_ORIG[other.login][question].split('\n')
                        if not student_source2:
                            continue
                        done = {}
                        for line_orig in student_source_orig:
                            line = simplify_line(line_orig)
                            if line in done:
                                continue
                            done[line] = True
                            if line in student_source2:
                                empty = False
                                add = ('Q' + (question+1) + ' ' + LINES[line] + '       ')[:8]
                                add += html(line_orig) + '<br>'
                                for line2_orig in student_source2_orig:
                                    if simplify_line(line2_orig) == line:
                                        add += '        ' + html(line2_orig) + '<br>'
                                if LINES[line] <= 2:
                                    add = '<span style="color: #F00">' + add + '</span>'
                                elif LINES[line] <= 4:
                                    add = '<b>' + add + '</b>'
                                    # Search other student with the line
                                    for s, q in SOURCES.Items():
                                        if s != student.login and s != other.login and line in (q[question] or []):
                                            other =  STUDENT_DICT[s]
                                            name = s + ' ' + other.__str__()
                                            if student.distance(other) < 5:
                                                name = '<b>' + name + '</b>'
                                            else:
                                                name = name + '(loin)'
                                            add += '        Et aussi ' + name + '<br>'
                                else:
                                    add = '<span style="color: #888">' + add + '</span>'
                                txt.append(add)
                    if empty:
                        txt.pop()
                    else:
                        txt.append('</pre>')
                txt.append('</td><td style="vertical-align:top">')
                for i, lines_orig in enumerate(SOURCES_ORIG[student.login]):
                    txt.append('<pre>Nombre de lignes identiques. Vide=code initial, 1=unique.\n')
                    txt.append('Et noms des voisins avec la même ligne.\n')
                    first_lines = SOURCES[student.login][i]
                    for line, simplified in zip(lines_orig.split('\n'), get_lines(lines_orig)):
                        nbr = LINES[simplified]
                        if nbr:
                            before = [(str(nbr) + '   ')[:4]]
                            if nbr >= 2 and nbr <= 20:
                                for other in SIMILARITIES[student.login]:
                                    if simplified in SOURCES[other][i]:
                                        tip = []
                                        lines_other = SOURCES_ORIG[other][i].split('\n')
                                        for j, line_other in enumerate(lines_other):
                                            # tip.append(html(line_other))
                                            if simplify_line(line_other) == simplified:
                                                for k in lines_other[j-6:j+7]:
                                                    simplified2 = simplify_line(k)
                                                    if simplified2 == simplified:
                                                        tip.append('<b>' + html(k) + '</b>\n')
                                                    elif simplified2 in first_lines:
                                                        tip.append(html(k) + '\n')
                                                    else:
                                                        tip.append('<span style="color:#666">' + html(k) + '</span>\n')
                                                tip.append('<hr>')
                                        tip.pop()
                                        before.append(
                                            '<div class="tipped">'
                                            + STUDENT_DICT[other].initials()
                                            + '<pre>' + ''.join(tip) + '</pre></div>'
                                        )
                                before.sort()
                        else:
                            before = ['    ']
                        while len(before) < 5:
                            before.append('         ')
                        txt.append(' '.join(before[:4]) + ' | ' + html(line) + '<br>')
                    txt.append('</pre>')
                    txt.append('<hr>')
                txt.append('</tr><table>')
                window.open("").document.write(''.join(txt))

            elif item.startswith("Noter"):
                window.open(BASE + '/grade/' + COURSE + '/' + login + '?ticket=' + TICKET)
            elif item.startswith("Temps"):
                minutes = prompt(
                    "Nombre de minutes bonus pour l'étudiant.\n"
                    + "C'est un temps total, pas un incrément.\n"
                    + "Les tiers-temps ont déjà leur temps en plus.",
                    int(student.bonus_time / 60))
                if minutes is not None:
                    record('checkpoint/TIME_BONUS/' + COURSE + '/'
                            + login + '/' + 60*int(minutes))
            elif item.startswith("Encart"):
                record('checkpoint/FULLSCREEN/' + COURSE + '/'
                       + login + '/' + (1 - student.fullscreen))
            else:
                alert(item)
        if student.active:
            state = "Clôturer l'examen"
        else:
            state = "Rouvrir l'examen"
        grade = "Noter l'étudiant"
        if self.state == 'done':
            grade = '*' + grade
        spy = "Espionner l'écran en temps réel"
        if self.state == 'running':
            spy = '*' + spy
        temps = "Temps bonus"
        if student.bonus_time:
            temps += ' (' + int(student.bonus_time / 60) + ' min.)'
        fullscreen = "Encart rouge bloquant : "
        if student.fullscreen:
            fullscreen += "le réactiver"
        else:
            fullscreen += "le désactiver"

        blur = grades = feedback = None
        if student.blur:
            blur = ' ' + student.blur + ' pertes de focus (' + student.blur_time + ' secs)'

        if student.grade != '':
            grades = ' Somme des ' + student.grade[1] + '/' + ROOM.nr_max_grade[student.version] + ' notes → ' + student.grade[0]
            feedback = ' ' + [
                "Rien d'affiché à l'étudiant",
                "Code source commenté",
                "bug1",
                "bug2",
                "Code source commenté et note totale",
                "Code source commenté et barème détaillé"
            ][student.feedback] + " affiché à l'étudiant"

        similarities = ''
        if SIMILARITIES[student.login] and len(self.similarity_todo) == 0:
            similarities = 'Lignes identiques avec voisins :'
            for similarity in SIMILARITIES[student.login].Values():
                similarities += ' ' + similarity

        self.the_menu.open(line, column,
            [
                student.firstname + ' ' + student.surname,
                "", spy,
                "Naviguer dans le temps",
                similarities,
                temps, fullscreen, state, grade,
                student.mail or 'Adresse mail inconnue',
                "",
                blur, grades, feedback

            ], [], select)

    def drag_stop(self, event):
        """Stop moving the map"""
        self.write_location()
        if self.zooming:
            window.onmousemove = None
            window.ontouchmove = None
            window.onmouseup = None
            window.ontouchend = None
            self.zooming = 0
            return
        if not self.moving:
            print('bug')
            return
        document.getElementById('top').style.background = TOP_INACTIVE
        self.get_event(event)
        column, line = self.get_coord(self.event_x, self.event_y)
        if self.moved and self.student_clicked: # pylint: disable=singleton-comparison
            self.moving = self.student_clicked
            column, line = self.get_coord(self.event_x, self.event_y, True)
            self.drag_stop_student(column, line)
        elif not self.moved:
            # Simple click
            if self.the_menu.selected:
                self.the_menu.select_and_close()
            elif column != -1 and not MAPPER and not self.the_menu.opened_at(line, column):
                if self.lines[line][column] == 's':
                    self.open_computer_menu(line, column)
                elif self.lines[line][column] == 'g':
                    self.open_room_menu(line, column)
                elif self.student_clicked:
                    self.open_student_menu(line, column,
                        STUDENT_DICT[self.student_clicked['login']])
                else:
                    self.the_menu.close()
                    self.drag_stop_click_on_room(event, column, line)
            else:
                self.the_menu.close()
        else:
            # Panning: recompute waiting room list
            self.compute_rooms_on_screen()
            self.update_waiting_room()
        if not self.the_menu.opened:
            window.onmousemove = None
            window.ontouchmove = None
        window.onmouseup = None
        window.ontouchend = None
        self.moving = False
    def animate_zoom(self):
        """Transition from zoom"""
        if len(self.transitions): # pylint: disable=len-as-condition
            self.scale, self.left, self.top = self.transitions.pop()
            scheduler.draw = "animate_zoom"
            setTimeout(bind(self.animate_zoom, self), 50)
        else:
            self.compute_rooms_on_screen()
            self.update_waiting_room()
    def compute_rooms_on_screen(self):
        """Compute the list of rooms on screen"""
        self.rooms_on_screen = {}
        for room_name, room in self.rooms.Items():
            left, top, width, height = room['position'][:4]
            right, bottom, _x_size, _y_size = self.xys(left + width, top + height)
            left, top, _x_size, _y_size = self.xys(left, top)
            if left > -5 and top > -5 and right < self.width + 5 and bottom < self.height + 5:
                self.rooms_on_screen[room_name] = True
    def update_waiting_room(self):
        """Update HTML with the current waiting student for the rooms on screen"""
        if self.pointer_on_student_list and not self.force_update_waiting_room:
            return
        self.force_update_waiting_room = False
        content = []
        for student in self.waiting_students:
            if student.room == '' or student.room.startswith('?'):
                room = self.ips[student.hostname]
                style = ''
                if room and self.building in BUILDINGS:
                    building, room_name = room.split(',')
                    if building != self.building:
                        continue
                    if not self.rooms_on_screen[room_name]:
                        continue
                else:
                    style = 'background: #FFCA'
                if student.checkpoint_time >= self.time_span[0] and student.checkpoint_time <= self.time_span[1]:
                    content.append(student.box(style))
        document.getElementById('waiting').innerHTML = ' '.join(content)
    def update_messages(self): # pylint: disable=no-self-use
        """Update HTML with the messages"""
        content = []
        for i, infos in enumerate(MESSAGES):
            if i in MESSAGES_TO_HIDE:
                continue
            login, date, message = infos
            message = html(message)
            message = message.replace(
                RegExp('(@[a-zA-Z]+)','g'),
                '<span style="background:#FF8">$1</span>')
            content.append(
                "<p>"
                + '<button onclick="hide_messages(0,'+i+')">×↑</button>'
                + '<button onclick="hide_messages('+i+','+i+')">×</button> '
                + nice_date(date)
                + ' ' + login + ' <b>' + message + '</b>')
        messages = document.getElementById('messages')
        if messages:
            messages.innerHTML = ' '.join(content)
            messages.scrollTop = 1000000 # messages.offsetHeight does not works
    def start_move_student(self, event):
        """Move student bloc"""
        if event.button != 0:
            return
        self.get_event(event)
        login = event.currentTarget.getAttribute('login')
        Student.moving_student = login
        Student.moving_element = event.currentTarget
        Student.moving_element.style.position = 'fixed'
        Student.moving_student_position = [self.event_x, self.event_y]
        document.body.onmousemove = document.body.ontouchmove = bind(self.move_student, self)
        window.onmouseup = document.body.ontouchend = bind(self.stop_move_student, self)
        self.move_student(event)
        event.preventDefault()
    def move_student(self, event):
        """To put the student on the map"""
        self.get_event(event)
        Student.moving_element.style.left = self.event_x + 'px'
        Student.moving_element.style.top = self.event_y + 'px'
        Student.moving_element.style.pointerEvents = 'none'
        pos = self.get_coord(self.event_x, self.event_y, True)
        if pos[0] != -1:
            if STUDENT_DICT[Student.moving_student].is_good_room(
                    self.get_room_name(pos[0], pos[1])):
                Student.moving_element.style.background = "#0F0"
            else:
                Student.moving_element.style.background = "#F00"
            document.getElementById('top').style.background = TOP_INACTIVE
        else:
            Student.moving_element.style.background = "#FFF"
            document.getElementById('top').style.background = TOP_ACTIVE
        scheduler.draw = "move_student"
        scheduler.draw_square_feedback = True
    def move_student_to(self, student, column, line):
        """Move the student on a chair.
        If not an A or B version, ask for the version.
        """
        version = self.lines[line][column]
        while version not in ('a', 'b'):
            if not OPTIONS['checkpoint']:
                version = 'a'
                break
            version = prompt(
                "Cette popup apparaît car l'étudiant\n"
                + "n'a pas été posé sur un sujet A ou B\n"
                + "comme vous deviez le faire.\n\n"
                + "Indiquez s'il fait la version A ou B :")
            if version:
                version = version.lower()
            else:
                version = student.version or 'a'
        record('checkpoint/' + COURSE + '/' + student.login + '/'
               + self.building + ',' + column + ',' + line + ',' + version)
        self.highlight_disk = [column, line, millisecs()]
    def stop_move_student(self, event):
        """Drop the student"""
        self.get_event(event)
        pos = self.get_coord(self.event_x, self.event_y, True)
        if pos[0] != -1:
            self.move_student_to(STUDENT_DICT[Student.moving_student], pos[0], pos[1])
        else:
            if Student.moving_student_position == [self.event_x, self.event_y]:
                create_realtime_spy(STUDENT_DICT[Student.moving_student])
        document.body.onmousemove = document.body.ontouchmove = None
        window.onmouseup = document.body.ontouchend = None
        document.getElementById('top').style.background = TOP_INACTIVE
        Student.moving_student = None
        Student.moving_element = None
        if pos[0] == -1:
            self.force_update_waiting_room = True
            scheduler.update_page = True
    def zoom_student(self, login):
        "Zoom on this student"
        student = STUDENT_DICT[login]
        if not student.building:
            return
        if student.building != self.building:
            self.change({"building": student.building})
            scheduler.update_page = True
            document.getElementById('buildings').value = student.building
        self.scale = self.width / 5
        self.left = self.top = 0
        left, top, _dx, _dy = self.xys(student.column, student.line)
        self.left = self.real_left - left + (self.width - self.real_left) / 2
        self.top = self.real_top - top + (self.height - self.real_top) / 2
        scheduler.draw = "zoom_student"
        self.write_location()
    def draw_move_timer(self):
        """Circle indicating the time before the student move is allowed"""
        if STUDENT_DICT[self.student_clicked['login']].grade:
            return # Do not move graded student
        ctx = document.getElementById('canvas').getContext("2d")
        x_pos, y_pos, x_size, _y_size = self.xys(self.student_clicked['column'], self.student_clicked['line'])
        ctx.strokeStyle = "#FF00FF80"
        ctx.lineWidth = 0.2 * self.scale
        angle = min(1, (millisecs() - self.drag_millisec_start) / LONG_CLICK)
        ctx.beginPath()
        ctx.arc(x_pos, y_pos, x_size/1.8, 0, Math.PI*2*angle)
        ctx.stroke()
    def pointer_enter_student_list(self):
        document.getElementById('pointer_on_student_list').style.display = 'block'
        self.pointer_on_student_list = True
    def pointer_leave_student_list(self):
        document.getElementById('pointer_on_student_list').style.display = 'none'
        self.pointer_on_student_list = False

def hide_messages(first, last):
    """Hide the indicated message indexes (last not included)"""
    for i in range(first, last + 1):
        MESSAGES_TO_HIDE[i] = 1
    ROOM.update_messages()

def highlight_student(element):
    """Display its place"""
    if element and not Student.moving_student and ROOM.moving != True and ROOM.moving != ROOM.student_clicked:
        Student.highlight_student = element.getAttribute('login')
    else:
        Student.highlight_student = None
        scheduler.draw = "erase «press space»"

def cmp_student_name(student_a, student_b):
    """Compare 2 students keys (static PC, name, surname)"""
    if student_a.sort_key > student_b.sort_key:
        return 1
    return -1

def cmp_student_position(student_a, student_b):
    """Compare 2 students column"""
    return student_a.column - student_b.column
def cmp_student_position_reverse(student_a, student_b):
    """Compare 2 students column"""
    return student_b.column - student_a.column

def create_room_selector(building_name):
    return (
        '''<select style="width:100%;margin-top:0.7em" id="buildings"
                   onchange="ROOM.change({'building':this.value}); scheduler.update_page = true;">'''
        + ''.join(['<option'
                   + (building == building_name and ' selected' or '')
                   + '>' + building.replace('empty', LOGIN) + '</option>'
                   for building in BUILDINGS_SORTED])
        + '</select>')

def create_page(building_name):
    """Fill the page content"""
    content = ['<title>ⒶⒷ', COURSE.split('=')[1], '</title>',
        '''<style>
        .name, LABEL { display: inline-block; vertical-align: top;
            cursor: pointer; user-select: none;
        }
        .filter { background: #EEE; }
        .name { background: #EEEA; display: block; white-space: nowrap;
             padding-top: 0.3em; padding-bottom: 0.3em;
              overflow: hidden; }
        BODY { font-family: sans-serif;
               --menu-width: 12em;
               --menu-padding: 2em;
             }
        .name:hover { background: #FFF }
        .name SPAN { color: #888 }
        CANVAS { position: absolute; left: 0px; width: 100%; top: 0px; height: 100% }
        #waiting { display: inline }
        #top {z-index: 2; position: absolute;
              top: 0px; left: 0px; width: var(--menu-width); padding-right: var(--menu-padding); height: 100vh;
              overflow-y: scroll; overflow-x: visible;
              background: ''', TOP_INACTIVE, '''}
        #top * { vertical-align: middle }
        #top .course { font-size: 150%; }
        #top SELECT { font-size: 150%; }
        #top .drag_and_drop { display: inline-block }
        #live_spy {
            position: fixed;
            top: 0; right: 0;
            padding-left: calc(var(--menu-width) + var(--menu-padding));
            text-align: right;
            pointer-events: none;
            font-size: ''', SPY_FONT, '''px;
            line-height: ''', SPY_FONT, '''px;
        }
        #live_spy > DIV {
            display: inline-block;
            vertical-align: top;
            white-space: break-spaces;
            overflow: hidden;
            height: 1em;
            background: #FFCE;
            text-align: left;
            max-width: 35em;
        }
        #live_spy > DIV > DIV {
            margin-bottom: 100em;
        }
        #live_spy > DIV > B, .tt_student > B {
            display: block;
            background: #FF0E;
            position: sticky;
            top: 0px;
            text-align: right;
        }
        #source { margin-top: 7em }
        .icon { font-size: 200% ; display: inline-block; font-family: emoji;
                transition: transform 0.5s; cursor: pointer;
                margin-left: 0.5em; }
        .icon:hover { transform: scale(2, 2) }
        #messages { position: fixed ; right: 0px ; bottom: 0px ;
            max-width: 40vw;
            max-height: 100vh;
            background: #F88; opacity: 0.8;
            padding-left: 0.5em;
            overflow: auto;
            }
        #time SPAN { position: absolute; top: 0px; cursor: pointer; pointer-events: none; }
        #time { height: 2.5em ; background: #FFF; border: 1px solid #000;
                position: relative; margin-top: 0.2em; }
        #time SPAN.cursor { display: inline-block; transition: left 0.2s, right 0.2s, color 0.2s }
        #time SPAN.left { border-left: 0.2em solid black }
        #time SPAN.right { border-right: 0.2em solid black; text-align: right }
        #time SPAN.c, #time SPAN.s, #time SPAN.a { font-size: 83%; height: 1em }
        #time SPAN.c { border-left: 1px solid #000; top: 0px }
        #time SPAN.s { border-left: 1px solid #00F; top: 1em }
        #time SPAN.a { border-left: 1px solid #0D0; top: 2em; color: #0F0 }
        #time SPAN.ca { color: #080 ; }
        #time SPAN.cc { color: #000 ; }
        #time SPAN.cs { color: #00F ; }
        #time .blur_span { position: absolute; background: #FAA;  height: 100% ; top: 0px }
        #pointer_on_student_list {
            display: none;
            position: fixed;
            background: #AFAD;
            top: 10em;
            left: var(--menu-width);
        }
        #timetravel {
            position: absolute;
            top: 0px;
            right: 0px;
            z-index: 10;
        }
        #timeline {
            width: 100%;
            height: 1.2em;
            background: #888;
            position: relative;
            display: none;
            overflow: hidden;
            }
        #timeline SPAN {
            position: absolute;
            color: #FFF;
            white-space: nowrap;
            pointer-events: none;
        }
        .tt_student {
            display: inline-block;
            width: 30em;
            white-space: pre;
            background: #FFF;
            vertical-align: top;
            overflow: hidden;
            font-size: 12px;
            line-height: 12px;
            border-bottom: 1px solid #000;
        }
        </style>
        <div id="top"
             onmouseenter="ROOM.pointer_enter_student_list()"
             onmouseleave="ROOM.pointer_leave_student_list()"
        >
        <span class="icon" onclick="send_alert()">🚨</span>
        <span class="icon" onclick="search_student()">🔍</span>
        <button onclick="ROOM.do_rotate_180()" style="float:right;"><span style="font-family:emoji;font-size:200%; line-height:0.4px">↺</span><br>180°</button>
        <div id="TTL" style="line-height: 0.1em; padding-top: 0.7em"></div>
        ''']
    content.append(
        '<span class="course" id="display_session_name">'
        + COURSE.split('=')[1].replace(RegExp('_', 'g'), ' ')
        + '</span>')
    content.append(create_room_selector(building_name))
    content.append(
        '<label id="display_my_rooms">'
        + '<input id="my_rooms" onchange="ROOM.scale = 0; scheduler.draw=\'onchange\'"'
        + '       type="checkbox">Seulement mes salles</label>')
    content.append(
        '<div><label id="display_student_filter" class="filter">Mettre en évidence les logins :<br>'
        + '<input onchange="filters(this)" onblur="filters(this)"'
        + '       style="box-sizing: border-box; width:100%"></label></div>')
    if not OPTIONS.checkpoint:
        now = Date()
        now.setHours(12)
        now.setMinutes(0)
        content.append(
            '<div><label id="display_checkpoint_time" class="filter">Filtrer par jour de dernière interaction :<br>'
            + '<input id="checkpoint_time" onchange="update_checkpoint_time(this)" onblur="update_checkpoint_time(this)"'
            + '       value="' + nice_date(now.getTime()/1000) + '"'
            + '       style="box-sizing: border-box; width:100%"></label>')
        buttons = []
        content.append('<div id="checkpoint_time_buttons" style="display:flex;width:100%">')
        background = 'background:#8F8'
        for label in ["Auj.<br>", "Hier<br>", "A.H.<br>", "<br>", "<br>", "<br>", "<br>"]:
            buttons.append("""<button
             style="padding:0;flex:1;border-width:1px;font-size: 70%;""" + background
             + '" value="' + nice_date(now.getTime()/1000)
             + '" onclick="button_checkpoint_time(this)">'
             + label + now.toString().split(' ')[0] + '</button>')
            now.setTime(now.getTime() - 86400 * 1000)
            background = ''
        buttons = buttons[::-1]
        content.append(''.join(buttons))
        content.append('</div></div>')

    content.append('''
        <div class="drag_and_drop">Faites glisser les noms<br>vers ou depuis le plan</div>
        <div id="waiting"></div>
        <div id="pointer_on_student_list">Mettez le curseur sur le plan<br>
        pour activer la mise à jour<br>
        de la liste des étudiants.</div>
        </div>
        <canvas
            id="canvas"
            onwheel="ROOM.zoom(event)"
            onmousedown="ROOM.drag_start(event)"
            ontouchstart="ROOM.drag_start(event)"
        ></canvas>
        <div id="live_spy"></div>
        <div id="messages"></div>
        <div id="timetravel"><div id="timeline" onmousemove="time_jump(event)">
        Ascenseur temporel : mettez votre curseur ici</div><div id="tt_students"></div></div>
        ''')
    document.body.innerHTML = ''.join(content)
    document.body.onkeydown = key_event_handler
    set_visibility('display_student_filter')
    set_visibility('display_my_rooms')
    set_visibility('display_session_name')

def send_alert():
    """Sent an on map alert message to all teachers"""
    message = prompt("Message à afficher sur les plans de tous les surveillants :")
    if message:
        record('checkpoint/MESSAGE/' + COURSE + '/' + encodeURIComponent(message))

def update_page():
    """Update students"""
    if ROOM.moving and ROOM.moving != True: # pylint: disable=singleton-comparison
        student = STUDENT_DICT[ROOM.moving['login']]
        line = student.line
        column = student.column

    students = [Student(student) for student in STUDENTS if student[0]]
    students.sort(cmp_student_name)
    ROOM.students = []
    ROOM.waiting_students = []
    ROOM.nr_max_grade = {'a': 0, 'b': 0}
    for student in students:
        if student.building == ROOM.building:
            ROOM.students.append(student)
        elif not student.active:
            ROOM.waiting_students.append(student)
        if student.grade != '' and student.grade[1] > ROOM.nr_max_grade[student.version]:
            ROOM.nr_max_grade[student.version] = student.grade[1]

    if ROOM.moving and ROOM.moving != True: # pylint: disable=singleton-comparison
        student = STUDENT_DICT[ROOM.moving['login']]
        student.line = line
        student.column = column

    ROOM.put_students_in_rooms()
    ROOM.draw()
    ROOM.compute_rooms_on_screen()
    ROOM.update_waiting_room()
    highlight_buttons()

def close_exam(login):
    """Terminate the student exam"""
    record('checkpoint/' + COURSE + '/' + login + '/STOP')

def open_exam(login):
    """Open again the student exam"""
    record('checkpoint/' + COURSE + '/' + login + '/RESTART')

def canonize(txt):
    """Cleanup name"""
    return txt.lower().replace(RegExp("[^a-z0-9]", 'g'), '')

def get_login(student):
    """Get login from any information: name, surname, number"""
    if (not student
            or normalize_login(student) in STUDENT_DICT
            or student_id(student) in STUDENT_DICT):
        return student
    possibles = []
    possibles2 = []
    student = canonize(student)
    size = len(student)
    for login, verify in STUDENT_DICT.Items():
        if (canonize(verify.firstname) == student
                or canonize(verify.surname) == student
                or canonize(login) == student
           ):
            possibles.append([login, verify.surname, verify.firstname, verify.building])
        if (canonize(verify.firstname)[:size] == student # pylint: disable=consider-using-in
                or canonize(verify.surname)[:size] == student
                or canonize(login)[:size] == student
           ):
            possibles2.append([login, verify.surname, verify.firstname, verify.building])
    if len(possibles) == 0:
        if len(possibles2) == 0:
            return None
        possibles = possibles2
    if len(possibles) == 1:
        return possibles[0][0]
    choices = '\n'.join([
        str(i) + ' → ' + choice[0] + ' ' + choice[1] + ' ' + choice[2]
            + ' (' + (choice[3] or 'non placé') + ')'
        for i, choice in enumerate(possibles)])
    i = prompt(choices)
    if i:
        print(possibles[i][0])
        return possibles[i][0]
    return None

def search_student():
    """Zoom on a student"""
    student = prompt("Début de numéro d'étudiant ou nom ou prénom à chercher")
    if not student:
        return
    student = get_login(student)
    if student:
        ROOM.zoom_student(student)
    else:
        alert('Introuvable')

def key_event_handler(event):
    """The spy popup receive a keypress"""
    if event.key == 'f' and event.ctrlKey:
        search_student()
        event.preventDefault()
    if event.key == ' ' and Student.highlight_student:
        student = STUDENT_DICT[Student.highlight_student]
        hostname = student.hostname
        if hostname in ROOM.positions:
            col, row = ROOM.positions[hostname]
            ROOM.move_student_to(student, col, row)
            ROOM.force_update_waiting_room = True
    if len(event.key) == 1:
        spy = document.getElementById('SPY-' + event.key.upper())
        if spy:
            while spy.tagName != 'DIV':
                spy = spy.parentNode
            spy.shared_worker.close()
            spy.remove()
            for i, infos in enumerate(TIME_TRAVEL_STUDENTS):
                if infos[1] is spy.shared_worker:
                    TIME_TRAVEL_STUDENTS.splice(i, 1) # pylint: disable=no-member
                    break
    if event.key == 'Escape':
        while document.getElementById('live_spy').firstChild:
            spy = document.getElementById('live_spy').firstChild
            spy.shared_worker.close()
            spy.remove()
        for _div, shared_worker, _journal, _student, _letter in TIME_TRAVEL_STUDENTS:
            shared_worker.close()
        while len(TIME_TRAVEL_STUDENTS):
            TIME_TRAVEL_STUDENTS.pop()
        document.getElementById('tt_students').innerHTML = ''
    if len(TIME_TRAVEL_STUDENTS) == 0:
        document.getElementById('timeline').style.display = 'none'
    if event.key == 'ArrowRight' and time_jump.seconds:
        time_jump(event, time_jump.seconds + 5)
    if event.key == 'ArrowLeft' and time_jump.seconds:
        time_jump(event, time_jump.seconds - 5)

def debug():
    """debug"""
    students_per_room = {}
    for room_name, room in ROOM.rooms.Items():
        students_per_room[room_name] = [student.login for student in room.students]
    print(JSON.stringify(students_per_room))

def set_visibility(attr):
    """For display_student_filter display_my_rooms display_session_name"""
    document.getElementById(attr).style.display = window.OPTIONS[attr] and 'initial' or 'none' # pylint: disable=consider-using-ternary

def reader(event): # pylint: disable=too-many-branches
    """Read the live journal"""
    length = len(event.target.responseText)
    while True: # Because it is a critical section
        chunk = event.target.responseText.substr(event.target.last_size or 0)
        if length == len(event.target.responseText):
            break
    event.target.last_size = length
    for expression in chunk.split('\n'):
        if expression == '':
            continue
        print(expression)
        data = JSON.parse(expression)
        if data[0] == 'messages':
            if data[2] == '+':
                MESSAGES.append(data[1])
            else:
                for message in data[1][len(MESSAGES):]:
                    MESSAGES.append(message)
            scheduler.update_messages = True
        elif data[0] == "active_teacher_room":
            if STUDENT_DICT[data[2]]:
                student = STUDENT_DICT[data[2]].data
                if data[3] == 4: # Blur because nbr blurs change
                    student.blurred = True
                elif data[3] == 9: # Focus because blur time change
                    student.blurred = False
                student[1][data[3]] = data[1]
            else:
                student = [data[2], data[1], { 'fn': "?", 'sn': "?" }]
                STUDENTS.append(student)
            Student(student) # Update structure from data
            scheduler.update_page = True
        elif data[0] == "infos":
            student = STUDENT_DICT[data[1]].data
            student[2] = data[2]
        else:
            window.OPTIONS[data[0]] = data[1]

    set_visibility('display_student_filter')
    set_visibility('display_my_rooms')
    set_visibility('display_session_name')

def split_time(secs):
    """61 → 1 m 01"""
    if secs >= 60:
        return Math.floor(secs/60) + 'm' + two_digit(secs%60)
    return secs

def simplify_line(line):
    return (line or '').split(start_comment)[0].replace(RegExp('[ :;,.{}\t]*', 'g'), '').lower()

def get_lines(source):
    """Remove not important characters"""
    return [line.split(start_comment)[0].replace(RegExp(';', 'g'), '')
            for line in (source or '').replace(RegExp('[ :,.{}\t]*', 'g'), '').lower().split('\n')]

start_comment, start_string, start_comment_bloc, end_comment_bloc = \
            language_delimiters(OPTIONS['language'])

def load_source(login):
    def record_source(journal):
        """Record for 'student' ID"""
        if record_source.done:
            return
        SOURCES[login] = []
        SOURCES_ORIG[login] = []
        record_source.done = True
        for q, question in journal.questions.Items():
            if q >= 0 and question.head >= 0:
                print('LOADED', len(question.first_source or " "), len(question.source or " "))
                initial = {}
                for line in get_lines(question.first_source):
                    initial[line] = True
                source = {}
                SOURCES[login].append(source)
                SOURCES_ORIG[login].append(question.source)
                for line in get_lines(question.source):
                    if line not in initial:
                        LINES[line] = (LINES[line] or 0) + 1
                        if line not in source: # Do not count twice the same
                            source[line] = True
                shared_worker.close()
        print("LOADED", login, len(journal.questions))
        ROOM.similarity_todo_pending -= 1
    print("LOAD", login)
    ROOM.similarity_todo_pending += 1
    shared_worker, _journal = create_shared_worker(login, record_source)

def compute_similarities():
    student = ROOM.similarity_todo[-1]

    if not GRAPH[student]:
        student_obj = STUDENT_DICT[student]
        GRAPH[student] = graph = []
        for student2 in STUDENTS:
            student2 = student2[0]
            if student2 != student:
                if student_obj.distance(STUDENT_DICT[student2]) < 4.13:
                    graph.append(student2)

    if student not in SOURCES:
        load_source(student)
    for student2 in GRAPH[student]:
        if student2 not in SOURCES:
            load_source(student2)
    if ROOM.similarity_todo_pending:
        # Wait all necessary sources
        return

    if not SIMILARITIES[student]:
        SIMILARITIES[student] = {}
    for student2 in GRAPH[student]:
        similarity = SIMILARITIES[student][student2]
        if similarity >= 0:
            continue
        common = 0
        for student_source, student_source2 in zip(SOURCES[student], SOURCES[student2]):
            for line in student_source:
                if line in student_source2:
                    common += 1
        ROOM.similarities.append(common)
        ROOM.similarities.sort(sort_integer)
        SIMILARITIES[student][student2] = common
        if not SIMILARITIES[student2]:
            SIMILARITIES[student2] = {}
        SIMILARITIES[student2][student] = common
        scheduler.draw = "similarity"

    ROOM.similarity_todo.pop()

def scheduler():
    """To not redraw needlessly"""
    if document.getElementById('buildings').value != ROOM.building:
        ROOM.change({'building': document.getElementById('buildings').value})
        scheduler.update_page = True
    secs = Math.floor(millisecs()/1000) - SERVER_TIME_DELTA
    if OPTIONS['state'] == 'Ready' and OPTIONS['checkpoint'] and secs != scheduler.secs:
        scheduler.secs = secs # To not recompute multiple time per seconds
        now = nice_date(secs) + ':00'
        if now >= OPTIONS['stop']:
            message = "Examen terminé"
            ROOM.state = 'done'
        elif now < OPTIONS['start']:
            message = 'Début dans ' + split_time(ROOM.start_timestamp - secs)
            ROOM.state = 'pending'
        else:
            message = 'Fin dans ' + split_time(ROOM.stop_timestamp - secs)
            ROOM.state = 'running'
        document.getElementById('TTL').innerHTML = message
    if Student.moving_student or Student.highlight_student:
        ROOM.draw(scheduler.draw_square_feedback)
        hostname = STUDENT_DICT[Student.moving_student or Student.highlight_student].hostname
        if hostname in ROOM.positions:
            col, row = ROOM.positions[hostname]
            x_pos, y_pos, x_size, y_size = ROOM.xys(col, row)
            ctx = document.getElementById('canvas').getContext("2d")
            ctx.globalAlpha = 1
            ctx.lineWidth = x_size / 10
            if millisecs() % 1000 > 500:
                ctx.strokeStyle = "#000"
            else:
                ctx.strokeStyle = "#0F0"
            ctx.beginPath()
            ctx.arc(x_pos, y_pos - 0.1*y_size, x_size/1.8, 0, Math.PI*2, True)
            ctx.closePath()
            ctx.stroke()
            if not Student.moving_student:
                ctx.save()
                ctx.font = "20px sans-serif"
                ctx.fillStyle = "#00F"
                ctx.strokeStyle = "#FFF"
                ctx.lineWidth = 4
                label = "Appuyez sur Espace pour placer"
                x_coord = x_pos + x_size / 1.8
                y_coord = y_pos + 0.15 * y_size
                ctx.strokeText(label, x_coord, y_coord)
                ctx.fillText(label, x_coord, y_coord)
                label = STUDENT_DICT[Student.highlight_student].__str__()
                y_coord += 25
                ctx.strokeText(label, x_coord, y_coord)
                ctx.fillText(label, x_coord, y_coord)
                ctx.restore()
        return
    if scheduler.update_page:
        scheduler.update_page = False
        update_page()
    elif scheduler.draw:
        scheduler.draw = False
        ROOM.draw(scheduler.draw_square_feedback)
    if scheduler.update_messages:
        scheduler.update_messages = False
        ROOM.update_messages()
    scheduler.draw_square_feedback = False
    scheduler.draw = ROOM.highlight_disk
    if len(ROOM.similarity_todo) and not ROOM.similarity_todo_pending:
        compute_similarities()

    # Display circle to indicate time before allowed to be moved
    if ROOM.moving == True and ROOM.student_clicked and not ROOM.moved and not ROOM.the_menu.opened:
        ROOM.draw_move_timer()

IP_TO_PLACE = {}

def clean_up_bad_placements():
    """Remove error of placement in IPS"""
    # Search the most probable placement for an IP
    # IP_TO_PLACE = { ip_addr: [ [place_list], nbr ] }
    # It is a list in case of equality
    for key, values in IPS.Items():
        for ip_addr, nbr in values.Items():
            if ip_addr.replace(RegExp("[0-9.]", 'g'), '') == '':
                continue # An IP
            if ip_addr in IP_TO_PLACE:
                if nbr > IP_TO_PLACE[ip_addr][1]:
                    IP_TO_PLACE[ip_addr] = [[key], nbr]
                elif nbr == IP_TO_PLACE[ip_addr][1]:
                    IP_TO_PLACE[ip_addr][0].append(key)
            else:
                IP_TO_PLACE[ip_addr] = [[key], nbr]

    # Remove placement errors
    for key, values in IPS.Items():
        # Keep most probables IP on this place
        nr_max = max(*[
            nbr
            for ip_addr, nbr in values.Items()
            if ip_addr in IP_TO_PLACE and key in IP_TO_PLACE[ip_addr][0]
        ]) # Max number of occurrences of probable IPs
        new_values = {}
        for ip_addr, nbr in values.Items():
            if ip_addr in IP_TO_PLACE and key in IP_TO_PLACE[ip_addr][0]:
                if nbr == nr_max:
                    new_values[ip_addr] = nbr
                else:
                    # The IP will not be used on the place
                    # Remove it from possibles
                    IP_TO_PLACE[ip_addr][0] = [i
                                            for i in IP_TO_PLACE[ip_addr][0]
                                            if i != key]
        #if len(new_values) > 1:
        #    print(key, values, new_values)
        #    for ip_addr in new_values:
        #        print(ip_addr, JSON.stringify(IP_TO_PLACE[ip_addr]))
        IPS[key] = new_values

    # Display enhanced version
    lines = []
    for room, hosts in CONFIG.ips_per_room.Items():
        lines.append(room)
        for host in hosts.split(' '):
            if host in IP_TO_PLACE:
                if len(IP_TO_PLACE[host][0]) == 1: # Not ambiguous
                    _building, pos_x, pos_y = IP_TO_PLACE[host][0][0].split(',')
                    host += ',' +  pos_x + ',' + pos_y
            lines.append(' ' + host)
        lines.append('\n')
    print(''.join(lines))

def display_student_screen(journal, feedback, student, letter):
    if journal.position > 0:
        before = html(journal.content[:journal.position-1])
        cursor = html(journal.content[journal.position-1])
    else:
        before = ''
        cursor = ''
    feedback.innerHTML = (
        '<b>Q' + (journal.question+1)
        + '<var style="font-weight: normal; color: #888">(«<i id="SPY-'
        + letter + '">' + letter + '</i>» pour fermer)</var> '
        + student.surname + ' ' + student.firstname
        + '</b><div>'
        + before + '<span style="color:#FFF;background:#000">' + cursor + '</span>'
        + html(journal.content[journal.position:])
        + '</div>')
    feedback.style.height = (journal.height or 20) * SPY_FONT + 'px'
    feedback.scrollTo({'top': journal.scroll_line * SPY_FONT, 'behavior': 'smooth'})

TIME_TRAVEL_STUDENTS = []

def time_jump(event=None, secs=None):
    timeline = document.getElementById('timeline')
    if secs:
        t01 = (secs - ROOM.start_timestamp) / (ROOM.stop_timestamp -  ROOM.start_timestamp)
        if t01 < 0:
            t01 = 0
        elif t01 > 1:
            t01 = 1
    else:
        if event:
            t01 = event.layerX / timeline.offsetWidth
        else:
            t01 = 0
        secs = (1 - t01) * ROOM.start_timestamp + t01 * ROOM.stop_timestamp
    time_jump.seconds = secs
    timestamp = str('T' + str(secs))
    if event:
        if t01 < 0.5:
            pos = 'left:' + t01 * timeline.offsetWidth
        else:
            pos = 'right:' + (1 - t01) * timeline.offsetWidth
        timeline.innerHTML = (
            '<span style="' + pos + 'px">use ← → keys '
            + nice_date(secs, True).replace(' ', ' <b>')
            + '</b></span>')
    for div, _shared_worker, journal, student, letter in TIME_TRAVEL_STUDENTS:
        for i, line in enumerate(journal.lines):
            if line.startswith('T') and line > timestamp:
                journal.see_past(i)
                break
        display_student_screen(journal, div, student, letter)

def create_timetravel(login):
    # line_height
    # time
    def nothing(_journal):
        time_jump()
    div = document.createElement('DIV')
    div.className = 'tt_student'
    student = STUDENT_DICT[login]
    letter = spy_letter(student)
    document.getElementById('tt_students').appendChild(div)
    div.shared_worker, journal = create_shared_worker(login, nothing)
    TIME_TRAVEL_STUDENTS.append([div, div.shared_worker, journal, student, letter])
    document.getElementById('timeline').style.display = 'block'

def spy_letter(student):
    letters = []
    for spy in document.getElementById('live_spy').childNodes:
        i = spy.getElementsByTagName('I')
        if len(i):
            letters.append(i[0].innerHTML)
    for spy in document.getElementById('tt_students').childNodes:
        i = spy.getElementsByTagName('I')
        if len(i):
            letters.append(i[0].innerHTML)
    letter = student.surname[0].upper()
    if letter not in letters:
        return letter
    letter = student.firstname[0].upper()
    if letter not in letters:
        return letter
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        if letter not in letters:
            return letter
    return '1'

def create_realtime_spy(student):
    """
    Choisir login
    """
    letter = spy_letter(student)
    feedback = document.createElement('DIV')
    document.getElementById('live_spy').appendChild(feedback)
    def update_real_time(journal):
        if not journal.remote_update:
            return
        display_student_screen(journal, feedback, student, letter)
    feedback.shared_worker, _journal = create_shared_worker(student.login, update_real_time)

try:
    INFO = JSON.parse(decodeURI(location.hash[1:]))
except SyntaxError:
    INFO = {}
if 'building' not in INFO:
    INFO['building'] = OPTIONS.default_building or "Nautibus"
if 'start' not in OPTIONS:
    OPTIONS['start'] = OPTIONS['stop'] = nice_date(0)

if COURSE == "=MAPS":
    document.body.innerHTML = ('<title>Hostmap</title><span id="top"></span>'
        + create_room_selector(INFO.building).replace("margin", "position:absolute;z-index:2;NOmargin")
        + '''<style>BODY { margin: 0px }</style><canvas
            id="canvas"
            style="position:absolute; left:0px; width:100vw; top:0px; height: 100vh;"
            onwheel="ROOM.zoom(event)"
            onmousedown="ROOM.drag_start(event)"
            ontouchstart="ROOM.drag_start(event)"
        ></canvas><div id="waiting" style="display:none"></div><div id="checkpoint_time_buttons"></div>'''
    )
    ROOM = Room(INFO)
    scheduler.update_page = True
else:
    create_page(INFO.building)
    ROOM = Room(INFO)
    update_page()
    if STUDENT_DICT[INFO['student']]:
        ROOM.zoom_student(INFO['student'])
    scheduler.update_page = True
    REAL_COURSE = COURSE

    def reload_on_error(event):
        if isinstance(event, ProgressEvent):
            return
        print('Connexion closed')
        print(event)
        window.location.reload()

    if COURSE == "=IPS":
        clean_up_bad_placements()
    else:
        XHR = eval('new XMLHttpRequest()') # pylint: disable=eval-used
        XHR.addEventListener('readystatechange', reader)
        XHR.addEventListener('error', reload_on_error)
        XHR.open("GET", 'journal/' + COURSE + '?ticket=' + TICKET)
        XHR.send()

SERVER_TIME_DELTA = int(millisecs()/1000 - SERVER_TIME)

setInterval(scheduler, 20)
