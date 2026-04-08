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
