
import json

infos = []
for classe in question_classes:
    infos.append({'title': classe.__doc__ or ''})
print(json.dumps(infos))
