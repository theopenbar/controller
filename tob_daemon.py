#Python Server Daomon to run The Open Bar Control Board and Neo Pixel

import sys
import socket
import time
import urllib
import urllib2
import json
import thread
import threading
import ConfigParser

from Adafruit_GPIO import MCP230xx
from neopixel import *

##################################################################################################
#Configuration Parameteres
##################################################################################################
parser = ConfigParser.SafeConfigParser()
parser.read('config.ini')
BIND_IP = parser.get('SocketBindings', 'host')
BIND_PORT = parser.getint('SocketBindings', 'port')
BASE_API_HOST_URL = parser.get('API', 'base_url')
RECIPE_URL = parser.get('API', 'recipe_route')
USERQUERY_URL = parser.get('API', 'user_route')
STATIONQUERY_URL = parser.get('API', 'station_route')
STATIONPOST_URL = parser.get('API', 'ingredient_route')
STATION_ID = "" #set in main
STATION_AUTH = "" #set in main
FLOW_FACTOR_MS_OZ_UNPRESSURIZED = parser.getint('StationCalibration', 'flow_factor_ms_oz_unpressurized')
FLOW_FACTOR_MS_OZ_PRESSURIZED = parser.getint('StationCalibration', 'flow_factor_ms_oz_pressurized')
TRAVEL_TIME_MS = parser.getint('StationCalibration', 'travel_time_ms')
RINSE_FILL_TIME_MS = parser.getint('StationCalibration', 'full_rinse_fill_time_ms')
RINSE_DRAIN_TIME_MS = parser.getint('StationCalibration', 'full_rinse_drain_time_ms')
LINE_PURGE_TIME_MS = parser.getint('StationCalibration', 'line_purge_time_ms')
VALVE_TEST_INTERVAL_MS = parser.getint('StationCalibration', 'valve_test_interval_ms')
PRESSURED_DRAIN_TIME_MULT = parser.getint('StationCalibration', 'pressured_drain_time_mult')
UNPRESSURED_DRAIN_TIME_MULT = parser.getint('StationCalibration', 'unpressured_drain_time_mult')
DRAIN_TIME_ADDON_MS = parser.getint('StationCalibration', 'drain_time_addon_ms')
MAX_DRINK_SIZE = parser.getint('StationCalibration', 'max_drink_size_oz')
PUMP_OUTPUT = parser.getint('OutputMapping', 'pump_output')
PRESSURE_BYPASS_VALVE = parser.getint('OutputMapping', 'pressure_bypass_valve')
PRESSURIZE_VALVE = parser.getint('OutputMapping', 'pressurize_valve')
VAC_BYPASS_VALVE = parser.getint('OutputMapping', 'vac_bypass_valve')
VACUUM_VALVE = parser.getint('OutputMapping', 'vacuum_valve')
DRAIN_VALVE = parser.getint('OutputMapping', 'drain_valve')
RINSE_TANK_VALVE = parser.getint('OutputMapping', 'rinse_tank_valve')
AIR_PURGE_VALVE = parser.getint('OutputMapping', 'air_purge_valve')
ON = parser.getint('OutputMapping', 'on')
OFF =parser.getint('OutputMapping', 'off')
LED_COUNT      = parser.getint('LED', 'led_count')
LED_PIN        = parser.getint('LED', 'led_pin')
LED_FREQ_HZ    = parser.getint('LED', 'led_freq_hz')
LED_DMA        = parser.getint('LED', 'led_dma')
LED_BRIGHTNESS = parser.getint('LED', 'led_brightness')
LED_INVERT     = parser.getboolean('LED', 'led_invert')

##################################################################################################
#LED functions
##################################################################################################
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

def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

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

def theaterChaseRainbow(strip, wait_ms=50, iterations=1):
    """Rainbow movie theater light style chaser animation."""
    for j in range(0, 256, 10):
        theaterChase(strip, wheel(j), wait_ms, iterations)

def ledWorker(strip):
    while not stop:
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
#Controller Functions
###############################################################################
def setupOutputs(io_board):
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

def activateOutput(output, io_board, time_ms=0, on=True):
    if output >0 and output <=8:
        pin = output-1
        if on:
            io_board[0].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[0].output(pin,OFF)
    elif output >8 and output <=16:
        pin = output-9
        if on:
            io_board[1].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[1].output(pin,OFF)
    elif output >16 and output <=24:
        pin = output-17
        if on:
            io_board[2].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[2].output(pin,OFF)
    elif output >24 and output <=32:
        pin = output-25
        if on:
            io_board[3].output(pin,ON)
        if time_ms > 0:
            time.sleep(time_ms/1000.0)
        if (not on) or time_ms > 0:
            io_board[3].output(pin,OFF)

def testValves (io_board, time_ms):
    for i in range(1, 32):
        activateOutput(i, io_board, time_ms)
        time.sleep(time_ms/1000.0)

def pumpOnOff(io_board, mode="VACUUM", on=False):
    if on:
        if mode == "PRESSURIZE":
            activateOutput(io_board=io_board, output=PUMP_OUTPUT)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
            activateOutput(io_board=io_board, output=VACUUM_VALVE, on = False)
            activateOutput(io_board=io_board, output=VAC_BYPASS_VALVE)
        elif mode == "VACUUM":
            activateOutput(io_board=io_board, output=PUMP_OUTPUT)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE)
            activateOutput(io_board=io_board, output=VACUUM_VALVE)
            activateOutput(io_board=io_board, output=VAC_BYPASS_VALVE, on=False)
        else:
            activateOutput(io_board=io_board, output=PUMP_OUTPUT, on=False)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
            activateOutput(io_board=io_board, output=VACUUM_VALVE, on=False)
            activateOutput(io_board=io_board, output=VAC_BYPASS_VALVE, on=False)

    else:
        #shutoff pump
        activateOutput(io_board=io_board, output=PUMP_OUTPUT, on=False)
        #relieve pressure in chamber
        activateOutput(io_board=io_board, output=PRESSURIZE_VALVE)
        activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE)
        activateOutput(io_board=io_board, output=VACUUM_VALVE)
        activateOutput(io_board=io_board, output=VAC_BYPASS_VALVE)
        time.sleep(1)
        #now close valves
        activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
        activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
        activateOutput(io_board=io_board, output=VACUUM_VALVE, on=False)
        activateOutput(io_board=io_board, output=VAC_BYPASS_VALVE, on=False)

def bubblesOnOff(io_board, on=False):
    global LED_pattern
    if on:
        LED_pattern = 1
        activateOutput(io_board=io_board, output=AIR_PURGE_VALVE)
        pumpOnOff(io_board=io_board, mode="VACUUM", on=True)
    else:
        LED_pattern = 0
        pumpOnOff(io_board=io_board)
        activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, on=False)

def dispensePressurizedIngredients(io_board, recipe_j, conn):
    total_time = 0
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == True:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*FLOW_FACTOR_MS_OZ_PRESSURIZED
            total_time = time_ms + total_time
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)
            activateOutput(io_board=io_board, output=ingredients[ingredient]['valve'], time_ms=time_ms)
            updateAmount(recipe_j, conn, STATION_ID, ingredient)
    return total_time

def dispenseVacuumIngredients(io_board, recipe_j, conn):
    total_time = 0
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        if ingredients[ingredient]['pressurized'] == False:
            amount = recipe_j['recipe'][i]['amount']
            time_ms=amount*FLOW_FACTOR_MS_OZ_UNPRESSURIZED
            total_time = time_ms + total_time
            length = len(ingredient)
            conn.sendall(str(length+14) + ' Dispensing ' + ingredient)
            activateOutput(io_board=io_board, output=ingredients[ingredient]['valve'], time_ms=time_ms + TRAVEL_TIME_MS)
            updateAmount(recipe_j, conn, STATION_ID, ingredient)
    return total_time

def checkAmounts(recipe_j, conn):
    totalamount = 0
    amounts_ok = True
    for i in range (0, len(recipe_j['recipe'])):
        ingredient = recipe_j['recipe'][i]['ingredient']
        amount = recipe_j['recipe'][i]['amount']
        totalamount = totalamount + amount
        length = len(ingredient)
        try:
            amount_left = ingredients[ingredient]['amount']
        except:
            conn.sendall(str(length+36) + ' [ERROR] No ' + ingredient + ' configured in station')
            print >> sys.stderr, '[ERROR] No ' + ingredient + ' configured in station'
            amounts_ok = False
        else:
            if amount > amount_left:
                conn.sendall(str(length+15) + ' Not enough ' + ingredient + '!')
                amounts_ok = False
    if totalamount > MAX_DRINK_SIZE:
        conn.sendall('35 Recipe size exceeds max allowed!')
        amounts_ok = False
    return amounts_ok

def updateAmount(recipe_j, conn, stationID, ingredient):
    for i in range(0, len(recipe_j['recipe'])):
        if recipe_j['recipe'][i]['ingredient'] == ingredient:
            amount = recipe_j['recipe'][i]['amount']
            ingredients[ingredient]['amount'] = ingredients[ingredient]['amount'] - amount
            try:
                data = urllib.urlencode(ingredients[ingredient])
                u = urllib2.urlopen(BASE_API_HOST_URL + STATIONPOST_URL + stationID, data)
            except:
                print >> sys.stderr, '[ERROR] Could Not Update Remote Ingredient Data'

def fillRinse(io_board):
    global LED_pattern
    LED_pattern = 1
    pumpOnOff(io_board=io_board, mode="VACUUM", on=True)
    activateOutput(io_board=io_board, output=RINSE_TANK_VALVE, time_ms=RINSE_FILL_TIME_MS)
    #PURGE INGREDIENTS SUPPLY LINE
    activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
    pumpOnOff(io_board=io_board)
    LED_pattern = 0

def drainRinse(io_board):
    global LED_pattern
    LED_pattern = 1
    activateOutput(io_board=io_board, output=RINSE_TANK_VALVE)
    pumpOnOff(io_board=io_board, mode="PRESSURIZE", on=True)
    time.sleep(RINSE_DRAIN_TIME_MS/1000.0)
    pumpOnOff(io_board=io_board)
    activateOutput(io_board=io_board, output=RINSE_TANK_VALVE, on=False)
    LED_pattern = 0

def makeDrink(io_board, recipe_j, conn):
    global LED_pattern
    print 'Drink Ordered: ' + recipe_j['name']
    print 'Ingredients:'
    for i in range (0, len(recipe_j['recipe'])):
        print recipe_j['recipe'][i]['ingredient'] + '\t\t ' + str(recipe_j['recipe'][i]['amount']) + 'oz'
    try:
        pullStationData(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
        conn.sendall("34 Controller Could Not Retrieve Station Data")
        return '08 ERROR'
    if checkAmounts(recipe_j, conn):
        LED_pattern = 1
        time1 = dispensePressurizedIngredients(io_board, recipe_j, conn)
        pumpOnOff(io_board=io_board, mode="VACUUM", on=True)
        time2 = dispenseVacuumIngredients(io_board, recipe_j, conn)
        #PURGE INGREDIENTS SUPPLY LINE
        activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
        #DRAIN DRINK
        conn.sendall('16 Pouring Drink')
        drain_time = time1*PRESSURED_DRAIN_TIME_MULT + time2*UNPRESSURED_DRAIN_TIME_MULT + DRAIN_TIME_ADDON_MS
        pumpOnOff(io_board=io_board, mode="PRESSURIZE", on=True)
        activateOutput(io_board=io_board, output=DRAIN_VALVE)
        time.sleep(drain_time/1000.0)
        activateOutput(io_board=io_board, output=DRAIN_VALVE, on=False)
        pumpOnOff(io_board)
        LED_pattern = 0
        return '07 DONE'
    else:
        return '08 ERROR'

def pullStationData(stationID):
    req = urllib2.Request(BASE_API_HOST_URL + STATIONQUERY_URL + stationID)
    response = urllib2.urlopen(req)
    station_j = json.load(response)
    for i in range(0, len(station_j['ingredients'])):
        ingredient = station_j['ingredients'][i]['type']
        if ingredient != '':
            ingredients[ingredient] = station_j['ingredients'][i]

def reset(io_board):
    global lock
    global LED_pattern
    lock = False
    LED_pattern = 0
    setupOutputs(io_board)
    try:
        pullStationData(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'

def parseCmd(cmd, data, conn, io_board):
    if cmd == '00': #reset
        conn.sendall("22 Received Command " + cmd)
        reset(io_board)
        return '07 DONE'
    elif cmd == '01': #Make Recipe with ID (data)
        conn.sendall("22 Received Command " + cmd)
        req = urllib2.Request(BASE_API_HOST_URL+ RECIPE_URL + data)
        url_response = urllib2.urlopen(req)
        recipe_j = json.load(url_response)
        return makeDrink(io_board, recipe_j, conn)
    elif cmd == '02': #Make Recipe Selected by User with ID (data)
        conn.sendall("22 Received Command " + cmd)

        #Need to implement


        return '07 DONE'
    elif cmd == '03': #Open Valve number (data)
        conn.sendall("22 Received Command " + cmd)
        activateOutput(io_board=io_board, output=int(data))
        return '07 DONE'
    elif cmd == '04': #Close Valve number (data)
        conn.sendall("22 Received Command " + cmd)
        activateOutput(io_board=io_board, output=int(data), on=False)
        return '07 DONE'
    elif cmd == '05': #Test led pattern
        conn.sendall("22 Received Command " + cmd)
        global LED_pattern
        LED_pattern = int(data)
        return '07 DONE'
    elif cmd == '06': #Set Station ID
        conn.sendall("22 Received Command " + cmd)
        cfgfile = open('config.ini','w')
        parser.set('API', 'station_id', data)
        parser.write(cfgfile)
        cfgfile.close()
        return '07 DONE'
    elif cmd == '07': #Fill Full Rinse
        conn.sendall("22 Received Command " + cmd)
        fillRinse(io_board)
        return '07 DONE'
    elif cmd == '08': #Drain Full Rinse
        conn.sendall("22 Received Command " + cmd)
        drainRinse(io_board)
        return '07 DONE'
    elif cmd == '09': #Activate Vacuum (BUBBLES/PURGE)
        conn.sendall("22 Received Command " + cmd)
        bubblesOnOff(io_board, on=True)
        return '07 DONE'
    elif cmd == '10': #Turn off Vacuum (BUBBLES/PURGE)
        conn.sendall("22 Received Command " + cmd)
        bubblesOnOff(io_board, on=False)
        return '07 DONE'
    elif cmd == '11': #Pull Station Data from Database
        conn.sendall("22 Received Command " + cmd)
        pullStationData(STATION_ID)
        return '07 DONE'
    elif cmd == '12': #Test Valves/Outputs
        conn.sendall("22 Received Command " + cmd)
        testValves(io_board, VALVE_TEST_INTERVAL_MS)
        return '07 DONE'
    else:
        conn.sendall("22 Received Command " + cmd)
        print >> sys.stderr, '[ERROR] Invalid Command'
        return '08 ERROR'

def connectionWorker(conn):
    global lock
    lock = True
    data = ''
    try:
        cmd = conn.recv(2)
        print 'Received Command: "%s"' % cmd
        if int(cmd) >= 1 and int(cmd) <= 6:
            data = conn.recv(33)
            data = data[1:33]
            print 'Received Data: "%s"' % data
        response = parseCmd(cmd, data, conn, io_board)
        if response:
            conn.sendall(response)
            print response
    except KeyboardInterrupt:
        conn.sendall('08 ERROR')
        raise
    except Exception as e:
        conn.sendall('08 ERROR')
        print >> sys.stderr, '[ERROR] In connectionWorker:' + str(e)
    finally:
        conn.close()
        lock = False
        threads.remove(threading.current_thread())

###############################################################################
#Main Program
###############################################################################
#GLOBAL DATA
io_board = {}
stop = False        #Flag to stop threads
lock = False        #Lock to decline further connections during a processing job
LED_pattern = 0     #Current Pattern For LEDs
station_j = {}      #Python object of retrieved station JSON data
ingredients = {}    #Array of ingredient objects from station JSON data referenced by ingredient
                    #to reference by ingredient for matching to recipe_j, & updating amounts
threads = []

if __name__ == '__main__':
    address = 0x20
    try:
        io_board[0] = MCP230xx.MCP23008(address)
        io_board[1] = MCP230xx.MCP23008((address+0x1))
        io_board[2] = MCP230xx.MCP23008((address+0x2))
        io_board[3] = MCP230xx.MCP23008((address+0x3))
        setupOutputs(io_board)
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup IO Board'
    try:
        # Create NeoPixel object with appropriate configuration.
        strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
        # Intialize the library (must be called once before other functions).
        strip.begin()
        ledThread = threading.Thread(target=ledWorker, args=(strip,))
        threads.append(ledThread)
        ledThread.start()
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup LED thread'
    print >> sys.stderr, 'Attempting To Pull Station Data from ' + BASE_API_HOST_URL + STATIONQUERY_URL
    try:
        STATION_ID = parser.get('API', 'station_id')
        STATION_AUTH = parser.get('API', 'station_auth')
        if STATION_ID == "": raise Exception("No Station ID configured. Please set using GUI")
        if STATION_AUTH == "": raise Exception("No Station Authorization configured. Please set using GUI")
    except Exception as e:
        print >> sys.stderr, '[WARNING] ' + e[0]
    try:
        pullStationData(STATION_ID)
    except:
        print >> sys.stderr, '[ERROR] Unable to pull station data'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, 'Starting Socket Server at ' + BIND_IP + ':' + str(BIND_PORT)
    try:
        s.bind((BIND_IP,BIND_PORT))
    except socket.error as msg:
        print >> sys.stderr, '[ERROR] Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]

    s.listen(5)
    print ('Press Ctrl-C To Quit')
    while not stop:
        print >> sys.stderr, 'TOB Waiting For Connection'
        try:
            conn, addr = s.accept()
            print >> sys.stderr, 'TOB Client Connected:', addr
            if lock:
                conn.sendall('07 BUSY')
                conn.close()
            else:
                connectionThread = threading.Thread(target=connectionWorker, args=(conn,))
                threads.append(connectionThread)
                connectionThread.start()
        except KeyboardInterrupt:
            stop = True
    for thread in threads:
        thread.join()
    s.close()
    print '\r\nGoodbye!\r\n'
