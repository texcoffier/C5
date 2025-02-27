"""
Display checkpoint page

"""
# pylint: disable=chained-comparison

HELP_LINES = 10
BOLD_TIME = 300 # In seconds for new students in checking room
BOLD_TIME_ACTIVE = 300 # In seconds for last activity
DECAL_Y = 0.15
TOP_INACTIVE = '#FFFD'
TOP_ACTIVE = '#8F8D'
ROOM_BORDER = ('d', 'w', '|', '-', '+', None)
MESSAGES_TO_HIDE = {}
LONG_CLICK = 500

BUILDINGS_SORTED = list(BUILDINGS)
BUILDINGS_SORTED.sort()

MAPPER = COURSE in ("=IPS", "=MAPS")

def filters(element):
    """Update student filter"""
    logins = {}
    for login in element.value.split(' '):
        logins[login] = True
    filters.logins = logins
    ROOM.update_waiting_room()

filters.logins = {}

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

class Room: # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Graphic display off rooms"""
    drag_x_current = drag_x_start = drag_y_current = drag_y_start = None
    scale = min_scale = 0
    top = 0
    left = 0
    x_max = 0
    moving = False
    students = []
    selected_computer = None
    selected_item = None
    selected_student = student_menu = None
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
    def __init__(self, building):
        self.menu = document.getElementById('top')
        self.ips = {}
        self.positions = {}
        for room_name in CONFIG.ips_per_room:
            for hostname in CONFIG.ips_per_room[room_name].split(' '):
                if hostname != '':
                    host, pos_x, pos_y = (hostname + ',,').split(',')[:3]
                    self.ips[host] = room_name
                    self.positions[host] = [pos_x, pos_y]
        self.change(building)
        window.onblur = mouse_leave
        window.onfocus = mouse_enter
        window.onresize = update_page
        self.draw_times = []
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
    def change(self, building):
        """Initialise with a new building"""
        self.building = building
        if building not in BUILDINGS: # It is a teacher login
            building = 'empty'
        self.lines = BUILDINGS[building].split('\n')
        self.x_max = max(*[len(line) for line in self.lines]) + 1
        self.real_left = self.menu.offsetWidth
        self.real_top = document.getElementById('canvas').offsetTop
        self.left = self.real_left
        self.top = self.real_top
        self.drag_x_current = self.drag_x_start = None
        self.drag_y_current = self.drag_y_start = None
        self.moving = False
        self.scale = 0
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
        self.student_menu = self.selected_student = None # Why not computer menu?
        self.time_span = [0, 1e10]
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
                    self.rooms[name] = {'label': [start-1, line],
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
            for i, value in enumerate(self.lines_y):
                self.lines_y[i] = position - self.lines_y[i] + height
    def get_room(self, column, line):
        """Get room position : col_min, lin_min, width, height, center_x, center_y"""
        if not self.lines[line] or not self.lines[line][column]: # XXX Called outside the map
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
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        new_todo.append([lin+dy, col+dx])
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
    def draw_menu(self, ctx, x_pos, y_pos, selected, model):
        """
        Returns the text overed by the mouse
        """
        ctx.font = "24px sans-serif"
        if self.rotate_180:
            x_pos -= self.scale
            y_pos -= self.scale
        padding = 10
        menu_width = 0
        y_size = 0
        for message in model:
            box = ctx.measureText(message)
            menu_width = max(box.width, menu_width)
            descent = box.fontBoundingBoxDescent
            y_size = max(box.fontBoundingBoxAscent + descent, y_size)
        menu_width += 2 * padding
        menu_line = y_size * 1.1
        menu_height = len(model) * menu_line

        ctx.fillStyle = "#FFC"
        ctx.globalAlpha = 0.9
        ctx.fillRect(x_pos + self.scale, y_pos, menu_width, menu_height)

        ctx.strokeStyle = "#000"
        ctx.lineWidth = 2
        ctx.lineCap = 'round'
        ctx.moveTo(x_pos, y_pos)
        ctx.lineTo(x_pos + self.scale + menu_width, y_pos)
        ctx.lineTo(x_pos + self.scale + menu_width, y_pos + menu_height)
        ctx.lineTo(x_pos + self.scale, y_pos + menu_height)
        ctx.lineTo(x_pos + self.scale, y_pos + self.scale)
        ctx.lineTo(x_pos, y_pos + self.scale)
        ctx.lineTo(x_pos, y_pos)
        ctx.stroke()

        x_pos += self.scale + padding
        ctx.globalAlpha = 1
        ctx.fillStyle = "#000"
        selected_item = None
        for i, message in enumerate(model):
            if message.startswith('*'):
                ctx.font = "bold 24px sans-serif"
                message = message[1:]
            else:
                ctx.font = "24px sans-serif"
            y_item = y_pos + menu_line * i
            if message in selected:
                ctx.fillStyle = "#FDD"
                ctx.fillRect(x_pos, y_item, menu_width - 2 * padding, menu_line)
                ctx.fillStyle = "#000"
            # print(self.event_x, x_pos, x_pos + menu_width, y_item, self.event_y , y_item + menu_line)
            if (i > 1 # pylint: disable=too-many-boolean-expressions
                    and message != ''
                    and self.event_x > x_pos
                    and self.event_x < x_pos + menu_width
                    and self.event_y > y_item
                    and self.event_y < y_item + menu_line
               ):
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos, y_item, menu_width - 2 * padding, menu_line)
                ctx.fillStyle = "#000"
                selected_item = message
            ctx.fillText(message, x_pos, y_item + menu_line - descent)
        return selected_item
    def draw_computer_menu(self, ctx):
        """The computer problems menu"""
        messages = self.draw_computer_problems(ctx)
        if not self.selected_computer or self.selected_computer[0] != self.building:
            return
        x_pos, y_pos, _x_size, _y_size = self.xys(self.selected_computer[1] - 0.5,
                                                  self.selected_computer[2] - 0.5)
        self.selected_item = self.draw_menu(ctx, x_pos, y_pos, messages,
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
            ])
    def draw_computer_problems(self, ctx):
        """Draw a red square on computer with problems"""
        ctx.fillStyle = "#F00"
        ctx.globalAlpha = 0.5
        messages = []
        for building, column, line, message, _time in CONFIG.computers:
            if building == self.building:
                x_pos, y_pos, x_size, y_size = self.xys(column - 0.5, line - 0.5)
                ctx.fillRect(x_pos, y_pos, x_size, y_size)
                if (self.selected_computer
                        and self.selected_computer[1] == column
                        and self.selected_computer[2] == line):
                    messages.append(message)
        ctx.globalAlpha = 1
        return messages
    def draw_students(self, ctx): # pylint: disable=too-many-branches
        """Draw students names"""
        now = seconds()
        line_height = self.scale/4
        ctx.font = 'bold ' + line_height + "px sans-serif"
        if self.rotate_180:
            self.students.sort(cmp_student_position_reverse)
        else:
            self.students.sort(cmp_student_position)
        char_size = ctx.measureText('x')
        for student in self.students:
            if (student.column < self.left_column or student.column > self.right_column
                    or student.line < self.top_line or student.line > self.bottom_line):
                continue

            x_pos, y_pos, x_size, y_size = self.xys(student.column, student.line)
            x_pos -= self.scale / 2
            ctx.globalAlpha = 0.7
            if student.active:
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos, y_pos - y_size/2, x_size, y_size)
            if (self.lines_height[2*student.line] < 0.5
                    or self.columns_width[2*student.column] < 0.5):
                continue
            width = max(ctx.measureText(student.firstname).width,
                        ctx.measureText(student.surname).width)
            if student.data.blurred:
                ctx.fillStyle = "#F0F"
                ctx.fillRect(x_pos - width/4, y_pos - y_size/2 - width/4,
                             width + 2 + width/4, y_size + 2 + width/2)
            else:
                ctx.fillStyle = "#FFF"
                ctx.fillRect(x_pos, y_pos - y_size/2, width + 2, y_size + 2)
            if student.blur:
                ctx.fillStyle = "#F00"
                ctx.fillRect(x_pos, y_pos - y_size/2,
                             student.blur / 10 * x_size, y_size/2)
            if student.nr_questions_done:
                ctx.fillStyle = "#0C0"
                ctx.fillRect(x_pos, y_pos + 1,
                             student.nr_questions_done / 10 * x_size, y_size/2)
            if student.with_me():
                if student.active:
                    if now - student.checkpoint_time < BOLD_TIME_ACTIVE:
                        ctx.fillStyle = "#000"
                    else:
                        ctx.fillStyle = "#00F"
                else:
                    ctx.fillStyle = "#080"
            else:
                if student.active:
                    if now - student.checkpoint_time < BOLD_TIME_ACTIVE:
                        ctx.fillStyle = "#888"
                    else:
                        ctx.fillStyle = "#88F"
                else:
                    ctx.fillStyle = "#484"
            if not student.good_room:
                ctx.fillStyle = "#F88"
            ctx.globalAlpha = 1
            ctx.fillText(student.firstname, x_pos, y_pos - char_size.fontBoundingBoxDescent)
            ctx.fillText(student.surname, x_pos, y_pos + line_height - char_size.fontBoundingBoxDescent)
            grading = ''
            if student.grade != '':
                grading += student.grade[0]
                if student.feedback >= 4:
                    grading += '👁'
                grading += '(' + student.grade[1] + 'notes'
                if student.feedback >= 5:
                    grading += '👁'
                grading += ')'
            if student.feedback >= 3:
                grading += '#👁'
            if grading != '':
                if student.grade[1] == self.nr_max_grade:
                    if student.feedback >= 5:
                        ctx.fillStyle = "#0A0"
                    else:
                        ctx.fillStyle = "#880"
                else:
                    ctx.fillStyle = "#000"
                ctx.fillText(grading, x_pos, y_pos + 2*line_height)
            if student.blur_time > 2:
                ctx.fillStyle = "#000"
                ctx.fillText(student.blur_time + ' secs', x_pos, y_pos - line_height)
        ctx.globalAlpha = 1
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
            for room in self.rooms:
                coord_x, coord_y, width, height = self.rooms[room].position
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

        if self.moving and self.moving != True:
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
                ctx.fillText(text, column, line)
                width = ctx.measureText(text).width
                if width > max_width:
                    max_width = width
                if first:
                    column += indent
                    first = False
                line += size
            return max_width + size/2

        column = self.left
        column += draw_messages(column, [
            "Navigation sur le plan :",
            "Utilisez la molette pour zoomer.",
            "Tirez le fond d'écran pour le déplacer.",
            "Cliquez sur le sol d'un salle pour zoomer."])
        column += draw_messages(column, [
            "Le carré jaune des étudiants :",
            "Tirez-le pour déplacer l'étudiant.",
            "Tirez-le tout à gauche pour le remettre en salle d'attente.",
            "Il passe en violet quand la fenêtre perd le focus.",
            "Il se remplit de rouge à chaque perte de focus.",
            "Il se remplit de vert pour chaque bonne réponse."])
        column += draw_messages(column, [
            "Couleurs des noms d'étudiants : ",
            "#888 Avec un autre enseignant.",
            "#000 Travaille avec vous.",
            "#00F N'a rien fait depuis " + BOLD_TIME_ACTIVE/60 + " minutes.",
            "#080 Examen terminé avant la fin.",
            "#800 Dans la mauvaise salle."])
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
                            ip = place[0].split('.')[0]
                            ctx.fillStyle = "#FFF"
                            ctx.globalAlpha = 0.8
                            ctx.beginPath()
                            ctx.rect(x_pos, y_pos - y_size/2, ctx.measureText(ip).width, y_size)
                            ctx.fill()
                            ctx.fillStyle = "#000"
                            ctx.globalAlpha = 1
                            ctx.fillText(ip, x_pos, y_pos)
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
        for y, line in enumerate(self.lines):
            for x, char in enumerate(line):
                if char == 'a' or char =='b':
                    x_pos, y_pos, _x_size, _y_size = self.xys(x, y)
                    ctx.fillText(x + ',' + y, x_pos, y_pos)
        for full_ip, places_nr in IP_TO_PLACE.Items():
            if len(places_nr[0]) != 1:
                continue
            building_x_y = places_nr[0][0].split(',')
            if building_x_y[0] != self.building:
                continue
            ip = full_ip.split('.')[0]
            x_pos, y_pos, x_size, y_size = self.xys(building_x_y[1], building_x_y[2])
            x_pos -= x_size/2
            y_pos -= 0.25 * y_size
            ctx.fillStyle = "#FFF"
            ctx.globalAlpha = 0.7
            ctx.fillRect(x_pos, y_pos, ctx.measureText(ip).width, y_size * 0.8)
            ctx.globalAlpha = 1
            if self.positions[full_ip] == [building_x_y[1], building_x_y[2]]:
                ctx.fillStyle = "#080"
            else:
                ctx.fillStyle = "#000"
            ctx.fillText(ip, x_pos, y_pos + y_size/2)
    def draw_student_menu(self, ctx):
        if not self.student_menu:
            return
        student = self.student_menu

        x_pos, y_pos, _x_size, _y_size = self.xys(student.column - 0.5, student.line - 0.5)
        if student.active:
            state = "Clôturer l'examen"
        else:
            state = "Rouvrir l'examen"
        grade = "Noter l'étudiant"
        if self.state == 'done':
            grade = '*' + grade
        spy = "Regarder en temps réel"
        if self.state == 'running':
            spy = '*' + spy
        temps = "Temps bonus"
        if student.bonus_time:
            temps += ' (' + int(student.bonus_time / 60) + ' min.)'

        self.selected_student = self.draw_menu(ctx, x_pos, y_pos, [],
            [
                student.firstname + ' ' + student.surname,
                "", spy, temps, state, grade,
                student.mail or 'Adresse mail inconnue'
            ])
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
        self.draw_student_menu(ctx)
        self.draw_ips(ctx)
        self.draw_computer_menu(ctx)
    def do_zoom(self, pos_x, pos_y, new_scale):
        """Do zoom"""
        self.left += (pos_x - self.left) * (1 - new_scale/self.scale)
        self.top += (pos_y - self.top) * (1 - new_scale/self.scale)
        self.scale = new_scale
        self.compute_rooms_on_screen()
        self.update_waiting_room()
        scheduler.draw = "do_zoom"
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
                    return
                return student
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
            and not self.student_menu
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
            if self.selected_computer or self.student_menu:
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
            elif not self.moved:
                # Simple click
                student_menu = STUDENT_DICT[self.moving['login']]
                if student_menu is self.student_menu:
                    if self.state == 'running':
                        create_realtime_spy(self.student_menu)
                    elif self.state == 'done':
                        window.open(BASE + '/grade/' + COURSE + '/'
                                    + self.moving['login'] + '?ticket=' + TICKET)
                    self.student_menu = None
                else:
                    self.student_menu = STUDENT_DICT[self.moving['login']]
                self.selected_computer = None
                scheduler.draw = "drag_stop_student"
        else:
            self.highlight_disk = None
            record('checkpoint/' + COURSE + '/' + self.moving['login'] + '/EJECT')
            self.force_update_waiting_room = True
    def drag_stop_click_on_computer_menu(self):
        """Select a compulter malfunction"""
        if self.selected_item:
            if self.selected_item[-1] == '!':
                self.selected_item = ''
            record('computer/' + COURSE + '/'
                   + self.selected_computer[0] + '/'
                   + self.selected_computer[1] + '/'
                   + self.selected_computer[2] + '/'
                   + self.selected_item)
            self.selected_item = None
            scheduler.draw = "drag_stop_click_on_computer_menu"
            return True
        return False
    def drag_stop_click_on_computer(self, column, line):
        """Click on computer"""
        if column != -1 and self.lines[line][column] == 's':
            select = [self.building, column, line]
            if self.selected_computer != select:
                self.selected_computer = select
                scheduler.draw = True
                self.moving = False
            elif self.selected_computer:
                self.selected_computer = None
                scheduler.draw = "drag_stop_click_on_computer"
                self.moving = False
            return True
        return False
    def drag_stop_click_on_grade(self, column, line):
        """Click on computer"""
        if column != -1 and self.lines[line][column] == 'g' and not MAPPER:
            room = self.rooms[self.get_room_name(column, line)]
            if len(room.students) == 0:
                alert('Aucun étudiant dans cette salle')
                return True
            logins = []
            mails = []
            for student in room.students:
                logins.append(student.login)
                mails.append(student.mail or (student.login + '@?.?'))
            div = document.getElementById('spy')
            div.innerHTML = (
                '<div class="spytop">'
                + '<button class="closepopup" onclick="spy_close()">×</button> '
                + '<button id="open_tabs">Ouvrir ' + len(logins)
                + ' onglets</button> pour noter :<ol><li>'
                + '<li>'.join(mails)
                + '</ol>'
                + '</div>'
            )
            div.style.display = 'block'
            def open_tabs():
                for login in logins:
                    window.open(BASE + '/grade/' + COURSE + '/' + login
                        + '?ticket=' + TICKET)
            document.getElementById('open_tabs').onclick = open_tabs            
            return True
        return False
    def drag_stop_click_on_room(self, event, column, line):
        """Click on a room to zoom"""
        if (column != -1
                and self.lines[line][column] != 's'
                and self.scale < self.min_scale * 2):
            # Zoom on room
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
    def drag_stop_click_on_student_menu(self):
        """Choose an item in student menu"""
        if not self.student_menu:
            return False
        if not self.selected_student:
            return False
        login = self.student_menu.login
        if self.selected_student.startswith("Regarder"):
            create_realtime_spy(self.student_menu)
        elif self.selected_student.startswith("Clôturer"):
            close_exam(login)
        elif self.selected_student.startswith("Rouvrir"):
            open_exam(login)
        elif self.selected_student.startswith("Noter"):
            window.open(BASE + '/grade/' + COURSE + '/' + login + '?ticket=' + TICKET)
        elif self.selected_student.startswith("Temps"):
            minutes = prompt(
                "Nombre de minutes bonus pour l'étudiant.\n"
                + "C'est un temps total, pas un incrément.\n"
                + "Les tiers-temps ont déjà leur temps en plus.",
                int(self.student_menu.bonus_time / 60))
            if minutes is not None:
                record('checkpoint/TIME_BONUS/' + COURSE + '/'
                        + login + '/' + 60*int(minutes))
        elif self.selected_student:
            alert(self.selected_student)

        self.student_menu = self.selected_student = None
        scheduler.draw = "drag_stop not moved student_menu"
        return True
    def drag_stop(self, event):
        """Stop moving the map"""
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
        if self.moving != True or (not self.moved and self.student_clicked and not self.selected_computer): # pylint: disable=singleton-comparison
            self.moving = self.student_clicked
            column, line = self.get_coord(self.event_x, self.event_y, True)
            self.drag_stop_student(column, line)
        elif not self.moved:
            # Simple click
            if self.selected_computer:
                self.drag_stop_click_on_computer_menu()
                self.selected_computer = None
                scheduler.draw = "drag_stop not moved selected computer"
            elif self.student_menu:
                self.drag_stop_click_on_student_menu()
                self.student_menu = self.selected_student = None
                scheduler.draw = "drag_stop not moved student_menu"
            elif (not self.drag_stop_click_on_computer(column, line)
                  and not self.drag_stop_click_on_grade(column, line)
                  and not self.drag_stop_click_on_room(event, column, line)
                 ):
                # No new menu open
                pass
        else:
            # Panning: recompute waiting room list
            self.compute_rooms_on_screen()
            self.update_waiting_room()
        if not self.selected_computer and not self.student_menu:
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
            content.append(
                "<p>"
                + '<button onclick="hide_messages(0,'+i+')">×↑</button>'
                + '<button onclick="hide_messages('+i+','+i+')">×</button> '
                + nice_date(date)
                + ' ' + login + ' <b>' + html(message) + '</b>')
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
            self.change(student.building)
            scheduler.update_page = True
            document.getElementById('buildings').value = student.building
        self.scale = self.width / 5
        self.left = self.top = 0
        left, top, _dx, _dy = self.xys(student.column, student.line)
        self.left = self.real_left - left + (self.width - self.real_left) / 2
        self.top = self.real_top - top + (self.height - self.real_top) / 2
        scheduler.draw = "zoom_student"
    def draw_move_timer(self):
        """Circle indicating the time before the student move is allowed"""
        ctx = document.getElementById('canvas').getContext("2d")
        x_pos, y_pos, x_size, y_size = self.xys(self.student_clicked.column, self.student_clicked.line)
        ctx.strokeStyle = "#FF00FF80"
        ctx.lineWidth = 0.2 * self.scale
        angle = (millisecs() - self.drag_millisec_start) / LONG_CLICK
        if angle > 1:
            angle = 1
        ctx.beginPath()
        ctx.arc(x_pos, y_pos, x_size/1.8, 0, Math.PI*2*angle)
        ctx.stroke()

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
        self.firstname = data[2]['fn']
        self.surname = data[2]['sn']
        self.mail = data[2]['mail']
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
                   onchange="ROOM.change(this.value); scheduler.update_page = true;">'''
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
            font-size: 12px;
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
        #live_spy > DIV > B {
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
        </style>
        <div id="top"
             onmouseenter="ROOM.pointer_on_student_list=true"
             onmouseleave="ROOM.pointer_on_student_list=false"
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
        <div id="messages"></div>
        </div>
        <canvas
            id="canvas"
            onwheel="ROOM.zoom(event)"
            onmousedown="ROOM.drag_start(event)"
            ontouchstart="ROOM.drag_start(event)"
        ></canvas>
        <div id="live_spy"></div>
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
    ROOM.nr_max_grade = 0
    for student in students:
        if student.building == ROOM.building:
            ROOM.students.append(student)
        elif not student.active:
            ROOM.waiting_students.append(student)
        if student.grade != '' and student.grade[1] > ROOM.nr_max_grade:
            ROOM.nr_max_grade = student.grade[1]

    if ROOM.moving and ROOM.moving != True: # pylint: disable=singleton-comparison
        student = STUDENT_DICT[ROOM.moving['login']]
        student.line = line
        student.column = column

    ROOM.put_students_in_rooms()
    ROOM.draw()
    ROOM.compute_rooms_on_screen()
    ROOM.update_waiting_room()
    student = window.location.hash
    if student and len(student) > 1:
        ROOM.zoom_student(student[1:])
        window.location.hash = ''
        ROOM.draw()
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
    if event.key == 'Escape':
        while document.getElementById('live_spy').firstChild:
            spy = document.getElementById('live_spy').firstChild
            spy.shared_worker.close()
            spy.remove()

def set_time_bonus(element, login):
    """Recode and update student bonus time"""
    record('checkpoint/TIME_BONUS/' + COURSE + '/' + login + '/' + 60*int(element.value))
    element.style.background = "#DFD"
    STUDENT_DICT[login].bonus_time = element.value

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
            for message in data[1][len(MESSAGES):]:
                MESSAGES.append(message)
                scheduler.update_messages = True
        elif data[0] == "active_teacher_room":
            if STUDENT_DICT[data[2]]:
                student = STUDENT_DICT[data[2]].data
                if data[3] == 4: # Blur because nr blurs change
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

def scheduler():
    """To not redraw needlessly"""
    if document.getElementById('buildings').value != ROOM.building:
        ROOM.change(document.getElementById('buildings').value)
        scheduler.update_page = True
    secs = Math.floor(millisecs()/1000) - SERVER_TIME_DELTA
    if OPTIONS['state'] == 'Ready' and OPTIONS['checkpoint'] and secs != scheduler.secs:
        scheduler.secs = secs # To not recompute multiple time per seconds
        now = nice_date(secs) + ':00'
        if now >= OPTIONS['stop']:
            message = "Examen terminé"
            ROOM.state = 'done'
        elif now < OPTIONS['start']:
            message = 'Début dans ' + split_time(strptime(OPTIONS['start']) - secs)
            ROOM.state = 'pending'
        else:
            message = 'Fin dans ' + split_time(strptime(OPTIONS['stop']) - secs)
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

    # Display circle to indicate time before allowed to be moved
    if ROOM.moving == True and ROOM.student_clicked and not ROOM.moved and not ROOM.student_menu:
        ROOM.draw_move_timer()

IP_TO_PLACE = {}

def clean_up_bad_placements():
    """Remove error of placement in IPS"""
    # Search the most probable placement for an IP
    # IP_TO_PLACE = { ip: [ [place_list], nr ] }
    # It is a list in case of equality
    for key, values in IPS.Items():
        for ip, nr in values.Items():
            if ip.replace(RegExp("[0-9.]", 'g'), '') == '':
                continue # An IP
            if ip in IP_TO_PLACE:
                if nr > IP_TO_PLACE[ip][1]:
                    IP_TO_PLACE[ip] = [[key], nr]
                elif nr == IP_TO_PLACE[ip][1]:
                    IP_TO_PLACE[ip][0].append(key)
            else:
                IP_TO_PLACE[ip] = [[key], nr]

    # Remove placement errors
    for key, values in IPS.Items():
        # Keep most probables IP on this place
        nr_max = max(*[
            nr
            for ip, nr in values.Items()
            if ip in IP_TO_PLACE and key in IP_TO_PLACE[ip][0]
        ]) # Max number of occurrences of probable IPs
        new_values = {}
        for ip, nr in values.Items():
            if ip in IP_TO_PLACE and key in IP_TO_PLACE[ip][0]:
                if nr == nr_max:
                    new_values[ip] = nr
                else:
                    # The IP will not be used on the place
                    # Remove it from possibles
                    IP_TO_PLACE[ip][0] = [i
                                            for i in IP_TO_PLACE[ip][0]
                                            if i != key]
        #if len(new_values) > 1:
        #    print(key, values, new_values)
        #    for ip in new_values:
        #        print(ip, JSON.stringify(IP_TO_PLACE[ip]))
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


def create_realtime_spy(student):
    """
    Choisir login
    """
    letters = []
    for spy in document.getElementById('live_spy').childNodes:
        letters.append(spy.getElementsByTagName('I')[1].innerHTML)
    letter = student.surname[0].upper()
    if letter in letters:
        letter = student.firstname[0].upper()
    if letter in letters:
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            if letter not in letters:
                break

    feedback = document.createElement('DIV')
    feedback_header = document.createElement('B')
    feedback.appendChild(feedback_header)
    feedback_header.innerHTML = (
        '<i style="float:left;background:#FFF;color: #080;">?</i> <var style="font-weight: normal; color: #888">(«<i id="SPY-'
        + letter + '">' + letter + '</i>» pour fermer)</var> '
        + student.surname + ' ' + student.firstname
        )
    feedback_div = document.createElement('DIV')
    feedback.appendChild(feedback_div)
    document.getElementById('live_spy').appendChild(feedback)
    feedback_div.textContent = '0'
    line_height = feedback_div.offsetHeight

    def update_real_time(journal):
        if not journal.remote_update:
            return
        if journal.position > 0:
            before = html(journal.content[:journal.position-1])
            cursor = html(journal.content[journal.position-1])
        else:
            before = ''
            cursor = ''
        feedback_div.innerHTML = (
            before + '<span style="color:#FFF;background:#000">' + cursor + '</span>'
            + html(journal.content[journal.position:]))
        feedback.style.height = journal.height * line_height + 'px'
        feedback.scrollTo({'top': journal.scroll_line * line_height, 'behavior': 'smooth'})
        feedback_header.firstChild.innerHTML = 'Q' + (journal.question+1)

    feedback.shared_worker, _journal = create_shared_worker(student.login, update_real_time)

if COURSE == "=MAPS":
    default_building = BUILDINGS_SORTED[0]
    document.body.innerHTML = ('<title>Hostmap</title><span id="top"></span>'
        + create_room_selector(default_building).replace("margin", "position:absolute;z-index:2;NOmargin")
        + '''<style>BODY { margin: 0px }</style><canvas
            id="canvas"
            style="position:absolute; left:0px; width:100vw; top:0px; height: 100vh;"
            onwheel="ROOM.zoom(event)"
            onmousedown="ROOM.drag_start(event)"
            ontouchstart="ROOM.drag_start(event)"
        ></canvas><div id="waiting" style="display:none"></div><div id="checkpoint_time_buttons"></div>'''
    )
    ROOM = Room(default_building)
    scheduler.update_page = True
else:
    create_page(OPTIONS.default_building or "Nautibus")
    ROOM = Room(document.getElementById('buildings').value)
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
