
"""
Helper to create 'COMPILE_.../session.json' file containing questionnary information.
"""
import json

infos = []
for classe in question_classes: # pylint: disable=undefined-variable
    infos.append({'title': classe.__doc__ or ''})

infos[0]['options'] = options = {}
try:
    for key, value in COURSE_OPTIONS.items():
        options[key] = value
except NameError:
    pass

print(json.dumps(infos))
