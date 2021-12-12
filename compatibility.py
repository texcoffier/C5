# pylint: disable=invalid-name,too-many-arguments,too-many-instance-attributes,self-assigning-variable

"""
To be Python compatible
"""

Object = Object # pylint: disable=undefined-variable
Array = Array # pylint: disable=undefined-variable

def str(txt): # pylint: disable=redefined-builtin
    """Python like"""
    return txt.toString()
def bind(fct, _obj):
    """Bind the function to the object: nothing to do in Python"""
    return fct
Object.defineProperty(Array.prototype, 'append',
                      {'enumerable': False, 'value': Array.prototype.push})