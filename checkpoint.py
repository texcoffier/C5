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
    MESSAGES = MESSAGES
    CHECKPOINT = CHECKPOINT
    document = document
    window = window
    confirm = confirm
    prompt = prompt
    encodeURIComponent = encodeURIComponent
    JSON = JSON
    RegExp = RegExp
    alert = alert
    Math = Math
    bind = bind
    Date = Date
    setInterval = setInterval
    setTimeout = setTimeout
    hljs = hljs
    record = record
    html = html
except ValueError:
    pass

RELOAD_INTERVAL = 60 # Number of seconds between update data
HELP_LINES = 10
BOLD_TIME = 180 # In seconds for new students in checking room
BOLD_TIME_ACTIVE = 300 # In seconds for last activity
MENU_WIDTH = 9
MENU_HEIGHT = 10
MENU_LINE = 0.6
TOP_INACTIVE = '#FFFD'
TOP_ACTIVE = '#8F8D'
ROOM_BORDER = ('d', 'w', '|', '-', '+', None)
MESSAGES_TO_HIDE = {}
BEFORE_FIRST = 60 # Time scroll bar padding left in seconds

BUILDINGS_SORTED = [_ for _ in BUILDINGS]
BUILDINGS_SORTED.sort()

def filters(element):
    """Update student filter"""
    logins = {}
    for login in element.value.split(' '):
        logins[login] = True
    filters.logins = logins
    ROOM.update_waiting_room()

filters.logins = {}

def seconds():
    """Number of second as Unix"""
    return int(Date().getTime() / 1000)

def mouse_enter():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = True
def mouse_leave():
    """Manage window.mouse_is_inside"""
    window.mouse_is_inside = False

def two_digit(number):
    """ 6 → 06 """
    return ('0' + str(int(number)))[-2:]

def nice_date(secs):
    """seconds → human date"""
    js_date = Date()
    js_date.setTime(secs*1000)
    return (js_date.getFullYear()
            + '-' + two_digit(js_date.getMonth() + 1)
            + '-' + two_digit(js_date.getDate())
            + ' ' + two_digit(js_date.getHours())
            + ':' + two_digit(js_date.getMinutes())
           )

mouse_enter()

def distance2(x1, y1, x2, y2):
    """Squared distance beween 2 points"""
    return (x1 - x2) ** 2 + (y1 - y2) ** 2
def distance(x1, y1, x2, y2):
    """Distance beween 2 points"""
    return distance2(x1, y1, x2, y2) ** 0.5

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
    def __init__(self, building):
        self.menu = document.getElementById('top')
        self.change(building)
        window.onblur = mouse_leave
        window.onfocus = mouse_enter
        window.onresize = update_page
        setInterval(reload_page, RELOAD_INTERVAL * 1000)
        self.draw_times = []
        self.ips = {}
        for room_name in CONFIG.ips_per_room:
            for client_ip in CONFIG.ips_per_room[room_name].split(' '):
                if client_ip != '':
                    self.ips[client_ip] = room_name
    def xys(self, column, line):
        """Change coordinates system"""
        return [self.left + self.scale * self.columns_x[2*column],
                self.top + self.scale * self.lines_y[2*line],
                2 * self.scale * self.columns_width[2*column],
                2 * self.scale * self.lines_height[2*line]]
    def get_column_row(self, pos_x, pos_y):
        """Return character position (float) in the character map"""
        if pos_y < self.TOP or pos_x < self.LEFT:
            return [-1, -1]
        column = -1
        for i, position in enumerate(self.columns_x):
            if position > (pos_x - self.left) / self.scale:
                column = int(i/2)
                break
        line = -1
        for i, position in enumerate(self.lines_y):
            if position > (pos_y - self.top) / self.scale:
                line = int(i/2)
                break
        if column >= 0 and column <= self.x_max and line >= 0 and line < len(self.lines):
            return [column, line]
        return [-1, -1]
    def get_event(self, event):
        """Get event coordinates"""
        if event.touches:
            if len(event.touches):
                self.event_x = event.touches[0].pageX
                self.event_y = event.touches[0].pageY
            # else: 'ontouchend' : return the last coordinates
        else:
            self.event_x = event.clientX
            self.event_y = event.clientY

    def get_coord(self, event):
        """Get column line as integer"""
        self.get_event(event)
        column, line = self.get_column_row(self.event_x, self.event_y)
        column = Math.round(column)
        line = Math.round(line)
        return [column, line]

    def get_room_name(self, column, line):
        """Return the short room name"""
        for room_name in ROOM.rooms:
            left, top, width, height = ROOM.rooms[room_name].position
            if (column >= left and column <= left + width
                    and line >= top and line <= top + height
                ):
                return room_name
        return

    def change(self, building):
        """Initialise with a new building"""
        self.building = building
        if building not in BUILDINGS: # It is a teacher login
            building = 'empty'
        self.lines = BUILDINGS[building].split('\n')
        self.x_max = max([len(line) for line in self.lines]) + 1
        self.LEFT = self.menu.offsetWidth # LEFT
        self.TOP = 0 # self.menu.offsetHeight
        self.left = self.LEFT
        self.top = self.TOP
        self.drag_x_current = self.drag_x_start = None
        self.drag_y_current = self.drag_y_start = None
        self.moving = False
        self.update_sizes(0.5)
        self.update_visible()
        self.search_rooms()
        self.prepare_draw()
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
                self.rooms[name] = {'label': [start-1, line],
                                    'position': self.get_room_by_name(name)[:4]
                                   }
                chars = chars[:start] + replace + chars[column+1:]
            self.lines[line] = chars
    def put_students_in_rooms(self):
        """Create the list of student per room"""
        for room_name in self.rooms:
            self.rooms[room_name]['students'] = []
            self.rooms[room_name]['teachers'] = []
        for student in self.students:
            if student.short_room_name and student.short_room_name in self.rooms:
                self.rooms[student.short_room_name]['students'].append(student)
                teachers = self.rooms[student.short_room_name]['teachers']
                if student.teacher not in teachers:
                    teachers.append(student.teacher)
        for room_name in self.rooms:
            room = self.rooms[room_name]
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
            if student.active and student.with_me():
                (col_start, line_start, room_width, room_height, _center_x, _center_y
                ) = self.get_room(student.column, student.line)
                for i in range(2*col_start, 2*(col_start + room_width)):
                    self.columns_width[i] = 0.5
                for i in range(2*line_start, 2*(line_start + room_height)):
                    self.lines_height[i] = 0.5
        self.left = self.LEFT
        self.top = self.TOP
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
            if not self.lines[line][col_end]:
                return [0, 0, 0, 0, 0, 0]
        col_start = column
        while self.lines[line][col_start] not in ROOM_BORDER:
            col_start -= 1
            if not self.lines[line][col_start]:
                return [0, 0, 0, 0, 0, 0]
        room_width = col_end - col_start
        center_x = self.columns_x[2*col_start + room_width]

        line_end = line
        while self.lines[line_end][column] not in ROOM_BORDER:
            line_end += 1
            if not self.lines[line_end]:
                return [0, 0, 0, 0, 0, 0]
        line_start = line
        while self.lines[line_start][column] not in ROOM_BORDER:
            line_start -= 1
            if not self.lines[line_start]:
                return [0, 0, 0, 0, 0, 0]
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
    def draw_computer_menu(self, ctx, messages):
        """The computer problems menu"""
        x_pos, y_pos, x_size, y_size = self.xys(self.selected_computer[1] - 0.5,
                                                self.selected_computer[2] - 0.5)
        ctx.fillStyle = "#FFF"
        ctx.globalAlpha = 0.9
        ctx.fillRect(x_pos, y_pos, x_size, y_size)
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
            y_item = y_pos + MENU_LINE * y_size * i
            if message in messages:
                ctx.fillStyle = "#FDD"
                ctx.fillRect(x_pos + x_size, y_item,
                             MENU_WIDTH*x_size, MENU_LINE*y_size)
                ctx.fillStyle = "#000"
            if (i > 1 # pylint: disable=too-many-boolean-expressions
                    and message != ''
                    and self.event_x > x_pos + x_size
                    and self.event_x < x_pos + x_size + MENU_WIDTH*y_size
                    and self.event_y > y_item
                    and self.event_y < y_item + MENU_LINE * y_size
               ):
                ctx.fillStyle = "#FF0"
                ctx.fillRect(x_pos + x_size, y_item,
                             MENU_WIDTH*x_size, MENU_LINE*y_size)
                ctx.fillStyle = "#000"
                self.selected_item = message
            ctx.fillText(message, x_pos + x_size*1.5, y_item + (MENU_LINE - 0.1)*y_size)
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
    def draw_students(self, ctx):
        """Draw students names"""
        now = seconds()
        self.students.sort(cmp_student_position)
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
            ctx.fillText(student.firstname, x_pos, y_pos)
            ctx.fillText(student.surname, x_pos, y_pos + y_size/3)
        ctx.globalAlpha = 1
    def draw_map(self, ctx, canvas):
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

        ctx.lineCap = 'round'
        ctx.lineWidth = 2
        ctx.strokeStyle = "#000"
        for coords in self.walls:
            line(*coords)

        ctx.strokeStyle = "#4ffff6"
        for coords in self.windows:
            line(*coords)

        ctx.strokeStyle = "#ff0"
        for coords in self.doors:
            line(*coords)

        ctx.strokeStyle = "#000"
        ctx.fillStyle = "#000"
        ctx.font = self.scale + "px sans-serif,emoji"
        for char in self.chars:
            char_size = ctx.measureText(char)
            for column, line in self.chars[char]:
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
                ctx.fillText(char, x_pos - char_size.width/2, y_pos + y_size/2)
    def draw_square_feedback(self, ctx):
        """Single square feedback"""
        column, line = self.get_column_row(self.event_x, self.event_y)
        x_pos, y_pos, x_size, y_size = self.xys(column - 0.5, line - 0.5)
        ctx.fillStyle = "#0F0"
        ctx.globalAlpha = 0.5
        ctx.fillRect(x_pos, y_pos, x_size, y_size)
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
        line += size
        ctx.fillStyle = "#800"
        ctx.fillText("Dans la mauvaise salle.", column, line)

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
    def draw_teachers(self, ctx):
        """Display teacher names in front of rooms"""
        ctx.fillStyle = "#000"
        size = self.scale * 0.5
        ctx.font = size + "px sans-serif"
        for room_name in self.rooms:
            room = self.rooms[room_name]
            if room['teachers']:
                column, line = room['label']
                if (self.lines_height[2*line] < 0.5
                    or self.columns_width[2*column] < 0.5):
                    continue
                x_pos, y_pos, _x_size, _y_size = self.xys(column, line)
                ctx.fillText(room['teachers'], x_pos, y_pos)
    def draw(self, square_feedback=False):
        """Display on canvas"""
        start = Date().getTime()
        canvas = document.getElementById('canvas')
        self.width = canvas.offsetWidth
        self.height = canvas.offsetHeight
        if self.scale == 0:
            if document.getElementById('my_rooms').checked:
                self.only_my_students()
            else:
                self.update_sizes(0.5)
            self.update_visible()
            self.scale = self.min_scale = min(
                (self.width - self.LEFT) / self.columns_x[2 * self.x_max - 1],
                (self.height - self.TOP) / self.lines_y[2 * len(self.lines) - 1 - HELP_LINES])
            self.top = self.TOP
            if not document.getElementById('my_rooms').checked:
                self.top += HELP_LINES * self.scale
        ctx = canvas.getContext("2d")
        self.left_column, self.top_line = self.get_column_row(0, self.TOP+1)
        self.left_column = Math.max(self.left_column, 0) - 1
        self.top_line = Math.max(self.top_line, 0) - 2
        self.right_column, self.bottom_line = self.get_column_row(self.width, self.height)
        if self.right_column == -1:
            self.right_column = self.x_max
        if self.bottom_line == -1:
            self.bottom_line = len(self.lines)

        self.draw_map(ctx, canvas)
        ctx.font = self.scale/3 + "px sans-serif"
        self.draw_students(ctx)
        ctx.font = self.scale/2 + "px sans-serif"
        self.draw_teachers(ctx)
        messages = self.draw_computer_problems(ctx)
        if self.selected_computer and self.selected_computer[0] == self.building:
            self.draw_computer_menu(ctx, messages)
        if square_feedback:
            self.draw_square_feedback(ctx)
        self.draw_help(ctx)
        self.draw_times.append(Date().getTime() - start)
        if LOGIN == 'thierry.excoffier' and len(self.draw_times) > 10:
            self.draw_times = self.draw_times[1:]
            ctx.font = "16px sans-serif"
            ctx.fillText(int(sum(self.draw_times) / len(self.draw_times)) + 'ms', self.width - 70, 50)
    def do_zoom(self, pos_x, pos_y, new_scale):
        """Do zoom"""
        self.left += (pos_x - self.left) * (1 - new_scale/self.scale)
        self.top += (pos_y - self.top) * (1 - new_scale/self.scale)
        self.scale = new_scale
        self.draw()
    def zoom(self, event):
        """Zooming on the map"""
        self.do_zoom(event.clientX, event.clientY,
                     self.scale * (1000 - event.deltaY) / 1000)
        event.preventDefault()
    def drag_start(self, event):
        """Start moving the map"""
        column, line = self.get_coord(event)
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
        self.moved = False
        for student in self.students:
            if student.column == column and student.line == line:
                self.moving = student
                student.column_start = student.column
                student.line_start = student.line
                return
        self.drag_x_start = self.drag_x_current = self.event_x
        self.drag_y_start = self.drag_y_current = self.event_y
        self.moving = True
        self.draw()
    def drag_move(self, event):
        """Moving the map"""
        column, line = self.get_coord(event)
        if self.zooming:
            if len(event.touches) == 2:
                zooming = distance(self.event_x, self.event_y,
                                   event.touches[1].pageX, event.touches[1].pageY)
                self.do_zoom(self.zooming_x, self.zooming_y,
                             self.scale_start * zooming / self.zooming)
                self.draw()
                return
            self.zooming = 0
            window.onmousemove = window.ontouchmove = None
            window.onmouseup = window.ontouchend = None
            return
        if not self.moving:
            if self.selected_computer:
                self.draw()
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
                self.moving.line = line
                self.moving.column = column
                self.moving.update()
                document.getElementById('top').style.background = TOP_INACTIVE
            else:
                document.getElementById('top').style.background = TOP_ACTIVE
        self.draw()
    def drag_stop_student(self, column, line):
        """Stop moving a student"""
        if column != -1:
            if self.moving.column_start != column or self.moving.line_start != line:
                self.move_student_to(self.moving, column, line)
            elif not self.moved:
                # Simple click
                record('/checkpoint/SPY/' + COURSE + '/' + self.moving.login)
        else:
            record('/checkpoint/' + COURSE + '/' + self.moving.login + '/EJECT')
    def drag_stop_click_on_computer_menu(self):
        """Select a compulter malfunction"""
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
            return True
        return False
    def drag_stop_click_on_computer(self, column, line):
        """Click on computer"""
        if column != -1 and self.lines[line][column] == 's':
            select = [self.building, column, line]
            if self.selected_computer != select:
                self.selected_computer = select
                self.draw()
                self.moving = False
            return True
        return False
    def drag_stop_click_on_grade(self, column, line):
        """Click on computer"""
        if column != -1 and self.lines[line][column] == 'g':
            room = self.rooms[self.get_room_name(column, line)]
            if len(room.students) == 0:
                alert('Aucun étudiant à noter dans cette salle')
            else:
                logins = []
                for student in room.students:
                    logins.append(student.login)
                if confirm("Ouvrir " + len(logins) + ' onglets pour noter '
                    + ' '.join(logins)):
                    if confirm("OK pour noter la dernière sauvegarde\nCancel pour noter la dernière compilation"):
                        what = '1'
                    else:
                        what = '2'
                    for login in logins:
                        window.open('/grade/' + COURSE + '/' + login + '/' + what
                            + '?ticket=' + TICKET)
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
            if room_width == 0 or room_height == 0:
                return
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
        column, line = self.get_coord(event)
        if self.moving != True: # pylint: disable=singleton-comparison
            self.drag_stop_student(column, line)
        elif not self.moved:
            # Simple click
            if (not self.drag_stop_click_on_computer_menu()
                    and not self.drag_stop_click_on_computer(column, line)
                    and not self.drag_stop_click_on_grade(column, line)
                    and not self.drag_stop_click_on_room(event, column, line)
               ):
                # No special click
                if self.selected_computer:
                    self.selected_computer = None
                    self.draw()
        else:
            # Panning: recompute waiting room list
            self.compute_rooms_on_screen()
            self.update_waiting_room()
        if not self.selected_computer:
            window.onmousemove = None
            window.ontouchmove = None
        window.onmouseup = None
        window.ontouchend = None
        self.moving = False
    def animate_zoom(self):
        """Transition from zoom"""
        if len(self.transitions): # pylint: disable=len-as-condition
            self.scale, self.left, self.top = self.transitions.pop()
            self.draw()
            setTimeout(bind(self.animate_zoom, self), 50)
        else:
            self.compute_rooms_on_screen()
            self.update_waiting_room()
    def compute_rooms_on_screen(self):
        """Compute the list of rooms on screen"""
        self.rooms_on_screen = {}
        for room_name in self.rooms:
            room = self.rooms[room_name]
            left, top, width, height = room['position'][:4]
            right, bottom, _x_size, _y_size = self.xys(left + width, top + height)
            left, top, _x_size, _y_size = self.xys(left, top)
            if left > 0 and top > 0 and right < self.width and bottom < self.height:
                self.rooms_on_screen[room_name] = True
    def update_waiting_room(self):
        """Update HTML with the current waiting student for the rooms on screen"""
        content = []
        for student in self.waiting_students:
            if student.room == '':
                room = self.ips[student.client_ip]
                style = ''
                if room and self.building in BUILDINGS:
                    building, room_name = room.split(',')
                    if building != self.building:
                        continue
                    if not self.rooms_on_screen[room_name]:
                        continue
                else:
                    style = 'background: #FFCA'
                content.append(student.box(style))
        document.getElementById('waiting').innerHTML = ' '.join(content)
    def update_messages(self):
        """Update HTML with the messages"""
        content = []
        for i, infos in enumerate(MESSAGES):
            if i in MESSAGES_TO_HIDE:
                continue
            login, date, message = infos
            content.append(
                "<p>"
                + '<button onclick="MESSAGES_TO_HIDE['
                + i + ']=1;ROOM.update_messages()">×</button> '
                + nice_date(date)
                + ' ' + login + ' <b>' + html(message) + '</b>')
        document.getElementById('messages').innerHTML = ' '.join(content)
    def start_move_student(self, event):
        """Move student bloc"""
        login = event.currentTarget.getAttribute('login')
        Student.moving_student = STUDENT_DICT[login]
        Student.moving_element = event.currentTarget
        Student.moving_element.style.position = 'fixed'
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
        pos = self.get_column_row(self.event_x, self.event_y)
        if pos[0] != -1:
            if Student.moving_student.is_good_room(ROOM.get_room_name(pos[0], pos[1])):
                Student.moving_element.style.background = "#0F0"
            else:
                Student.moving_element.style.background = "#F00"
            document.getElementById('top').style.background = TOP_INACTIVE
        else:
            Student.moving_element.style.background = "#FFF"
            document.getElementById('top').style.background = TOP_ACTIVE
        self.draw(square_feedback=True)
    def move_student_to(self, student, column, line):
        """Move the student on a chair.
        If not an A or B version, ask for the version.
        """
        version = self.lines[line][column]
        while version not in ('a', 'b'):
            if not CHECKPOINT:
                version = 'a'
                break
            version = prompt('Version A / B:')
            if version:
                version = version.lower()
            else:
                version = student.version or 'a'
        record('/checkpoint/' + COURSE + '/' + student.login + '/'
               + self.building + ',' + column + ',' + line + ',' + version)
    def stop_move_student(self, event):
        """Drop the student"""
        pos = self.get_coord(event)
        if pos[0] != -1:
            self.move_student_to(Student.moving_student, pos[0], pos[1])
        document.body.onmousemove = document.body.ontouchmove = None
        window.onmouseup = document.body.ontouchend = None
        del Student.moving_element.style.position
        del Student.moving_element.style.background
        del Student.moving_element.style.pointerEvents
        document.getElementById('top').style.background = TOP_INACTIVE
        Student.moving_student = None
        Student.moving_element = None
        if pos[0] == -1:
            update_page()

    def zoom_student(self, login):
        "Zoom on this student"
        student = STUDENT_DICT[login]
        if student.building != ROOM.building:
            self.change(student.building)
            update_page()
            document.getElementById('buildings').value = student.building
        self.scale = self.width / 5
        self.left = self.top = 0
        left, top, _dx, _dy = self.xys(student.column, student.line)
        self.left = self.LEFT - left + (self.width - self.LEFT) / 2
        self.top = self.TOP - top + (self.height - self.TOP) / 2
        self.draw()

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
        if len(room) >= 3:
            self.building = room[0]
            self.column = int(room[1])
            self.line = int(room[2])
            self.version = room[3]
        self.checkpoint_time = data[1][3]
        self.blur = data[1][4]
        self.nr_questions_done = data[1][5] or 0
        self.client_ip = data[1][6]
        self.bonus_time = data[1][7]
        self.firstname = data[2]['fn']
        self.surname = data[2]['sn']
        self.sort_key = self.surname + '\001' + self.firstname + '\001' + self.login
        STUDENT_DICT[self.login] = self
        self.update()

    def is_good_room(self, room_name):
        """Use IP to compute if the student is in the good room"""
        if self.client_ip not in ROOM.ips: # Unknown IP
            return True
        if ROOM.building not in BUILDINGS: # Virtual room
            return True
        return ROOM.ips[self.client_ip] == ROOM.building + ',' + room_name

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

def cmp_student_name(student_a, student_b):
    """Compare 2 students names"""
    if student_a.sort_key > student_b.sort_key:
        return 1
    return -1

def cmp_student_position(student_a, student_b):
    """Compare 2 students column"""
    return student_a.column - student_b.column

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
        BODY { font-family: sans-serif}
        .name:hover { background: #FFF }
        .name SPAN { color: #888 }
        CANVAS { position: absolute; left: 0px; width: 100%; top: 0px; height: 100% }
        #waiting { display: inline }
        #top {z-index: 2; position: absolute;
              top: 0px; left: 0px; width: 12em; padding-right: 2em; height: 100vh;
              overflow-y: scroll; overflow-x: visible;
              background: ''', TOP_INACTIVE, '''}
        #top * { vertical-align: middle }
        #top .course { font-size: 150%; }
        #top SELECT { font-size: 150%; }
        #top .drag_and_drop { display: inline-block }
        #top .reload { font-family: emoji; font-size: 300%; cursor: pointer; }
        #spy { position: absolute; left: 0% ; top: 0% ; right: 0%; bottom: 0%;
               display: none; background: #FFF; opacity: 0.95; overflow: auto;
               padding: 1em; font-size: 150%; z-index: 3
             }
        #spy BUTTON { font-size: 150%; }
        #spy .source {  white-space: pre; }
        .send_alert { font-size: 200% ; display: inline-block;
                      transition: transform 0.5s; cursor: pointer }
        .send_alert:hover { transform: scale(2, 2) }
        #messages { position: fixed ; right: 0px ; bottom: 0px ;
            max-width: 40vw;
            background: #F88; opacity: 0.8;
            padding-left: 0.5em;
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
        </style>
        <div id="top">
        <span class="reload" onclick="reload_page()">⟳</span>
          
        <span class="send_alert" onclick="send_alert()">🚨</span>
          
        ''',
        '<span class="course">',
        COURSE.split('=')[1].replace(RegExp('_', 'g'), ' '),
        '</span>',
        ' <select style="width:100%" id="buildings" onchange="ROOM.change(this.value); update_page(); ROOM.draw()">',
        ''.join(['<option'
                 + (building == building_name and ' selected' or '')
                 + '>' + building.replace('empty', LOGIN) + '</option>'
                 for building in BUILDINGS_SORTED]),
        '''</select>
        <label><input id="my_rooms" onchange="ROOM.scale = 0;ROOM.draw()" type="checkbox"
               >Seulement mes salles</label>
        <label class="filter">Mettre en évidence les logins :<br>
        <input onchange="filters(this)" onblur="filters(this)" style="box-sizing: border-box; width:100%"></label>
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
        <div id="spy"></div>
        ''']
    document.body.innerHTML = ''.join(content)
    document.body.onkeydown = key_event_handler

def send_alert():
    """Sent an on map alert message to all teachers"""
    message = prompt("Message à afficher sur les plans de tous les surveillants :")
    if message:
        record('/checkpoint/MESSAGE/' + COURSE + '/' + encodeURIComponent(message))

def update_page():
    """Update students"""
    students = [Student(student) for student in STUDENTS if student[0]]
    students.sort(cmp_student_name)
    ROOM.students = []
    ROOM.waiting_students = []
    for student in students:
        if student.building == ROOM.building:
            ROOM.students.append(student)
        elif not student.active:
            ROOM.waiting_students.append(student)
    ROOM.put_students_in_rooms()
    ROOM.draw()
    ROOM.compute_rooms_on_screen()
    ROOM.update_waiting_room()
    ROOM.update_messages()
    student = window.location.hash
    if student and len(student) > 1:
        ROOM.zoom_student(student[1:])
        window.location.hash = ''

def reload_page():
    """Update data now"""
    if document.body.onmousemove is None and window.mouse_is_inside:
        record('/update/' + COURSE)


def close_exam(login):
    """Terminate the student exam"""
    record('/checkpoint/' + COURSE + '/' + login + '/STOP')
    spy_close()

def open_exam(login):
    """Open again the student exam"""
    record('/checkpoint/' + COURSE + '/' + login + '/RESTART')
    spy_close()

def spy_close():
    """Close the student source code"""
    document.getElementById('spy').style.display = 'none'


def canonize(txt):
    """Cleanup name"""
    return txt.lower().replace(RegExp('[ -_]', 'g'), '')

def get_login(student):
    """Get login from any information"""
    if not student:
        return student
    if student in STUDENT_DICT:
        return student
    if 'p' + student[1:] in STUDENT_DICT:
        return student
    possibles = []
    student = canonize(student)
    for login in STUDENT_DICT:
        verify = STUDENT_DICT[login]
        if not verify.building:
            continue
        if canonize(verify.firstname) == student or canonize(verify.surname) == student:
            possibles.append([login, verify.surname, verify.firstname])
    if len(possibles) == 1:
        return possibles[0][0]
    if len(possibles) == 0:
        return None
    choices = '\n'.join([
        str(i) + ' ' + choice[0] + ' ' + choice[1] + ' ' + choice[2]
        for i, choice in enumerate(possibles)])
    i = prompt(choices)
    if i:
        print(possibles[i][0])
        return possibles[i][0]
    return None

def key_event_handler(event):
    """The spy popup receive a keypress"""
    if event.key == 'Escape':
        spy_close()
    if event.key == 'f' and event.ctrlKey:
        spy_close();
        student = prompt("Numéro d'étudiant ou nom ou prénom à chercher")
        student = get_login(student)
        if student:
            ROOM.zoom_student(student)
        else:
            alert('Introuvable')

def spy_cursor(source):
    if not spy.sources[0]:
        return
    bar = document.getElementById('time')
    cursor = bar.lastChild
    first = spy.sources[0][0] - BEFORE_FIRST
    last = spy.sources[-1][0]
    width = last - first
    pos_x = (source[0] - first) / width * bar.offsetWidth
    if pos_x < bar.offsetWidth / 2:
        cursor.style.left = pos_x + 'px'
        cursor.style.right = 'auto'
        cursor.className = 'cursor left c' + source[2]
    else:
        cursor.style.right = bar.offsetWidth - pos_x + 'px'
        cursor.style.left = 'auto'
        cursor.className = 'cursor right c' + source[2]
    cursor.innerHTML = (
        nice_date(source[0])
        + '<br>' + {'c': 'Compile', 's': 'Sauve', 'a': 'Réussi'}[source[2]]
        + ' N° ' + (source[1] + 1)
    )

def spy_it(event=None):
    """Display the selected source"""
    if not spy.sources[0]:
        return
    bar = document.getElementById('time')
    first = spy.sources[0][0] - BEFORE_FIRST
    last = spy.sources[-1][0]
    width = last - first
    if event:
        time = first + width * (event.clientX - bar.offsetLeft) / bar.offsetWidth
        source = None # To please pylint
        last_source = None
        for source in spy.sources:
            if source[0] >= time:
                break
            last_source = source
        if last_source and source[0] - time > time - last_source[0]:
            source = last_source # Take the previous because it is nearer
        event.stopPropagation()
        event.preventDefault()
    else:
        source = spy.sources[-1]
    spy_cursor(source)
    div_source = document.getElementById('source')
    div_source.textContent = source[3]
    hljs.highlightElement(div_source)

def spy_concat(sources):
    """Display all answers concatenated"""
    done = {}
    div_source = document.getElementById('source')
    for source in sources[::-1]:
        if source[1] in done:
            continue
        done[source[1]] = True
        title = document.createElement('H1')
        title.textContent = 'Question ' + (source[1] + 1)
        div_source.appendChild(title)
        lines = document.createElement('PRE')
        lines.style.position = 'absolute'
        lines.style.left = '0px'
        lines.style.textAlign = 'right'
        lines.style.marginTop = '0px'
        lines.textContent = '\n'.join(
            [
                str(i+1)
                for i, _ in enumerate(source[3].split('\n'))
            ])
        div_source.appendChild(lines)
        code = document.createElement('PRE')
        code.textContent = source[3]
        code.style.marginLeft = "1em"
        hljs.highlightElement(code)
        div_source.appendChild(code)

def set_time_bonus(element, login):
    """Recode and update student bonus time"""
    record('/checkpoint/TIME_BONUS/' + COURSE + '/' + login + '/' + 60*int(element.value))
    element.style.background = "#DFD"
    STUDENT_DICT[login].bonus_time = element.value

def spy(sources, login, infos):
    """Display the infos source code"""
    student = STUDENT_DICT[login]
    sources.sort()
    if student.active:
        state = '<button onclick="close_exam(\'' + login + '\')">Clôturer examen</button>'
    else:
        state = '<button onclick="open_exam(\'' + login + '\')">Rouvrir examen</button>'
    if not student.good_room:
        state += ' (Adresse IP dans la mauvaise salle)'
    last_save = {}
    last_compile = {}
    grade_compile = ''
    grade_save = ''
    for source in sources:
        if source[2] == 's':
            last_save[source[1]] = source
            if not grade_save:
                grade_save = ('<button onclick="window.open(\'/grade/'
                    + COURSE + '/' + login + '/1?ticket=' + TICKET
                    + '\')">Noter sauvegarde</button>')
        elif source[2] == 'c':
            last_compile[source[1]] = source
    for question in last_compile:
        if (not last_save[question]
            or last_compile[question][0] > last_save[question][0]
                and last_compile[question][3].strip() != last_save[question][3].strip()
           ):
            grade_compile = ('<button onclick="window.open(\'/grade/'
                + COURSE + '/' + login + '/2?ticket=' + TICKET
                + '\')">Noter dernière compilation</button>')
            break

    div = document.getElementById('spy')
    content = [
        '<button onclick="spy_close()">Fermer</button> ',
        login, ' ', infos.fn, ' ', infos.sn, ' ', state,
        '(<input onchange="set_time_bonus(this,\'' + login
            + '\')" value="' + student.bonus_time/60 + '">Minutes bonus)',
        grade_save, grade_compile,
        '<div id="time" onmousedown="spy_it(event)"',
        ' onmousemove="if (event.buttons) spy_it(event)">']
    spy.sources = []
    if sources[0]:
        first = sources[0][0] - BEFORE_FIRST
        last = sources[-1][0]
        width = (last - first) or 1
        for source in sources:
            spy.sources.append(source)
            content.append(
                '<span style="left:' + 100*(source[0] - first)/width
                + '%" class="' + source[2] + '">'
                + (source[2] == 'a' and (source[1]+1) or '')
                + '</span>')
    else:
        content.append("Aucune sauvegarde n'a été faite.")
    content.append('<span class="cursor right"></span>')
    content.append('</div><pre id="source"></pre>')
    div.innerHTML = ''.join(content)
    div.style.display = 'block'
    spy_concat(sources)
    spy_cursor(spy.sources[-1])

def debug():
    """debug"""
    students_per_room = {}
    for room_name in ROOM.rooms:
        room = ROOM.rooms[room_name]
        students_per_room[room_name] = [student.login for student in room.students]
    print(JSON.stringify(students_per_room))

create_page('Nautibus')
ROOM = Room('Nautibus')
update_page()
