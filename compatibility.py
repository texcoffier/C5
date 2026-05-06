# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To be Python compatible
"""

def str(txt): # pylint: disable=redefined-builtin
    """Python like"""
    return txt.toString()
Object.defineProperty(Array.prototype, 'append',
                      {'enumerable': False, 'value': Array.prototype.push})
Object.defineProperty(Array.prototype, 'index',
                      {'enumerable': False, 'value': Array.prototype.indexOf})
def dict_values():
    """Dicts values"""
    THIS = eval('this') # pylint: disable=eval-used
    return [THIS[i] for i in THIS] # pylint: disable=undefined-variable
Object.defineProperty(Object.prototype, 'Values',
                      {'enumerable': False, 'value': dict_values})
def dict_items():
    """Dict items"""
    THIS = eval('this') # pylint: disable=eval-used
    return [[i, THIS[i]] for i in THIS] # pylint: disable=undefined-variable
DIGITS = RegExp('^[0-9]+$')
def isdigit():
    """Compatible with Python"""
    return eval('this').match(DIGITS)
Object.defineProperty(Object.prototype, 'Items',
                      {'enumerable': False, 'value': dict_items})
Object.defineProperty(String.prototype, 'lower',
                      {'enumerable': False, 'value': String.prototype.toLowerCase})
Object.defineProperty(String.prototype, 'upper',
                      {'enumerable': False, 'value': String.prototype.toUpperCase})
Object.defineProperty(String.prototype, 'isdigit',
                      {'enumerable': False, 'value': isdigit})
String.prototype.strip = String.prototype.trim

def title():
    """Nearly compatible with Python"""
    uppercased = ''
    first = True
    for i in eval('this'):
        lower = i.lower()
        upper = i.upper()
        if lower == upper:
            # Not alphabetic
            first = True
            uppercased += i
        elif first:
            uppercased += upper
            first = False
        else:
            uppercased += lower
    return uppercased
Object.defineProperty(String.prototype, 'title',
                      {'enumerable': False, 'value': title})

def rjust(nr):
    """Compatible with Python"""
    THIS = eval('this')
    return ('                       '+THIS)[-nr:]
Object.defineProperty(String.prototype, 'rjust',
                      {'enumerable': False, 'value': rjust})

def startswith(txt):
    """Only if txt is a string"""
    return this.substr(0, txt.length) == txt # pylint: disable=undefined-variable
Object.defineProperty(String.prototype, 'startswith',
                      {'enumerable': False, 'value': startswith})
def millisecs():
    """Current time in milli seconds"""
    return Date().getTime()

def join(table):
    """Python join"""
    return table.join(this) # pylint: disable=undefined-variable
Object.defineProperty(String.prototype, 'join',
                      {'enumerable': False, 'value': join})

def html(txt):
    """Escape < > &"""
    return str(txt).replace(RegExp('&', 'g'), '&amp;'
                           ).replace(RegExp('<', 'g'), '&lt;'
                                    ).replace(RegExp('>', 'g'), '&gt;')

def record_error():
    """onerror event handler"""
    alert("Une erreur de sauvegarde s'est produite.\nRechargez la page et recommencez")

def record(action):
    """Do an action and get data"""
    script = document.createElement('SCRIPT')
    script.src = BASE + '/' + action + '?ticket=' + TICKET
    try:
        script.onload = update_page
        script.onerror = record_error
    except: # pylint: disable=bare-except
        # There is no update_page for the student interface
        pass
    document.body.append(script)

def two_digit(number):
    """ 6 → 06 """
    return ('0' + str(int(number)))[-2:]

def nice_date(seconds, sec=False):
    """Returns a string from seconds"""
    js_date = Date()
    js_date.setTime(seconds*1000)
    return (js_date.getFullYear()
            + '-' + two_digit(js_date.getMonth() + 1)
            + '-' + two_digit(js_date.getDate())
            + ' ' + two_digit(js_date.getHours())
            + ':' + two_digit(js_date.getMinutes())
            + (sec and ':' + two_digit(js_date.getSeconds()) or '')
           )

def hhmmss(seconds):
    """Returns a string from seconds"""
    js_date = Date()
    js_date.setTime(seconds*1000)
    return two_digit(js_date.getHours()) + ':' + two_digit(js_date.getMinutes()) + ':' + two_digit(js_date.getSeconds()) 

def strptime(yyyymmddhhmmss):
    """Parse start/stop date"""
    js_date = Date(
        yyyymmddhhmmss[:4],
        yyyymmddhhmmss[5:7] - 1,
        yyyymmddhhmmss[8:10],
        yyyymmddhhmmss[11:13],
        yyyymmddhhmmss[14:16],
        yyyymmddhhmmss[17:19])
    return js_date.getTime() / 1000.

def max(*items): # pylint: disable=redefined-builtin)
    """Emulate Python max"""
    return Math.max.apply(None, items)

def list(items): # pylint: disable=redefined-builtin)
    """Emulate Python list"""
    return [i for i in items] # pylint: disable=unnecessary-comprehension

def is_int(obj):
    """True is it is a number"""
    return obj.toFixed

def post(url, value, iframe=False):
    """POST a value"""
    form = document.createElement("form")
    form.setAttribute("method", "post")
    form.setAttribute("action", url)
    form.setAttribute("enctype", "multipart/form-data")
    form.setAttribute("encoding", "multipart/form-data") # For IE
    data = document.createElement("input")
    data.setAttribute("type", "hidden")
    data.setAttribute("name", "value")
    data.setAttribute("value", value)
    form.appendChild(data)
    if iframe:
        iframe = document.createElement("iframe")
        iframe.style.border = '0px'
        form.target = iframe.name = 'post_iframe_' + millisecs()
        form.appendChild(iframe)
    document.body.appendChild(form)
    form.submit()
    #def remove_form(event):
    #    print(event)
    #form.onload = remove_form

inf = Infinity

@external
class Grades:
    pass

def init_minimal_worker(notation_a, notation_b, hook):
    """Return the worker.
            worker.notation_a
            worker.notation_b
    """
    def init_worker(worker, version):
        worker.postMessage(['reset'])
        worker.postMessage(['config',
            {
                'WHERE': [0, "", ",,," + version, 0, 0, 0, "", 0, [0, 0, 0, 0], 0, 0, 0, ""],
                'ANSWERS': [],
            }])
    def onmessage(event):
        if event.data[0] == 'grading_ladder':
            worker._notation.append(event.data[1])
        elif event.data[0] == 'allow_edit' and event.data[1] == "1":
            if not hasattr(worker, 'notation_a'):
                worker.notation_a_list = worker._notation
                worker.notation_a = Grades(worker._notation)
                worker._notation = [['', notation_b]]
                init_worker(worker, 'b')
            else:
                worker.notation_b_list = worker._notation
                worker.notation_b = Grades(worker._notation)
                worker.notation = {
                    'a':  worker.notation_a,
                    'b':  worker.notation_b,
                }
                hook()
    def onerror(event):
        print(event)
    worker_url = BASE + '/' + COURSE + "?ticket=" + TICKET
    worker_url += '&login=' + LOGIN
    worker = eval('new Worker(worker_url)') # pylint: disable=eval-used
    worker._notation = [['', notation_a]]
    worker.onmessage = onmessage
    worker.onmessageerror = onerror
    worker.onerror = onerror
    init_worker(worker, 'a')
    return worker

class Positions:
    """Manage the position and color of screen blocs"""
    def __init__(self, blocs):
        """blocs :
             { "bloc_name": [X, DX, Y, DY, COLOR], ... }
           The dictionnary content may be modified in the future.
        """
        self.blocs = blocs
    def move(self, xy, old_pos, new_pos):
        """
        xy = 0 : move_pos
        xy = 2 : move y
        """
        if old_pos == new_pos:
            return
        for bloc in self.blocs.Values():
            if bloc[xy] == old_pos:
                bloc[xy+1] += old_pos - new_pos
                bloc[xy] = new_pos
            elif bloc[xy] + bloc[xy+1] == old_pos:
                bloc[xy+1] += new_pos - old_pos
    def update(self, bloc_name, new_bloc):
        old_bloc = self.blocs[bloc_name]
        self.move(0, old_bloc[0], new_bloc[0])
        self.move(0, old_bloc[0]+old_bloc[1], new_bloc[0]+new_bloc[1])
        self.move(2, old_bloc[2], new_bloc[2])
        self.move(2, old_bloc[2]+old_bloc[3], new_bloc[2]+new_bloc[3])
    def set_width(self, bloc_name, width):
        new_bloc = self.blocs[bloc_name][:]
        if new_bloc[0] + new_bloc[1] == 100:
            new_bloc[0] -= width - new_bloc[1]
        new_bloc[1] = width
        self.update(bloc_name, new_bloc)
    def draw(self, canvas):
        canvas.width = canvas.offsetWidth
        canvas.height = canvas.offsetHeight
        ctx = canvas.getContext('2d')
        width = canvas.width
        height = canvas.height
        dx = width / 100
        dy = height / 100
        ctx.fillStyle = '#000'
        ctx.fillRect(0, 0, width, height)
        for key, bloc in self.blocs.Items():
            ctx.fillStyle = bloc[4]
            ctx.fillRect(bloc[0]*dx, bloc[2]*dy, bloc[1]*dx, bloc[3]*dy)
        ctx.strokeStyle = '#0004'
        ctx.fillStyle = '#000'
        ctx.lineWidth = 1
        for key, bloc in self.blocs.Items():
            x1 = bloc[0] * dx
            y1 = bloc[2] * dy
            x2 = (bloc[0] + bloc[1]) * dx
            y2 = (bloc[2] + bloc[3]) * dy
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.closePath(); ctx.stroke()
            ctx.beginPath(); ctx.moveTo(x1, y2); ctx.lineTo(x2, y1); ctx.closePath(); ctx.stroke()
            box = ctx.measureText(key)
            ctx.fillText(key, (bloc[0] + bloc[1]/2)*dx - box.width/2,
                              bloc[2]*dy + box.fontBoundingBoxAscent+box.fontBoundingBoxDescent)
        ctx.fillStyle = '#F004'
        for b1 in self.blocs.Values():
            for b2 in self.blocs.Values():
                if b1 is not b2:
                    minx = max(b1[0], b2[0])
                    maxx = min(b1[0]+b1[1], b2[0]+b2[1])
                    miny = max(b1[2], b2[2])
                    maxy = min(b1[2]+b1[3], b2[2]+b2[3])
                    if minx < maxx and miny < maxy:
                        ctx.fillRect(minx*dx, miny*dy, (maxx - minx)*dx, (maxy - miny)*dy)

def positions_regtest():
    a = [2, 2, 2, 2]
    b = [0, 2, 0, 4]
    c = [2, 4, 0, 2]
    d = [4, 2, 2, 4]
    e = [0, 4, 4, 2]
    p = Positions({'a': a, 'b': b, 'c': c, 'd': d, 'e': e})
    p.update('a', [1, 4, 1, 4])
    if (a != [1, 4, 1, 4]
        or b != [0, 1, 0, 5]
        or c != [1, 5, 0, 1]
        or d != [5, 1, 1, 5]
        or e != [0, 5, 5, 1]
    ):
        print(p.blocs)
        alert('BUG Position')

positions_regtest()