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
    hljs = hljs
except ValueError:
    pass

RELOAD_INTERVAL = 60 # Number of seconds between update data
HELP_LINES = 8
LEFT = 10
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
    rooms = {}
    rooms_on_screen = {}
    width = height = 0
    waiting_students = []
    zooming = scale_start = zooming_x = zooming_y = 0
    event_x = event_y = 0
    walls = windows = doors = chars = []
    def __init__(self, building):
        self.menu = document.getElementById('top')
        self.change(building)
        window.onblur = mouse_leave
        window.onfocus = mouse_enter
        window.onresize = update_page
        setInterval(reload_page, RELOAD_INTERVAL * 1000)

        self.ips = {}
        for room_name in CONFIG.ips_per_room:
            for client_ip in CONFIG.ips_per_room[room_name].split(' '):
                if client_ip != '':
                    self.ips[client_ip] = room_name
    def xys(self, column, line):
        """Change coordinates system"""
        return [self.left + self.scale * self.columns_x[2*column],
                self.top + self.scale * self.lines_y[2*line],
                self.scale * Math.min(self.columns_x[2*column+2] - self.columns_x[2*column],
                                      self.lines_y[2*line+2] - self.lines_y[2*line])]
    def get_column_row(self, pos_x, pos_y):
        """Return character position (float) in the character map"""
        if pos_y < self.menu.offsetHeight:
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
    def change(self, building):
        """Initialise with a new building"""
        self.building = building
        self.lines = BUILDINGS[building].split('\n')
        self.x_max = max([len(line) for line in self.lines]) + 1
        self.top = self.menu.offsetHeight
        self.left = LEFT
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
            room = self.rooms[room_name]
            left, top, width, height = room.position
            right = left + width
            bottom = top + height
            room['students'] = []
            teachers = []
            for student in self.students:
                if (student.active
                        and student.column >= left and student.column <= right
                        and student.line >= top and student.line <= bottom):
                    room['students'].append(student)
                    if student.teacher not in teachers:
                        teachers.append(student.teacher)
            teachers.sort()
            room['teachers'] = ' '.join(teachers)
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
                     'w': ' ', 'd': ' ', '+': ' ', '-': ' ', '|': ' '}
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
            if (i > 1 # pylint: disable=too-many-boolean-expressions
                    and message != ''
                    and self.event_x > x_pos + size
                    and self.event_x < x_pos + size + MENU_WIDTH*size
                    and self.event_y > y_item
                    and self.event_y < y_item + MENU_LINE * size
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
            if (self.lines_height[2*student.line] < 0.5
                or self.columns_width[2*student.column] < 0.5):
                continue
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
        canvas.setAttribute('width', self.width)
        canvas.setAttribute('height', self.height)
        ctx.fillStyle = "#EEE"
        ctx.fillRect(0, 0, self.width, self.height)

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
                if self.lines_height[2*line] < 0.5:
                    # _x_pos, y_pos, size = self.xys(1, line)
                    # ctx.fillStyle = "#DDD"
                    # ctx.fillRect(0, y_pos, width, size)
                    # ctx.fillStyle = "#000"
                    continue
                if self.columns_width[2*column] < 0.5:
                    continue
                x_pos, y_pos, size = self.xys(column, line)
                ctx.fillText(char, x_pos - char_size.width/2, y_pos + size/2)
    def draw_square_feedback(self, ctx):
        """Single square feedback"""
        column, line = self.get_column_row(self.event_x, self.event_y)
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
    def draw_teachers(self, ctx):
        """Display teacher names in front of rooms"""
        size = self.scale * 0.6
        ctx.font = size + "px sans-serif"
        for room_name in self.rooms:
            room = self.rooms[room_name]
            if room['teachers']:
                column, line = room['label']
                if (self.lines_height[2*line] < 0.5
                    or self.columns_width[2*column] < 0.5):
                    continue
                x_pos, y_pos, _size = self.xys(column, line)
                ctx.fillText(room['teachers'], x_pos, y_pos + self.scale/3)
    def draw(self, square_feedback=False):
        """Display on canvas"""
        #start = Date().getTime()
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
                (self.width - LEFT) / self.columns_x[2 * self.x_max - 1],
                (self.height - self.menu.offsetHeight) / self.lines_y[2 * len(self.lines) - 1 - HELP_LINES])
            self.top = self.menu.offsetHeight + HELP_LINES * self.scale
            self.left = LEFT
        ctx = canvas.getContext("2d")
        self.draw_map(ctx, canvas)
        ctx.font = self.scale/2 + "px sans-serif"
        self.draw_students(ctx)
        self.draw_teachers(ctx)
        messages = self.draw_computer_problems(ctx)
        if self.selected_computer and self.selected_computer[0] == self.building:
            self.draw_computer_menu(ctx, messages)
        if square_feedback:
            self.draw_square_feedback(ctx)
        self.draw_help(ctx)
        #print(Date().getTime() - start)
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
                document.getElementById('top').style.background = TOP_INACTIVE
            else:
                document.getElementById('top').style.background = TOP_ACTIVE
        self.draw()
    def drag_stop_student(self, column, line):
        """Stop moving a student"""
        if column != -1:
            if self.moving.column_start != column or self.moving.line_start != line:
                record('/checkpoint/' + COURSE + '/' + self.moving.login + '/'
                       + ROOM.building + ',' + column + ',' + line)
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
    def drag_stop_click_on_room(self, event, column, line):
        """Click on a room to zoom"""
        if (column != -1
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
            right, bottom, _size = self.xys(left + width, top + height)
            left, top, _size = self.xys(left, top)
            if left > 0 and top > 0 and right < self.width and bottom < self.height:
                self.rooms_on_screen[room_name] = True
    def update_waiting_room(self):
        """Update HTML with the current waiting student for the rooms on screen"""
        content = []
        for student in self.waiting_students:
            if student.room == '':
                room = self.ips[student.client_ip]
                if room:
                    building, room_name = room.split(',')
                    if building != self.building:
                        continue
                    if not self.rooms_on_screen[room_name]:
                        continue
                content.append(student.box())
        document.getElementById('waiting').innerHTML = ' '.join(content)
    def start_move_student(self, event):
        """Move student bloc"""
        login = event.currentTarget.getAttribute('login')
        Student.moving_student = STUDENT_DICT[login]
        Student.moving_element = event.currentTarget
        Student.moving_element.style.position = 'absolute'
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
            Student.moving_element.style.background = "#0F0"
            document.getElementById('top').style.background = TOP_INACTIVE
        else:
            Student.moving_element.style.background = "#FFF"
            document.getElementById('top').style.background = TOP_ACTIVE
        self.draw(square_feedback=True)
    def stop_move_student(self, event):
        """Drop the student"""
        pos = self.get_coord(event)
        if pos[0] != -1:
            record('/checkpoint/' + COURSE + '/' + Student.moving_student.login + '/'
                   + self.building + ',' + pos[0] + ',' + pos[1])

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
        self.client_ip = data[1][6]
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
            '<div class="name" onmousedown="ROOM.start_move_student(event)"',
            ' ontouchstart="ROOM.start_move_student(event)" login="',
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

def create_page(building_name):
    """Fill the page content"""
    content = [
        '''<style>
        .name, LABEL { display: inline-block; background: #EEE; vertical-align: top;
            cursor: pointer; user-select: none;
        }
        BODY { font-family: sans-serif }
        .name:hover { background: #FFF }
        .name SPAN { color: #888 }
        CANVAS { position: absolute; left: 0px; width: 100%; top: 0px; height: 100% }
        #waiting { display: inline }
        #top {z-index: 2; position: absolute;
              top: 0px; left: 0px; width: 100%; height: 5em;
              background: ''', TOP_INACTIVE, '''}
        #top * { vertical-align: middle }
        #top .course { font-size: 200%; }
        #top SELECT { font-size: 150%; }
        #top .drag_and_drop { display: inline-block }
        #top .reload { font-family: emoji; font-size: 300%; cursor: pointer; }
        #spy { position: absolute; left: 0% ; top: 0% ; right: 0%; bottom: 0%;
               display: none; background: #FFF; opacity: 0.95; overflow: auto;
               padding: 1em; font-size: 150%; z-index: 3
             }
        #spy BUTTON { font-size: 150%; }
        #spy .source {  white-space: pre; }
        </style>
        <div id="top"><span class="reload" onclick="reload_page()">⟳</span>''',

        '<span class="course">', COURSE, '</span>',
        ' <select onchange="ROOM.change(this.value); update_page(); ROOM.draw()">',
        ''.join(['<option'
                 + (building == building_name and ' selected' or '')
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
            ontouchstart="ROOM.drag_start(event)"
        ></canvas>
        <div id="spy"></div>
        ''']
    document.body.innerHTML = ''.join(content)

def update_page():
    """Update students"""
    students = [Student(student) for student in STUDENTS if student[0]]
    students.sort(cmp_student)
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

def spy(text, login, infos):
    """Display the infos source code"""
    student = STUDENT_DICT[login]
    if student.active:
        state = '<button onclick="close_exam(\'' + login + '\')">Clôturer examen</button>'
    else:
        state = '<button onclick="open_exam(\'' + login + '\')">Rouvrir examen</button>'
    div = document.getElementById('spy')
    div.innerHTML = (
        '<button onclick="spy_close()">Fermer</button> '
        + login + ' ' + infos.fn + ' ' + infos.sn + ' ' + state
        + '<pre></pre>')
    div.style.display = 'block'
    div.lastChild.textContent = text
    hljs.highlightElement(div.lastChild)


create_page('Nautibus')
ROOM = Room('Nautibus')
update_page()
