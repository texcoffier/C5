
"""
Helper to create 'COMPILE_.../session.json' file containing questionnary information.
"""
import json

infos = []
for classe in question_classes: # pylint: disable=undefined-variable
    infos.append({'title': classe.__doc__ or ''})
print(json.dumps(infos))
