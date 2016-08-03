def add_mult(data, char, step):  # Str
    i = step
    data = list(data)
    while i < len(data):
        data.insert(i, char)
        i += step + 1
    return ''.join(data)


def add_single(data, char, index):
    return data[:index] + char + data[index:]


def join(data, char):  # List
    return char.join(data)


def pad(data, length, char, end=False):
    if type(data) is list:
        p_data = []
        for val in data:
            if len(val) < length:
                if not end:
                    val = char*(length - len(val)) + val
                else:
                    val = val + char*(length - len(data))
            p_data.append(val)
        data = p_data
    else:
        if len(data) < length:
            if not end:
                data = char*(length - len(data)) + data
            else:
                data = data + char*(length - len(data))
    return data


def remove_char(data, char):
    if type(data) == str:
        return data.replace(char, '')
    elif type(data) == list:
        return [val for val in data if val != char]


def split(data, char):  # Str
    return data.split(char)


def strip(data, minimum, chars=None, end=False):
    if type(data) is list:
        s_data = []
        for val in data:
            if not end:
                val = val.lstrip(chars)
            else:
                val = val.rstrip(chars)
            if len(val) == 0:
                val = minimum
            s_data.append(val)
        data = s_data
    else:
        if not end:
            data = data.lstrip(chars)
        else:
            data = data.rstrip(chars)
        if len(data) == 0:
            data = minimum
    return data


def trim(data, length, end=False):
    if not end:
        data = data[length:]
    else:
        data = data[:-length]
    return data


def sanitize(data, functions):
    for function in functions:
        data = function(data)
    return data


def intlist_to_strlist(data, fmt=None):
    return[str(val) for val in data]


def strlist_to_intlist(data):
    return [int(val) for val in data]


def to_format_str(data, fmt):
    if type(data) is list:
        data = [fmt % val for val in data]
    else:
        data = fmt % data
    return data
