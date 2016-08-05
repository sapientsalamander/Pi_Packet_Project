#!/usr/bin/env python

import time
from enum import Enum
from Adafruit_CharLCD import *

"""LCD Input Wrapper.

A wrapper around the Adafruit LCD library. This extends the functionality to
allow for easy and generic input that can be reused.

Example:
    lcd = LCD_Input_Wrapper()
    mac_address = lcd.get_input('%h%h:%h%h:%h%h:%h%h:%h%h:%h%h')
    ip_address = lcd.get_input('%i%i%i.%i%i%i.%i%i%i.%i%i%i')

    Any non-input characters are displayed literally, ex.
    random = lcd.get_input('%i%h-%i%i hello %h%h. %i')
    will shot up as '00-00 hello 00. 0' on the screen.
"""

# TODO: Remove Value_Types, and find a better way to represent the idea
# behind it (to hold the enum, format specifier, and values an Input_Char
# can hold.


class LCD_Input_Wrapper(Adafruit_CharLCDPlate):

    # An enum to represent the different values that you can be prompted for.
    # Note, Char is used to represent a static value that won't change, only
    # used for UI purposes, to make things look better.
    Input_Type = Enum('Input_Type', 'Char Int Hex', start=0)

    # An extendable tuple, one for each type of input we want. See above for
    # examples.
    # For each tuple withing Value_Types, here's what they represent:
    # Input_Type.___: An enum for the type of input.
    # 'char': The formatter that is passed when doing get_input('%char')
    # 'string': The value that a type can hold. TODO: The current default
    #   is hardcoded to '0', but make it the first char of this list.
    Value_Types = ((Input_Type.Int.value, 'i', '0123456789'),
                   (Input_Type.Hex.value, 'h', '0123456789abcdef'))

    class Input_Char(object):
        """Holds the type and value of an input character.

        Each character shown on the screen is represented by this class.

        Attributes:
            value (str): The representation of a character.
            value_type (int): The type of character this is, ex. int or hex
        """
        value = ' '
        value_type = 0

    def get_value_tuple(self, key):
        """Basically taking Value_Types and letting it act as a dictionary.

        Args:
            key (enum): The key you want to look for in the Value_Types.

        Returns:
            tuple (int, string, string): Returns the tuple in Value_Types
                that contains the key passed in.
        """
        for i in self.Value_Types:
            if key in i:
                return i
        return None

    def _inc_or_dec(self, value, value_type, delta):
        """A looping increase or decrease for Value_Types.

        Args:
            value (str): The value to be increased or decreased.
            value_type (int): The type of the value. See Value_Types.
            delta (int): The amount to increase or decrease by.

        Returns:
            str: The value at value + delta, with looping semantics.

        TODO: Separate this function from Value_Type.
        """
        values_array = self.get_value_tuple(value_type)[2]
        index = (values_array.index(value) + delta) % len(values_array)
        return values_array[index]

    def increment(self, value):
        """Wrapper function, calls _inc_or_dec with appropriate values.

        Args:
            value (Input_Char): The value to be incremented.

        Returns:
            str: The value of value + 1, with looping semantics.

        TODO: Increment by more than 1?
        """
        return self._inc_or_dec(value.value, value.value_type, 1)

    def decrement(self, value):
        """Wrapper function, calls _inc_or_dec with appropriate values.

        Args:
            value (Input_Char): The value to be decremented.

        Returns:
            str: The value of value - 1, with looping semantics.

        TODO: Decrement by more than 1?
        """
        return self._inc_or_dec(value.value, value.value_type, -1)

    def parse_identifier(self, input_format):
        """Takes an identifier (ex. 'i' or 'h') deals with it appropriately.

        Args:
            input_format (str): The format to deal with.

        Returns:
            tuple (int, enum): First element is how much to advance the input
                by, (for a theoretical multichar format, ex. %ll. Second is
                the type of the input.

        TODO: Clean up once Value_Types is a dictionary, and get rid of the
            hard-coded advance value of 2. Also, make it able to take
            multichar identifiers.
        """
        char_type = self.Input_Char()
        advances = 0
        try:
            char_type.value_type = self.get_value_tuple(input_format[1])[0]
            # TODO: Make default configurable (first in Input_Char string).
            char_type.value = '0'
        except (TypeError):
            print 'Cannot parse format; unknown identifier after "%"'
            char_type.value_type = self.Input_Type.Char
            char_type.value = input_format[0]
        return (2, char_type)

    def parse_char(self, input_format):
        """Parse a char, and determine if it's supposed to be an input.

        Args:
            input_format (str): A single char.

        Returns:
            tuple (int, enum): First element is how much to advance the input
                by, (for a theoretical multichar format, ex. %ll. Second is
                the type of the input.
        """
        char_type = self.Input_Char()
        advances = 0
        if input_format[0] == '%':
            advances, char_type = self.parse_identifier(input_format)
        else:
            char_type.value_type = self.Input_Type.Char
            char_type.value = input_format[0]
            advances = 1
        return (advances, char_type)

    def _find_input(self, list_chars, index, delta):
        """Find the next/previous input char, with looping semantics.

        Used for the left and right buttons. When you click right, the screen
        doesn't advance to the next character, it advances to the next
        character which requires input.

        Args:
            list_chars ([Input_Char]): List of input chars to look in.
            index (int): The index to start looking from.
            delta (int): How much to jump in between each look (used for -1
                or 1, so we can look forwards and backwards.

        Returns:
            int: The index of the next/previous input char. If there is none,
                it just returns index.
        """
        for i in list_chars[(index+delta) % len(list_chars)::delta]:
            if i.value_type != self.Input_Type.Char:
                return list_chars.index(i)
        # When you go forwards, and reach the end, it doesn't wrap around to
        # the beginning. But when you go backwards and reach the beginning, it
        # does wrap to the end. So this is for the case that you go forwards
        # and don't find an input, wrap around the end beginning, and start
        # looking forward again.
        return self._find_input(list_chars, len(list_chars), delta)

    def find_previous_input(self, list_chars, index):
        """Wrapper function, calls _find_input with appropriate values.

        Args:
            list_chars ([Input_Char]): List of input chars to look in.
            index (int): Index to start the search from.

        Returns:
            int: Index of previous input.
        """
        return self._find_input(list_chars, index, -1)

    def find_next_input(self, list_chars, index):
        """Wrapper function, calls _find_input with appropriate values.

        Args:
            list_chars ([Input_Char]): List of input chars to look in.
            index (int): Index to start the search from.

        Returns:
            int: Index of next input.
        """
        return self._find_input(list_chars, index, 1)

    def find_newline(self, list_chars):
        """Finds a newline, to be used for the second line of the LCD.

        Args:
            list_chars ([Input_Char]): List of chars to look in.

        Returns:
            int: Index of the newline, or -1 if there is none.
        """
        index_newline = -1
        for i in xrange(len(list_chars)):
            if list_chars[i].value == '\n':
                index_newline = i
        return index_newline

    def set_cursor_index(self, index_newline, index):
        """Sets the cursor at a certain index.

        index_newline acts as a kind of new line separator. It tells
        us where the split in the string might be, so we can put the
        cursor on the second line if necessary.

        Args:
            index_newline (int): The position of the newline char, if
                present, or -1 if not present.
            index (int): The index of the char to set the cursor at. Starts
                at the beginning of the string, not from the newline.

        Returns:
            tuple (int, int): Returns the cursor_index, which starts from the
                beginning of the current row, and the row the cursor is on.

        TODO: This function should not even exist. Clean up logic behind
            where we call it, and remove this function.
        """
        cursor_index = index
        if index_newline != -1 and index >= index_newline:
            cursor_index -= index_newline + 1
            row = 1
        elif index_newline != -1:
            row = 0
        return (cursor_index, row)

    def use_default(self, list_chars, default):
        """A function to set the initial values of the Input Chars.

        In theory, to be used for setting ex. default MAC addresses, because
        those things are a pain to type out using the screen interface.

        Args:
            list_chars ([Input_Char]): List of input chars to set defaults for.
            default (str): The defaults for each of the list chars.

        Returns:
            ([Input_Char]): list_chars, but values modified to reflect
                initialized values.

        TODO: Clean this up somehow."""
        i = 0
        cur_default = 0
        while i < len(list_chars):
            cur_value_type = list_chars[i].value_type
            try:
                index = [val[0] for val
                         in self.Value_Types].index(cur_value_type)
                if default[cur_default] in self.Value_Types[index][2]:
                    list_chars[i].value = default[cur_default]
                    i += 1
                cur_default += 1
            except (ValueError):
                i += 1
        return list_chars

    def modify_chars(self, list_chars, index):
        """Gets input from user, and acts accordingly.

        Args:
            list_chars ([Input_Char]): List of chars to work on and display.
            index: The index to start out. TODO: This index is used for
                starting the cursor on a field that actually requires
                input, and not a static/const field, but rework function
                so it doesn't take this index as an argument.

        Returns:
            list_chars ([Input_Char]): The user modified chars.

        TODO: Rename function."""
        index_newline = self.find_newline(list_chars)
        cursor_index, row = self.set_cursor_index(index_newline, index)
        self.display_list_chars_cursor(list_chars, cursor_index, row)
        while True:
            time.sleep(0.15)
            if self.is_pressed(UP):
                list_chars[index].value = self.increment(list_chars[index])
            elif self.is_pressed(DOWN):
                list_chars[index].value = self.decrement(list_chars[index])
            elif self.is_pressed(LEFT):
                index = self.find_previous_input(list_chars, index)
            elif self.is_pressed(RIGHT):
                index = self.find_next_input(list_chars, index)
            elif self.is_pressed(SELECT):
                break
            else:
                continue
            cursor_index, row = self.set_cursor_index(index_newline, index)
            self.display_list_chars_cursor(list_chars, cursor_index, row)
        return list_chars

    def display_list_chars_cursor(self, list_chars, cursor_index, row):
        """Takes an array of Input_Char and displays their values on screen.

        Args:
            list_chars ([Input_Char]): List of chars to display.
            cursor_index (int): Index on the current line to set cursor at.
            row (int): Row to set the cursor at.
        """
        self.clear()
        self.message(''.join([x.value for x in list_chars]))
        self.set_cursor(cursor_index, row)

    def get_input(self, prompt, default=None):
        """Wrapper function for get_input_list and get_input_format.

        TODO: Rip this out."""
        if type(prompt) is list:
            return self.get_input_list(prompt)
        elif type(prompt) is str:
            return self.get_input_format(prompt, default)
        else:
            print 'Invalid input'
            return ''

    def get_input_list(self, list_vals):
        """Get input from a list of predetermined responses.

        Args:
            list_vals ([str]): A list of potential responses.

        Returns:
            int: The index of the selected response."""
        index = 0
        self.blink(False)
        self.clear()
        self.message(list_vals[index])
        while True:
            time.sleep(0.15)
            if self.is_pressed(UP):
                index = ((index + 1) % len(list_vals))
            elif self.is_pressed(DOWN):
                index = ((index - 1) % len(list_vals))
            elif self.is_pressed(SELECT):
                break
            else:
                continue
            self.clear()
            self.message(list_vals[index])
        self.clear()
        return index

    def get_input_format(self, lcd_format, default=None):
        """Get input according to the rules of lcd_format.

        TODO: Better documentation about format of lcd_format.

        Args:
            lcd_format (str): The format of the input to poll for.
            default (str): Defaults for the values of lcd_format."""
        list_chars = []
        i = 0
        while i < len(lcd_format):
            advance, char = self.parse_char(lcd_format[i:i+2])
            i += advance
            list_chars.append(char)

        if default is not None:
            list_chars = self.use_default(list_chars, default)

        index = self.find_next_input(list_chars, -1)
        if index == -1:
            print 'Enter a format, dummy'
            return lcd_format

        self.blink(True)
        list_chars = self.modify_chars(list_chars, index)

        return ''.join([x.value for x in list_chars])
