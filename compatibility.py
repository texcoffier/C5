# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To be Python compatible
"""
Object = Object # pylint: disable=undefined-variable
Array = Array # pylint: disable=undefined-variable
String = String # pylint: disable=undefined-variable
Date = Date # pylint: disable=undefined-variable
alert = alert # pylint: disable=undefined-variable
document = document # pylint: disable=undefined-variable
TICKET = TICKET # pylint: disable=undefined-variable
update_page = update_page # pylint: disable=undefined-variable
JSON = JSON # pylint: disable=undefined-variable
Math = Math # pylint: disable=undefined-variable

def str(txt): # pylint: disable=redefined-builtin
    """Python like"""
    return txt.toString()
def bind(fct, _obj):
    """Bind the function to the object: nothing to do in Python"""
    return fct
Object.defineProperty(Array.prototype, 'append',
                      {'enumerable': False, 'value': Array.prototype.push})
Object.defineProperty(String.prototype, 'lower',
                      {'enumerable': False, 'value': String.prototype.toLowerCase})
Object.defineProperty(String.prototype, 'upper',
                      {'enumerable': False, 'value': String.prototype.toUpperCase})
String.prototype.strip = String.prototype.trim
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
    # pylint: disable=undefined-variable
    return txt.replace(RegExp('&', 'g'), '&amp;'
                      ).replace(RegExp('<', 'g'), '&lt;'
                               ).replace(RegExp('>', 'g'), '&gt;')

def record_error():
    """onerror event handler"""
    alert("Une erreur de sauvegarde s'est produite.\nRechargez la page et recommencez")

def record(action):
    """Do an action and get data"""
    script = document.createElement('SCRIPT')
    script.src = action + '?ticket=' + TICKET
    try:
        script.onload = update_page
        script.onerror = record_error
    except: # pylint: disable=bare-except
        # There is no update_page for the student interface
        pass
    document.body.append(script)

def parse_grading(history):
    """Get grading dictionary from text history"""
    grading = {}
    if not history:
        return grading
    d = Date()
    for line in history.split('\n'):
        if line:
            line = JSON.parse(line)
            d.setTime(line[0]*1000)
            grading[line[2]] = [line[3], d + '\n' + line[1]]
    return grading

def two_digit(number):
    """ 6 → 06 """
    return ('0' + str(int(number)))[-2:]

def nice_date(seconds):
    """Returns a string from seconds"""
    js_date = Date()
    js_date.setTime(seconds*1000)
    return (js_date.getFullYear()
            + '-' + two_digit(js_date.getMonth() + 1)
            + '-' + two_digit(js_date.getDate())
            + ' ' + two_digit(js_date.getHours())
            + ':' + two_digit(js_date.getMinutes())
           )

def max(*items): # pylint: disable=redefined-builtin)
    """Emulate Python max"""
    return Math.max.apply(None, items)
