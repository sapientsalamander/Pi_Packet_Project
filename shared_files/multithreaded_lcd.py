import time


def lock_and_display_bandwidth_LED(lcd, lcd_lock, bandwidth, bw_unit):
    """Changes the LED color for different amounts of traffic.

    bandwidth -- the amount of traffic
    bw_unit -- the unit accompanying the bandwidth (bps, Kbps, Mbps)
    """
    with lcd_lock:
        if bw_unit == 0 and bandwidth == 0:
            lcd.set_color(0, 0, 0)
        elif bw_unit == 0:
            lcd.set_color(0, 0, 1)
        elif bw_unit == 1:
            lcd.set_color(0, 1, 0)
        elif bw_unit == 2:
            lcd.set_color(1, 0, 0)


def lock_and_set_led_color(lcd, lcd_lock, r, g, b):
    with lcd_lock:
        lcd.set_color(r, g, b)


def lock_and_print_lcd_line(lcd, lcd_lock, message, line):
    """Print message to screen on line, multithreading safe.

    Locks the LCD so that only one thread can write to it at a time.
    Also ensures that writing to a line won't clear the entire screen.
    """
    # Pad with spaces, manually clearing the line on LCD.
    message = message.ljust(20)
    with lcd_lock:
        lcd.set_cursor(0, line)
        lcd.message(message)


def flash_led(lcd, lcd_lock, r, g, b):
    lock_and_set_led_color(lcd, lcd_lock, r, g, b)
    time.sleep(0.1)
    lock_and_set_led_color(lcd, lcd_lock, 0, 0, 0)
