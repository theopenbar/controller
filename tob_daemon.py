#Python Server Daomon to run The Open Bar Control Board and Neo Pixel

import sys
import socket
import time
import urllib2
import json
import thread

from Adafruit_GPIO import MCP230xx

from neopixel import *


# LED strip configuration:
LED_COUNT      = 16      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

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

def theaterChaseRainbow(strip, wait_ms=50, iterations=1):
    """Rainbow movie theater light style chaser animation."""
    for j in range(0, 256, 10):
        theaterChase(strip, wheel(j), wait_ms, iterations)


def ledWorker():
    while True:
        try:
            if LED_pattern == 1:
                theaterChaseRainbow(strip, wait_ms=40)
            else:
                time.sleep(100/1000.0)
        except:
            raise
        finally:
            colorWipe(strip, Color(0, 0, 0),0)

###############################################################################
###############################################################################
#Connection Information For Database API
BASE_RECIPE_URL = 'http://theopenbar.herokuapp.com/api/drinks/'
#BASE_USERQUERY_URL = 'http://theopenbar.herokuapp.com/api/users/'
BASE_STATIONQUERY_URL = 'http://theopenbar.herokuapp.com/api/station/'
STATION_ID = '56a2be2d5d08dd13939871de'

FLOW_FACTOR_MS_OZ_UNPRESSURIZED = 4570  #ms per oz dispensed for vacuum ingredients
FLOW_FACTOR_MS_OZ_PRESSURIZED = 4570    #ms per oz dispensed for pressurized ingredients
TRAVEL_TIME_MS = 800                #Time for liquid to travel from bottle to valve
RINSE_FILL_TIME_MS = 40000          #Time to run pump to fill chamber for rinse cycle
RINSE_DRAIN_TIME_MS = 50000         #Time to run drain cycle to remove rinse
LINE_PURGE_TIME_MS =5000            #Time to purge ingredient line to chamber after all ingredients
VALVE_TEST_INTERVAL_MS = 1000       #Time interval for the valve test sequence
PRESSURED_DRAIN_TIME_MULT = 2       #Ratio of drain time to fill time for pressurized ingredients
UNPRESSURED_DRAIN_TIME_MULT = 2     #Ratio of drain time to fill time for unpressurized ingredients
DRAIN_TIME_ADDON_MS = 3000          #Additional fixed drain time for each drain cycle

MAX_DRINK_SIZE = 12 #oz             #Max drink size that chamber can accomodate

#Mapping of Valves to Output numbers
PUMP_OUTPUT = 24
PRESSURE_RELEASE_VALVE = 31
VAC_SOURCE_CHAMBER_VALVE = 29
VAC_SOURCE_DRAIN_VALVE = 30
DRAIN_VALVE =26
RINSE_TANK_VALVE = 1
AIR_PURGE_VALVE = 28

ON = 1
OFF = 0

def setup_valves(io_board):
    io_board[0].gpio = [0x00]
    io_board[1].gpio = [0x00]
    io_board[2].gpio = [0x00]
    io_board[3].gpio = [0x00]
    io_board[0].write_gpio()
    io_board[1].write_gpio()
    io_board[2].write_gpio()
    io_board[3].write_gpio()
    io_board[0].gppu = [0xFF]
    io_board[1].gppu = [0xFF]
    io_board[2].gppu = [0xFF]
    io_board[3].gppu = [0xFF]
    io_board[0].write_gppu()
    io_board[1].write_gppu()
    io_board[2].write_gppu()
    io_board[3].write_gppu()
    io_board[0].iodir = [0x00]
    io_board[1].iodir = [0x00]
    io_board[2].iodir = [0x00]
    io_board[3].iodir = [0x00]
    io_board[0].write_iodir()
    io_board[1].write_iodir()
    io_board[2].write_iodir()
    io_board[3].write_iodir()

def activate_valve(valve, io_board, time_ms=0, on=True):
    if valve >0 and valve <=8:
        pin = valve-1
        if on:
            io_board[0].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[0].output(pin,OFF)
    elif valve >8 and valve <=16:
        pin = valve-9
        if on:
            io_board[1].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[1].output(pin,OFF)
    elif valve >16 and valve <=24:
        pin = valve-17
        if on:
            io_board[2].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[2].output(pin,OFF)
    elif valve >24 and valve <=32:
        pin = valve-25
        if on:
            io_board[3].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[3].output(pin,OFF)

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
    global LED_pattern
    if on:
        LED_pattern = 1
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE)
        vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    else:
        LED_pattern = 0
        vac_onoff(io_board=io_board)
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, on=False)

def dispense_pressurized_ingredients(io_board, recipe_j, conn):
    total_time = 0
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == True:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*FLOW_FACTOR_MS_OZ_PRESSURIZED
            total_time = time_ms + total_time
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)
            activate_valve(io_board=io_board, valve=ingredients[ingredient]['valve'], time_ms=time_ms)
    return total_time

def dispense_vacuum_ingredients(io_board, recipe_j, conn):
    total_time = 0
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == False:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*FLOW_FACTOR_MS_OZ_UNPRESSURIZED
            total_time = time_ms + total_time
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)
            activate_valve(io_board=io_board, valve=ingredients[ingredient]['valve'], time_ms=time_ms + TRAVEL_TIME_MS)
    return total_time

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

def drain_drink(io_board, conn, time_ms):
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE)
    time.sleep(time_ms/1000.0)
    activate_valve(io_board=io_board, valve=DRAIN_VALVE, on=False)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)

def fill_rinse(io_board, conn):
    global LED_pattern
    LED_pattern = 1
    vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
    activate_valve(io_board=io_board, valve=RINSE_TANK_VALVE, time_ms=RINSE_FILL_TIME_MS)
    #PURGE INGREDIENTS SUPPLY LINE
    activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
    vac_onoff(io_board=io_board)
    LED_pattern = 0

def drain_rinse(io_board, conn):
    global LED_pattern
    LED_pattern = 1
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE)
    vac_onoff(io_board=io_board, vac_source="DRAIN", on=True)
    time.sleep(RINSE_DRAIN_TIME_MS/1000.0)
    vac_onoff(io_board=io_board)
    activate_valve(io_board=io_board, valve=PRESSURE_RELEASE_VALVE, on=False)
    LED_pattern = 0

def makedrink(io_board, recipe_j, conn):
    global LED_pattern
    try:
        pull_station_data(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
        conn.sendall("34 Could Not Retrieve Station Data")
    if check_amounts(recipe_j, conn):
        LED_pattern = 1
        time1 = dispense_pressurized_ingredients(io_board, recipe_j, conn)
        vac_onoff(io_board=io_board, vac_source="CHAMBER", on=True)
        time2 = dispense_vacuum_ingredients(io_board, recipe_j, conn)
        #PURGE INGREDIENTS SUPPLY LINE
        activate_valve(io_board=io_board, valve=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
        vac_onoff(io_board)
        drain_time = time1*PRESSURED_DRAIN_TIME_MULT + time2*UNPRESSURED_DRAIN_TIME_MULT + DRAIN_TIME_ADDON_MS
        drain_drink(io_board, conn, drain_time)
        LED_pattern = 0
        update_amounts(recipe_j, conn)

def pull_station_data(stationID):
    req = urllib2.Request(BASE_STATIONQUERY_URL + stationID)
    response = urllib2.urlopen(req)
    station_j = json.load(response)
    for i in range(0, len(station_j['ingredients'])):
        ingredient = station_j['ingredients'][i]['type']
        if ingredient != '':
            ingredients[ingredient] = station_j['ingredients'][i]

def reset(io_board):
    setup_valves(io_board)
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
    elif cmd == '03': #Open Valve number (data)
        activate_valve(io_board=io_board, valve=int(data))
        return '07 DONE'
    elif cmd == '04': #Close Valve number (data)
        activate_valve(io_board=io_board, valve=int(data), on=False)
        return '07 DONE'
    elif cmd == '05': #Test led pattern
        global LED_pattern
        LED_pattern = int(data)
        return '07 DONE'
    elif cmd == '06': #Fill Rinse
        fill_rinse(io_board, conn)
        return '07 DONE'
    elif cmd == '07': #Drain Rinse
        drain_rinse(io_board, conn)
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
LED_pattern = 0
station_j = {}      #Python object of retrieved station JSON data
ingredients = {}    #Python object of ingredients part of station JSON data
                    #    to reference by ingredient for matching to recipe_j, & updating amounts


if __name__ == '__main__':
    address = 0x20
    io_board = {}
    try:
        io_board[0] = MCP230xx.MCP23008(address)
        io_board[1] = MCP230xx.MCP23008((address+0x1))
        io_board[2] = MCP230xx.MCP23008((address+0x2))
        io_board[3] = MCP230xx.MCP23008((address+0x3))
        setup_valves(io_board)
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup IO Board'
    try:
        ledThread = thread.start_new_thread(ledWorker,())
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup LED thread'
    try:
        pull_station_data(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, 'Starting Socket Server on localhost port 1000'
    try:
        s.bind(('192.168.0.5',1000))
    except socket.error as msg:
        print >> sys.stderr, '[ERROR] Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]

    s.listen(1)
    stop = False
    print ('Press Ctrl-C To Quit')
    while not stop:
        print >> sys.stderr, 'TOB Waiting For Connection'
        try:
            conn, addr = s.accept()
            data = ''
            print >> sys.stderr, 'TOB Client Connected:', addr
            try:
                cmd = conn.recv(2)
                print 'Received Command: "%s"' % cmd
                if int(cmd) >= 1 and int(cmd) <= 5:
                    data = conn.recv(33)
                    data = data[1:33]
                    print 'Received Data: "%s"' % data
                response = parse_cmd(cmd, data, conn, io_board)
                if response:
                    conn.sendall(response)
                    print response
            except KeyboardInterrupt:
                raise
            except:
                conn.sendall('08 ERROR')
                print 'ERROR'
                raise
            else:
                conn.close()
        except KeyboardInterrupt:
            stop = True
    print '\r\nGoodbye!\r\n'
    s.close()
