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
String.prototype.strip = String.prototype.trim
def startswith(txt):
    """Only if txt is a string"""
    return this.substr(0, txt.length) == txt # pylint: disable=undefined-variable
Object.defineProperty(String.prototype, 'startswith',
                      {'enumerable': False, 'value': startswith})
def millisecs():
    """Current time in milli seconds"""
    return Date().getTime()
