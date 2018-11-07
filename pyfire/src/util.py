import datetime


def default_json_serializer(o):
    if isinstance(o, set):
        return list(o)
    if isinstance(o, datetime.datetime):
        return str(o)
    return o.__dict__

def object_to_json(o, types=[int,float,list,str]):
    class_json = o.__dict__ 
    final_json = {}
    for key, value in class_json.items():
        if True in [True for x in types if isinstance(value, x)]:
            final_json[key] = value
    return final_json

def get_current_datetime():
    return str(datetime.datetime.now())
