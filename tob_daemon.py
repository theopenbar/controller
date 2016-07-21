#Python Server Daomon to run The Open Bar Control Board and Neo Pixel

import sys
import socket
import time
import urllib2
import json
from thread import *

from Adafruit_GPIO import MCP230xx

from neopixel import *


# LED strip configuration:
LED_COUNT      = 16      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = True   # True to invert the signal (when using NPN transistor level shift)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
# Intialize the library (must be called once before other functions).
strip.begin()

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChase(strip, color, wait_ms=50, iterations=10):
    """Movie theater light style chaser animation."""
    for j in range(iterations):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, color)
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)

def rainbow(strip, wait_ms=20, iterations=1):
    """Draw rainbow that fades across all pixels at once."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((i+j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def rainbowCycle(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel(((i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

def theaterChaseRainbow(strip, wait_ms=50):
    """Rainbow movie theater light style chaser animation."""
    for j in range(256):
        for q in range(3):
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, wheel((i+j) % 255))
            strip.show()
            time.sleep(wait_ms/1000.0)
            for i in range(0, strip.numPixels(), 3):
                strip.setPixelColor(i+q, 0)

def testLEDs():
    # Color wipe animations.
    colorWipe(strip, Color(255, 0, 0))  # Red wipe
    colorWipe(strip, Color(0, 255, 0))  # Blue wipe
    colorWipe(strip, Color(0, 0, 255))  # Green wipe
    # Theater chase animations.
    theaterChase(strip, Color(127, 127, 127))  # White theater chase
    theaterChase(strip, Color(127,   0,   0))  # Red theater chase
    theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
    # Rainbow animations.
    rainbow(strip)
    rainbowCycle(strip)
    theaterChaseRainbow(strip)

###############################################################################
###############################################################################
BASE_RECIPE_URL = 'http://theopenbar.herokuapp.com/api/drinks/'
BASE_USERQUERY_URL = 'http://theopenbar.herokuapp.com/api/drinks/'
BASE_STATIONQUERY_URL = 'http://theopenbar.herokuapp.com/apt/station/'
STATION_ID = '56a2be2d5d08dd13939871de'

DRAIN_TIME_MS = 1000
RINSE_FILL_TIME_MS = 100
RINSE_DRAIN_TIME_MS = 1000
LINE_PURGE_TIME_MS =300

NUM_INGREDIENTS = 18
MAX_POUR = 8 #oz

PUMP_PIN = 26
PRESSURE_RELEASE_VALVE = 27
VAC_SOURCE_CHAMBER_VALVE = 28
VAC_SOURCE_DRAIN_VALVE = 29
DRAIN_VALVE =30
RINSE_TANK_VALVE = 31
AIR_PURGE_VALVE = 32


def setup_valves(address=0x20):
    io_board[0] = MCP230xx.MCP23008(address)
    io_board[1] = MCP230xx.MCP23008((address+0x1))
    io_board[2] = MCP230xx.MCP23008((address+0x2))
    io_board[3] = MCP230xx.MCP23008((address+0x3))
    io_board[0].write_gpio(0x00)
    io_board[1].write_gpio(0x00)
    io_board[2].write_gpio(0x00)
    io_board[3].write_gpio(0x00)
    io_board[0].write_gppu(0xFF)
    io_board[1].write_gppu(0xFF)
    io_board[2].write_gppu(0xFF)
    io_board[3].write_gppu(0xFF)
    io_board[0].write_iodir(0x00)
    io_board[1].write_iodir(0x00)
    io_board[2].write_iodir(0x00)
    io_board[3].write_iodir(0x00)
    return io_bard

def activate_valve(valve, io_board, time_ms=0, on=True):
    if valve >0 and valve <=8:
        pin = valve-1
        if on:
            io_board[0].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[0].output(pin,GPIO.LOW)
    elif valve >8 and valve <=16:
        pin = valve-9
        if on:
            io_board[1].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[1].output(pin,GPIO.LOW)
    elif valve >16 and valve <=24:
        pin = valve-17
        if on:
            io_board[2].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[2].output(pin,GPIO.LOW)
    elif valve >24 and valve <=32:
        pin = valve-25
        if on:
            io_board[3].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[3].output(pin,GPIO.LOW)

def dispense_ingredient(io_board, ingredient_num, amount):
    if ingredient_num <= NUM_INGREDIENTS and amount > 0 and amount <= MAX_POUR:
        time_ms=amount*flow_factor[valve]
        activate_valve(io_board=io_board, valve=ingredient_num, time_ms=time_ms)

def vac_onoff(io_board, vac_source="CHAMBER", on=False):
    if on:
        if vac_source == "CHAMBER":
            activate_valve(io_board=io_board, valve=PUMP_PIN)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)
        elif vac_source == "DRAIN":
            activate_valve(io_board=io_board, valve=PUMP_PIN)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE)
        else:
            activate_valve(io_board=io_board, valve=PUMP_PIN, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)
    else:
        activate_valve(io_board=io_board, valve=PUMP_PIN, on=False)
        activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
        activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)

def bubbles_onoff(io_board, on=False):
    if on:
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE)
        vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    else:
        vac_onoff(io_board=io_board)
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, on=False)

def dispense_pressurized_ingredients(io_board, drink):
    #get pressurized ingredients
    pass
    #dispense each ingredient for required amount



def dispense_vacuum_ingredients(io_board, drink):
    #get vaccuum ingredients
    pass
    #dispense each ingredient for required amount

def drain_drink(io_board):
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE)
    time.sleep(DRAIN_TIME_MS/1000.0)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE, on=False)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)

def fill_rinse(io_board):
    vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    activate_valve(io_board=io_board, valve=RINSE_TANK_VALVE, time_ms=RINSE_FILL_TIME_MS)
    vac_onoff(io_board=io_board)

def drain_rinse(io_board):
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    vac_onoff(io_board=io_board, vac_source="DRAIN", on=True)
    time.sleep(RINSE_DRAIN_TIME_MS/1000.0)
    vac_onoff(io_board=io_board)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)

def makedrink(io_board, drink):
    dispense_pressurized_ingredients(io_board, drink)
    vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    dispense_vacuum_ingredients(io_board, drink)
    #PURGE INGREDIENTS SUPPLY LINE
    activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
    vac_onoff(io_board)
    drain_drink(io_board)

def parse_cmd(cmd, data, conn, io_board):
    if cmd == "00": #reset
        return "OK"
    elif cmd == "01": #Make Recipe with ID (data)
        req = urllib2.Request(BASE_RECIPE_URL + data)
        response = urllib2.urlopen(req)
        recipe = response.read()
        print recipe
        #makedrink(io_board, recipe)
        return "OK"
    elif cmd == "02": #Make Recipe Selected by User with ID (data)
        return "OK"
    elif cmd == "03": #Test Neopixel Ring
        testLEDs()
        return "OK"
    elif cmd == "04": #Open Valve number (data)
        activate_valve(io_board=io_board, valve=int(data))
        return "OK"
    elif cmd == "05": #Close Valve number (data)
        activate_valve(io_board=io_board, valve=int(data), on=False)
        return "OK"
    elif cmd == "06": #Fill Rinse
        fill_rinse(io_board)
        return "OK"
    elif cmd == "07": #Drain Rinse
        drain_rinse(io_board)
        return "OK"
    elif cmd == "08": #Activate Vacuum (BUBBLES/PURGE)
        bubbles_onoff(io_board, on=True)
        return "OK"
    elif cmd == "09": #Turn off Vacuum (BUBBLES/PURGE)
        bubbles_onoff(io_board, on=False)
        return "OK"
    else:
        print >> sys.stderr, 'Unable to Parse Command'
        return 'ERROR'


# Main program logic follows:
if __name__ == '__main__':
    io_board = ''
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, 'Starting Server on localhost port 1000'

    try:
        s.bind(('192.168.0.5',1000))
    except socket.error as msg:
        print >> sys.stderr, 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]

    s.listen(1) #ensure only one client can control the unit at a time

    print ('Press Ctrl-C to quit.')
    try:
        while True:
            print >> sys.stderr, 'TOB waiting for connection'
            conn, addr = s.accept()
            try:
                print >> sys.stderr, 'TOB client connected:', addr
                cmd = conn.recv(2)
                print 'Received Command: "%s"' % cmd
                if int(cmd) >= 1 and int(cmd) <= 02:
                    data = conn.recv(33)
                    data = data[1:33]
                    print 'Recieved Data: "%s"' % data
                else:
                    data = 'COMMAND'
                response = parse_cmd(cmd, data, conn, io_board)
                if response:
                    conn.sendall(response)
            except KeyboardInterrupt:
                raise
            except:
                conn.sendall('ERROR')
                raise###
            finally:
                conn.close()
    except KeyboardInterrupt:
        raise ###
        print 'Goodbye'
    s.close()
