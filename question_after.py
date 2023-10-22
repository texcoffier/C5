
"""
Helper to create 'COMPILE_.../session.json' file containing questionnary information.
"""
import json

infos = []
for classe in question_classes: # pylint: disable=undefined-variable
    infos.append({'title': classe.__doc__ or ''})

infos[0]['options'] = options = {}
for key, value in Session.default_options.items():
    options[key] = value
try:
    for key, value in COURSE_OPTIONS.items():
        if value == False:
            value = 0
        elif value == True:
            value = 1
        options[key] = value
except NameError:
    pass

print(json.dumps(infos))
