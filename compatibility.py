# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To be Python compatible
"""

Object = Object # pylint: disable=undefined-variable
Array = Array # pylint: disable=undefined-variable
String = String # pylint: disable=undefined-variable
Date = Date # pylint: disable=undefined-variable

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

def record(action):
    """Do an action and get data"""
    script = document.createElement('SCRIPT')
    script.src = action + '?ticket=' + TICKET
    try:
        script.onload = update_page
    except: # pylint: disable=bare-except
        # There is no update_page for the student interface
        pass
    document.body.append(script)
