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
#    theaterChase(strip, Color(127, 127, 127))  # White theater chase
#    theaterChase(strip, Color(127,   0,   0))  # Red theater chase
#    theaterChase(strip, Color(  0,   0, 127))  # Blue theater chase
    # Rainbow animations.
#    rainbow(strip)
#    rainbowCycle(strip)
#    theaterChaseRainbow(strip)

###############################################################################
###############################################################################
#Connection Information For Database API
BASE_RECIPE_URL = 'http://theopenbar.herokuapp.com/api/drinks/'
#BASE_USERQUERY_URL = 'http://theopenbar.herokuapp.com/api/users/'
BASE_STATIONQUERY_URL = 'http://theopenbar.herokuapp.com/api/station/'
STATION_ID = '56a2be2d5d08dd13939871de'

DRAIN_TIME_MS = 1000
RINSE_FILL_TIME_MS = 100
RINSE_DRAIN_TIME_MS = 1000
LINE_PURGE_TIME_MS =300
VALVE_TEST_INTERVAL_MS = 100

MAX_DRINK_SIZE = 8 #oz

#Mapping of Valves to Output numbers
PUMP_OUTPUT = 26
PRESSURE_RELEASE_VALVE = 27
VAC_SOURCE_CHAMBER_VALVE = 28
VAC_SOURCE_DRAIN_VALVE = 29
DRAIN_VALVE =30
RINSE_TANK_VALVE = 31
AIR_PURGE_VALVE = 32

def setup_valves(io_board, address=0x20):
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

def activate_valve(valve, io_board, time_ms=0, on=True):
    if valve >0 and valve <=8:
        pin = valve-1
        if on:
            pass
#            io_board[0].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            pass
#            io_board[0].output(pin,GPIO.LOW)
    elif valve >8 and valve <=16:
        pin = valve-9
        if on:
            pass
#            io_board[1].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            pass
#            io_board[1].output(pin,GPIO.LOW)
    elif valve >16 and valve <=24:
        pin = valve-17
        if on:
            pass
#            io_board[2].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            pass
#            io_board[2].output(pin,GPIO.LOW)
    elif valve >24 and valve <=32:
        pin = valve-25
        if on:
            pass
#            io_board[3].output(pin,GPIO.HIGH)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            pass
#            io_board[3].output(pin,GPIO.LOW)

def testValves (io_board, time_ms):
    for i in range(1, 32):
        activate_valve(i, io_board, time_ms)
        time.sleep(time_ms/1000.0)

def vac_onoff(io_board, vac_source="CHAMBER", on=False):
    if on:
        if vac_source == "CHAMBER":
            activate_valve(io_board=io_board, valve=PUMP_OUTPUT)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)
        elif vac_source == "DRAIN":
            activate_valve(io_board=io_board, valve=PUMP_OUTPUT)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE)
        else:
            activate_valve(io_board=io_board, valve=PUMP_OUTPUT, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
            activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)
    else:
        activate_valve(io_board=io_board, valve=PUMP_OUTPUT, on=False)
        activate_valve(io_board=io_board, valve=VAC_SOURCE_CHAMBER_VALVE, on=False)
        activate_valve(io_board=io_board, valve=VAC_SOURCE_DRAIN_VALVE, on=False)

def bubbles_onoff(io_board, on=False):
    if on:
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE)
        vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    else:
        vac_onoff(io_board=io_board)
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, on=False)

def dispense_pressurized_ingredients(io_board, recipe_j, conn):
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == True:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*ingredients[ingredient]['flow_factor']
            activate_valve(io_board=io_board, valve=ingredients[ingredient]['valve'], time_ms=time_ms)
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)

def dispense_vacuum_ingredients(io_board, recipe_j, conn):
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == False:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*ingredients[ingredient]['flow_factor']
            activate_valve(io_board=io_board, valve=ingredients[ingredient]['valve'], time_ms=time_ms)
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)

def check_amounts(recipe_j, conn):
    totalamount = 0
    amounts_ok = True
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        amount = recipe_j['recipe'][i]['amount']
        totalamount = totalamount + amount
        if amount > ingredients[ingredient]['amount']:
            length = len(ingredient)
            conn.sendall(str(length+15) + ' Not enough ' + ingredient + '!')
            amounts_ok = False
    if totalamount > MAX_DRINK_SIZE:
        conn.sendall('35 Recipe size exceeds max allowed!')
        amounts_ok = False
    return amounts_ok

def update_amounts(recipe_j, conn):
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        amount = recipe_j['recipe'][i]['amount']
        ingredients[ingredient]['amount'] = ingredients[ingredient]['amount'] - amount
        #need to add functionality to update amounts in GUI database

def drain_drink(io_board, conn):
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE)
    time.sleep(DRAIN_TIME_MS/1000.0)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE, on=False)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)

def fill_rinse(io_board, conn):
    vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    activate_valve(io_board=io_board, valve=RINSE_TANK_VALVE, time_ms=RINSE_FILL_TIME_MS)
    vac_onoff(io_board=io_board)

def drain_rinse(io_board, conn):
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    vac_onoff(io_board=io_board, vac_source="DRAIN", on=True)
    time.sleep(RINSE_DRAIN_TIME_MS/1000.0)
    vac_onoff(io_board=io_board)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)

def makedrink(io_board, recipe_j, conn):
    try:
        pull_station_data(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
        conn.sendall("34 Could Not Retrieve Station Data")
    if check_amounts(recipe_j, conn):
        dispense_pressurized_ingredients(io_board, recipe_j, conn)
        vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
        dispense_vacuum_ingredients(io_board, recipe_j, conn)
        #PURGE INGREDIENTS SUPPLY LINE
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
        vac_onoff(io_board)
        drain_drink(io_board, conn)
        update_amounts(recipe_j, conn)

def pull_station_data(stationID):
    req = urllib2.Request(BASE_STATIONQUERY_URL + stationID)
    response = urllib2.urlopen(req)
    station_j = json.load(response)
    for i in range(0, len(station_j['ingredients'])):
        ingredients[station_j['ingredients'][i]['type']] = station_j['ingredients'][i]

def reset(io_board):
    try:
        io_board = {}
        setup_valves(io_board)
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup IO Board'
    try:
        pull_station_data(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'

def parse_cmd(cmd, data, conn, io_board):
    if cmd == '00': #reset
        reset(io_board)
        return '07 DONE'
    elif cmd == '01': #Make Recipe with ID (data)
        req = urllib2.Request(BASE_RECIPE_URL + data)
        url_response = urllib2.urlopen(req)
        recipe_j = json.load(url_response)
        print 'Drink Ordered: ' + recipe_j['name']
        print 'Ingredients:'
        for i in range (0, len(recipe_j['recipe'])):
            print recipe_j['recipe'][i]['ingredient'] + '\t\t ' + str(recipe_j['recipe'][i]['amount']) + 'oz'
        makedrink(io_board, recipe_j, conn)
        return '07 DONE'
    elif cmd == '02': #Make Recipe Selected by User with ID (data)

        #Need to implement


        return '07 DONE'
    elif cmd == '03': #Test Neopixel Ring
        testLEDs()
        return '07 DONE'
    elif cmd == '04': #Open Valve number (data)
        activate_valve(io_board=io_board, valve=int(data))
        return '07 DONE'
    elif cmd == '05': #Close Valve number (data)
        activate_valve(io_board=io_board, valve=int(data), on=False)
        return '07 DONE'
    elif cmd == '06': #Fill Rinse
        fill_rinse(io_board)
        return '07 DONE'
    elif cmd == '07': #Drain Rinse
        drain_rinse(io_board)
        return '07 DONE'
    elif cmd == '08': #Activate Vacuum (BUBBLES/PURGE)
        bubbles_onoff(io_board, on=True)
        return '07 DONE'
    elif cmd == '09': #Turn off Vacuum (BUBBLES/PURGE)
        bubbles_onoff(io_board, on=False)
        return '07 DONE'
    elif cmd == '10': #Pull Station Data from Database
        pull_station_data(STATION_ID)
        return '07 DONE'
    elif cmd == '11': #Return Controller state

        #add functionality to return valve states? or mode?

        return '07 DONE'
    elif cmd == '12': #Test Valves/Outputs
        testValves(io_board, VALVE_TEST_INTERVAL_MS)
        return '07 DONE'
    else:
        print >> sys.stderr, 'Unable To Parse Command'
        return '08 ERROR'


#GLOBAL DATA
station_j = {}      #Python object of retrieved station JSON data
ingredients = {}    #Python object of ingredients part of station JSON data
                    #    to reference by ingredient for matching to recipe_j, & updating amounts

if __name__ == '__main__':
    io_board = {}
    try:
        setup_valves(io_board)
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup IO Board'
    try:
        pull_station_data(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, 'Starting Socket Server on localhost port 1000'

    try:
        s.bind(('192.168.0.5',1000))
    except socket.error as msg:
        print >> sys.stderr, 'Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]

    s.listen(1)

    print ('Press Ctrl-C To Quit')
    try:
        while True:
            print >> sys.stderr, 'TOB Waiting For Connection'
            conn, addr = s.accept()
            try:
                data = ''
                print >> sys.stderr, 'TOB Client Connected:', addr
                cmd = conn.recv(2)
                print 'Received Command: "%s"' % cmd
                if int(cmd) >= 1 and int(cmd) <= 02:
                    data = conn.recv(33)
                    data = data[1:33]
                    print 'Received Data: "%s"' % data
                response = parse_cmd(cmd, data, conn, io_board)
                if response:
                    conn.sendall(response)
            except KeyboardInterrupt:
                raise
            except:
                conn.sendall('08 ERROR')
                raise###
            finally:
                conn.close()
    except KeyboardInterrupt:
        print '\r\nGoodbye!\r\n'
    s.close()
