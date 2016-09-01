"""Functions for converting data to the proper format.

The LCD input class requires leading zeros and a particular format for certain
fields to use default values. Scapy requires no leading zeros, a more standard
format, and that most values be represented as integers rather than strings. In
combination with casts, these functions are used to convert from one format to
the other. Several are wrappers for basic string operations so that they are
callable with the string as an argument.

add_mult: insert a character in between every n characters.
add_single: insert a single character.
join: join a list with the specified character.
pad: add x character to a string to bring it up to length n.
remove_char: remove all instances of x character in a string.
split: split the string at a specified character.
strip: strip characters from an end of a string with a minimum value if needed.
trim: remove n characters from the beginning or end of a string.
sanitize: call the list of sanitization functions on the data.
"""


def add_mult(data, char, step):
    """Insert char between every step characters in data.

    Args:
        data (str): the string to operate on
        char (str): the character to insert
        step (int): the interval between inserted characters.

    Returns:
        str: the data with inserted characters.
    """
    i = step
    data = list(data)
    while i < len(data):
        data.insert(i, char)
        i += step + 1
    return ''.join(data)


def add_single(data, char, index):
    """Insert a single instance of a character into a string.

    Args:
        data (str): the string to operate on
        char (str): the character to insert

    Returns:
        str: the data with inserted character.
    """
    return data[:index] + char + data[index:]


def join(data, char):
    """Join a list with char in between.

    Args:
        data (list): the list to operate on
        char (str): the character to join the list with

    Returns:
        str: the joined list
    """
    return char.join(data)


def pad(data, length, char, end=False):
    """Pad a string to length with the given character.

    Adds the given character if the string is too short. If it is longer than
    specified, return the provided string.

    Args:
        data (str): the string to operate on
        length (int): the desired length
        char (str): the character to pad with
        end (boolean): the end to add the pad character to. Default is left.

    Returns:
        str: the data, padded to length.
    """
    if not end:
        data = char*(length - len(data)) + data
    else:
        data = data + char*(length - len(data))
    return data


def remove_char(data, char):
    """Removes all occurrences of char in data."""
    return data.replace(char, '')


def split(data, char):
    """Splits data at char."""
    return data.split(char)


def strip(data, minimum, chars=None, end=False):
    """Removes the given characters from an end of data. Default whitespace.

    Args:
        data (str): the string to operate on
        minimum (str): the string to use if strip removes all contents.
        chars (str): the characters to remove
        end (boolean): the end to strip from. Default is left.
    """

    if not end:
        data = data.lstrip(chars)
    else:
        data = data.rstrip(chars)
    if len(data) == 0:
        data = minimum
    return data


def trim(data, length, end=False):
    """Removes characters from an end of the string. Default is left."""
    if not end:
        data = data[length:]
    else:
        data = data[:-length]
    return data


def sanitize(data, functions):
    """Calls the provided list of functions on data in order.

    Args:
        data (str): the string to operate on
        functions (list): a list of partial functions. The only parameter not
        provided should be data.

    Returns:
        data, in whatever format it was left by the last function called. That
        should be a string, but sanitize does not force it.
    """
    for function in functions:
        data = function(data)
    return data
