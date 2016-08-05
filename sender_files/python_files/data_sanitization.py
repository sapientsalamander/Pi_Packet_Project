def add_mult(data, char, step):  # Str
    print data
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
    if len(data) < length:
        if not end:
            data = char*(length - len(data)) + data
        else:
            data = data + char*(length - len(data))
    return data


def remove_char(data, char):
    return data.replace(char, '')


def split(data, char):  # Str
    return data.split(char)


def strip(data, minimum, chars=None, end=False):
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
