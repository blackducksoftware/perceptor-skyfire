import datetime


def default_json_serializer(o):
    if isinstance(o, set):
        return list(o)
    if isinstance(o, datetime.datetime):
        return str(o)
    return o.__dict__

def get_current_datetime():
    return str(datetime.datetime.now())
