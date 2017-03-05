#Python Server Daomon to run The Open Bar Control Board and a Neo Pixel
import sys
import socket
import time
import urllib
import urllib2
import json
import thread
import threading
import ConfigParser
import RPi.GPIO as GPIO

from Adafruit_GPIO import MCP230xx
from neopixel import *

##################################################################################################
#Retrieve Configuration Parameters
##################################################################################################
parser = ConfigParser.SafeConfigParser()
parser.read('/home/pi/controller/config.ini')
BIND_IP = parser.get('SocketBindings', 'host')
BIND_PORT = parser.getint('SocketBindings', 'port')
BASE_API_HOST_URL = parser.get('API', 'base_url')
RECIPE_URL = parser.get('API', 'recipe_route')
STATIONQUERY_URL = parser.get('API', 'station_route')
LIQUIDPOST_URL = parser.get('API', 'liquid_route')
STATION_ID = "" #set in main
STATION_AUTH = "" #set in main
FLOW_FACTOR_MS_OZ_UNPRESSURIZED = parser.getint('StationCalibration', 'flow_factor_ms_oz_unpressurized')
FLOW_FACTOR_MS_OZ_PRESSURIZED = parser.getint('StationCalibration', 'flow_factor_ms_oz_pressurized')
TRAVEL_TIME_MS = parser.getint('StationCalibration', 'travel_time_ms')
RINSE_FILL_TIME_MS = parser.getint('StationCalibration', 'rinse_fill_time_ms')
LINE_PURGE_TIME_MS = parser.getint('StationCalibration', 'line_purge_time_ms')
VALVE_TEST_INTERVAL_MS = parser.getint('StationCalibration', 'valve_test_interval_ms')
CHAMBER_FALL_TIME_MS = parser.getint('StationCalibration', 'chamber_fall_time_ms')
PUMP_TIMEOUT_MS = parser.getint('StationCalibration', 'pump_timeout_ms')
DRINK_REMOVE_TIMEOUT_MS = parser.getint('StationCalibration', 'drink_remove_timeout_ms')
PUMP_EXTRA_MS = parser.getint('StationCalibration', 'pump_extra_ms')
MAX_DRINK_SIZE = parser.getint('StationCalibration', 'max_drink_size_oz')
BUTTON_SWITCH_GPIO = parser.getint('OutputMapping', 'BUTTON_switch_gpio')
PUMP_TOP_SWITCH_GPIO = parser.getint('OutputMapping', 'pump_top_switch_gpio')
PUMP_BOTTOM_SWITCH_GPIO = parser.getint('OutputMapping', 'pump_bottom_switch_gpio')
PUMP_OUTPUT = parser.getint('OutputMapping', 'pump_output')
PRESSURE_BYPASS_VALVE = parser.getint('OutputMapping', 'pressure_bypass_valve')
PRESSURIZE_VALVE = parser.getint('OutputMapping', 'pressurize_valve')
RINSE_TANK_VALVE = parser.getint('OutputMapping', 'rinse_tank_valve')
AIR_PURGE_VALVE = parser.getint('OutputMapping', 'air_purge_valve')
MANUAL_BUTTON_VALVE = parser.getint('OutputMapping', 'manual_button_valve')
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
                time.sleep(250/1000.0)
        except:
            raise Exception("Error in LED Worker")
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
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_TOP_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PUMP_BOTTOM_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_UP)

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
    global maintainHeight
    if on:
        if mode == "PRESSURIZE":
            activateOutput(io_board=io_board, output=PUMP_OUTPUT)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
            maintainHeight = False
        elif mode == "VACUUM":
            activateOutput(io_board=io_board, output=PUMP_OUTPUT)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE)
            maintainHeight = True
        else:
            #incorrect option, do nothing
            activateOutput(io_board=io_board, output=PUMP_OUTPUT, on=False)
            activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
            activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
            maintainHeight = False
    else:
        #ensure we're not trying to maintain the column height
        maintainHeight = False
        #shutoff pump
        activateOutput(io_board=io_board, output=PUMP_OUTPUT, on=False)
        #relieve pressure in chamber
        activateOutput(io_board=io_board, output=PRESSURIZE_VALVE)
        activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE)
        activateOutput(io_board=io_board, output=AIR_PURGE_VALVE)
        #closeChamberValves() must be called after the chamber has fallen
        #should be done by calling function after a timeout

def closeChamberValves():
    activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
    activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
    activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, on=False)

def maintainHeightWorker():
    while not stop:
        try:
            if maintainHeight == True:
                if GPIO.input(PUMP_BOTTOM_SWITCH_GPIO) or GPIO.input(PUMP_TOP_SWITCH_GPIO):
                    activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE, on=False)
                    activateOutput(io_board=io_board, output=PRESSURIZE_VALVE)
                    count = 0
                    while GPIO.input(PUMP_BOTTOM_SWITCH_GPIO) or GPIO.input(PUMP_TOP_SWITCH_GPIO):
                        time.sleep(0.5)
                        count = count + 1
                        if count > 10:
                            print >> sys.stderr, '[ERROR] Timeout in Maintain Height Worker'
                            break
                    activateOutput(io_board=io_board, output=PRESSURE_BYPASS_VALVE)
                    activateOutput(io_board=io_board, output=PRESSURIZE_VALVE, on=False)
                else:
                    #height is okay
                    time.sleep(0.5)
            else:
                #we're idle, not maintaining
                time.sleep(0.5)
        except:
            raise

def dispensePressurizedIngredients(io_board, recipe_j, conn):
    for i in range (0, len(recipe_j['liquids'])):
        liquidId = recipe_j['liquids'][i]['id']['_id']
        liquidType = recipe_j['liquids'][i]['id']['type']
        try:
            if matchedLiquids[liquidId]['pressurized'] == True:
                amount = recipe_j['liquids'][i]['amount']
                time_ms=amount*FLOW_FACTOR_MS_OZ_PRESSURIZED
                length = len(liquidType)
                conn.sendall(str(length+14) + ' Dispensing ' + liquidType)
                activateOutput(io_board=io_board, output=matchedLiquids[liquidId]['valve'], time_ms=time_ms)
                updateAmount(recipe_j, conn, amount, liquidId)
        except:
            print >> sys.stderr, '[INFO] Skipping Unmatched Liquid ' + liquidType + ' for Pressurized'

def dispenseVacuumIngredients(io_board, recipe_j, conn):
    for i in range (0, len(recipe_j['liquids'])):
        liquidId = recipe_j['liquids'][i]['id']['_id']
        liquidType = recipe_j['liquids'][i]['id']['type']
        try:
            if matchedLiquids[liquidId]['pressurized'] == False:
                amount = recipe_j['liquids'][i]['amount']
                time_ms=amount*FLOW_FACTOR_MS_OZ_UNPRESSURIZED
                length = len(liquidType)
                conn.sendall(str(length+14) + ' Dispensing ' + liquidType)
                activateOutput(io_board=io_board, output=matchedLiquids[liquidId]['valve'], time_ms=time_ms + TRAVEL_TIME_MS)
                updateAmount(recipe_j, conn, amount, liquidId)
        except:
            print >> sys.stderr, '[INFO] Skipping Unmatched Liquid ' + liquidType + ' for Vacuum'

def checkAmounts(recipe_j, conn):
    totalamount = 0
    amounts_ok = True

    for i in range(0, len(recipe_j['liquids'])):
        ingredient = recipe_j['liquids'][i]['id']
        length = len(ingredient['type'])
        amount = recipe_j['liquids'][i]['amount']
        try:
            amount_left = matchedLiquids[ingredient['_id']]['amount']
            if amount > amount_left:
                conn.sendall(str(length+15) + ' Not enough ' + str(ingredient['type']) + '!')
                amounts_ok = False
            else:
                totalamount = totalamount + amount
        except:
            print >> sys.stderr, '[INFO] Skipping Unmatched Liquid ' + ingredient['type'] + ' for Amount Check'
    if totalamount > MAX_DRINK_SIZE:
        conn.sendall('35 Recipe size exceeds max allowed!')
        amounts_ok = False
    return amounts_ok

def updateAmount(recipe_j, conn, amount, liquidId):
    new_amount = matchedLiquids[liquidId]['amount'] - amount
    body = {'valve':matchedLiquids[liquidId]['valve'], 'amount':new_amount}
    try:
        data = urllib.urlencode(body)
        request = urllib2.Request(BASE_API_HOST_URL + LIQUIDPOST_URL + STATION_ID, data)
        request.get_method = lambda: 'PUT'
        u = urllib2.urlopen(request)
    except:
        print >> sys.stderr, '[ERROR] Could Not Update Remote Ingredient Data'

def rinseCycle(io_board, time_ms):
    print >> sys.stderr, '[INFO] Beginning Rinse Cycle'
    pumpOnOff(io_board=io_board, mode="PRESSURIZE", on=True)
    #WAIT FOR TOP SWITCH ACTIVATION
    count = 0
    while GPIO.input(PUMP_TOP_SWITCH_GPIO):
        time.sleep(0.1)
        count = count + 1
        if count > PUMP_TIMEOUT_MS/100:
            pumpOnOff(io_board=io_board)
            time.sleep(CHAMBER_FALL_TIME_MS/1000.0)
            closeChamberValves()
            LED_pattern = 0
            return '08 ERROR'
    time.sleep(PUMP_EXTRA_MS/1000.0)
    pumpOnOff(io_board=io_board, mode="VACUUM", on=True)
    activateOutput(io_board=io_board, output=RINSE_TANK_VALVE, time_ms=time_ms)
    #PURGE INGREDIENTS SUPPLY LINE
    activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
    pumpOnOff(io_board=io_board)
    time.sleep(CHAMBER_FALL_TIME_MS/1000.0)
    closeChamberValves()

def parseRecipe(recipe_j):
    global matchedLiquids
    global garnishes
    global onHandLiquids
    matchedLiquids.clear()
    garnishes = []
    onHandLiquids.clear()

    for liquid in recipe_j['liquids']:
        for stationLiquid in station_j['connectedLiquids']:
            if (stationLiquid['id']['_id'] == liquid['id']['_id']
                    or stationLiquid['id']['type'] == liquid['id']['type'] and liquid['id']['subtype'] == "*Any"
                    or stationLiquid['id']['type'] == liquid['id']['type'] and stationLiquid['id']['subtype'] == liquid['id']['subtype'] and liquid['id']['brand'] == "*Any"):
                matchedLiquids[liquid['id']['_id']] = ({'valve':stationLiquid['valve'],
                                                        'amount':stationLiquid['amount'],
                                                        'pressurized':stationLiquid['pressurized'],
                                                        'id':stationLiquid['id']['_id']})
            else:
                for onHandLiquid in station_j['onHandLiquids']:
                    if (onHandLiquid['_id'] == liquid['id']['_id']
                            or onHandLiquid['type'] == liquid['id']['type'] and liquid['id']['subtype'] == "*Any"
                            or onHandLiquid['type'] == liquid['id']['type'] and onHandLiquid['subtype'] == liquid['id']['subtype'] and liquid['id']['brand'] == "*Any"):
                        onHandLiquids[liquid['id']['_id']] = ({'id':onHandLiquid['_id'],
                                                                'amount':liquid['amount'],
                                                                'type':onHandLiquid['type'],
                                                                'brand':onHandLiquid['brand'],
                                                                'subtype':onHandLiquid['subtype'],
                                                                'description':onHandLiquid['description']})
    garnishes = recipe_j['garnishes']



def makeDrink(io_board, recipe_j, conn):
    global LED_pattern
    print 'Drink Ordered: ' + recipe_j['name']
    try:
        pullStationData()
    except:
        print >> sys.stderr, '[ERROR] Could Not Retrieve Station Data'
        conn.sendall("45 Controller Could Not Retrieve Station Data")
        return '08 ERROR'
    try:
        parseRecipe(recipe_j)
    except:
        print >> sys.stderr, '[ERROR] Could Not Match Station Liquids To Recipe'
        conn.sendall("55 Controller Could Not Match Station Liquids To Recipe")
        raise
        return '08 ERROR'
    if checkAmounts(recipe_j, conn):
        LED_pattern = 1
        # Make sure a glass is present
        if GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
            conn.sendall("38 Please Place Empty Glass on Station")
            count = 0
            while GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
                time.sleep(0.25)
                count = count + 1
                if count > DRINK_REMOVE_TIMEOUT_MS/100:
                    print >> sys.stderr, '[ERROR] Timeout waiting for glass placement'
                    conn.sendall("38 Timeout waiting for glass placement")
                    LED_pattern = 0
                    return '08 ERROR'
            time.sleep(0.75)
        print >> sys.stderr, '[INFO] Starting Pour, Raising Drink'
        conn.sendall("31 Starting Pour, Raising Drink")
        dispensePressurizedIngredients(io_board, recipe_j, conn)
        pumpOnOff(io_board=io_board, mode="PRESSURIZE", on=True)
        #WAIT FOR TOP SWITCH ACTIVATION
        count = 0
        while GPIO.input(PUMP_TOP_SWITCH_GPIO):
            time.sleep(0.25)
            count = count + 1
            if count > PUMP_TIMEOUT_MS/250:
                print >> sys.stderr, '[ERROR] Timeout waiting for chamber to rise'
                conn.sendall("38 Timeout waiting for chamber to rise")
                pumpOnOff(io_board=io_board)
                time.sleep(CHAMBER_FALL_TIME_MS/1000.0)
                closeChamberValves()
                LED_pattern = 0
                return '08 ERROR'
        time.sleep(PUMP_EXTRA_MS/1000.0)
        pumpOnOff(io_board=io_board, mode="VACUUM", on=True)
        dispenseVacuumIngredients(io_board, recipe_j, conn)
        #PURGE INGREDIENTS SUPPLY LINE
        activateOutput(io_board=io_board, output=AIR_PURGE_VALVE, time_ms=LINE_PURGE_TIME_MS)
        print >> sys.stderr, '[INFO] Pour Complete, Lowering Drink'
        conn.sendall("32 Pour Complete, Lowering Drink")
        #SEND PROMPT TO ADD NOT-CONNECTED ITEMS
        for liquid in onHandLiquids:
            length = len(str(onHandLiquids[liquid]['amount'])) + len(onHandLiquids[liquid]['brand']) + len(onHandLiquids[liquid]['type'])
            conn.sendall(str(length + 16)+' Add ' + str(onHandLiquids[liquid]['amount']) + ' oz. of ' + onHandLiquids[liquid]['brand'] + ' ' + onHandLiquids[liquid]['type'])
        for i in range(0, len(garnishes)):
            length = len(garnishes[i]['amount']) + len(garnishes[i]['name'])
            conn.sendall(str(length + 11)+' Add ' + garnishes[i]['amount'] + ' of ' + garnishes[i]['name'])
        #TURN OFF PUMP AND RELEASE PRESSURE IN CHAMBER
        pumpOnOff(io_board)
        #WAIT A MINIMUM AMOUNT OF 4 SECs TIME BEFORE CHECKING FOR GLASS REMOVAL
        time.sleep(4)
        #WAIT FOR BOTTOM SWITCH RELEASE (Drink Removal)
        while not GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
            time.sleep(0.25)
            count = count + 1
            if count > CHAMBER_FALL_TIME_MS/250:
                break
        closeChamberValves()
        while not GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
            time.sleep(0.25)
            count = count + 1
            if count > DRINK_REMOVE_TIMEOUT_MS/100:
                print >> sys.stderr, '[ERROR] Timeout waiting for drink removal'
                conn.sendall("36 Timeout waiting for drink removal")
                LED_pattern = 0
                return '08 ERROR'
        time.sleep(0.75)
        #RINSE THE CHAMBER
        conn.sendall("24 Beginning Rinse Cycle")
        rinseCycle(io_board=io_board, time_ms=RINSE_FILL_TIME_MS)
        LED_pattern = 0
        print >> sys.stderr, '[INFO] Rinse Complete, Station Ready'
        conn.sendall("32 Rinse Complete, Station Ready")
        return '07 DONE'
    else:
        LED_pattern = 0
        return '08 ERROR'

def pullStationData():
    global station_j
    req = urllib2.Request(BASE_API_HOST_URL + STATIONQUERY_URL + STATION_ID)
    response = urllib2.urlopen(req)
    station_j = json.load(response)

def reset(io_board):
    global lock
    global LED_pattern
    lock = False
    LED_pattern = 0
    setupOutputs(io_board)
    try:
        pullStationData()
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
        try:
            url_response = urllib2.urlopen(req)
            recipe_j = json.load(url_response)
            return makeDrink(io_board, recipe_j, conn)
        except:
            print >> sys.stderr, '[ERROR] Could Not Retrieve Recipe Data'
            raise
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
        cfgfile = open('/home/pi/controller/config.ini','w')
        parser.set('API', 'station_id', data)
        parser.write(cfgfile)
        cfgfile.close()
        return '07 DONE'
    elif cmd == '07': #Fill Full Rinse
        conn.sendall("22 Received Command " + cmd)
        fillRinse(io_board, RINSE_FILL_TIME_MS)
        return '07 DONE'
    elif cmd == '08': #
        conn.sendall("22 Received Command " + cmd)

        return '07 DONE'
    elif cmd == '09': #
        conn.sendall("22 Received Command " + cmd)

        return '07 DONE'
    elif cmd == '10': #
        conn.sendall("22 Received Command " + cmd)

        return '07 DONE'
    elif cmd == '11': #Pull Station Data from Database
        conn.sendall("22 Received Command " + cmd)
        pullStationData()
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
        print '[INFO] Received Command: "%s"' % cmd
        if int(cmd) >= 1 and int(cmd) <= 6:
            data = conn.recv(33)
            data = data[1:33]
            print '[INFO] Received Data: "%s"' % data
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
        raise
    finally:
        conn.close()
        lock = False
        threads.remove(threading.current_thread())

def buttonWorker():
    global lock
    buttonWasPressed = False
    try:
        while not stop:
            if not lock or buttonWasPressed:
                if not GPIO.input(BUTTON_SWITCH_GPIO):
                    #button is pressed, make sure glass is present
                    print "Button Pressed!"
                    if not GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
                        #glass is present, set lock, activate the appropriate valve
                        lock = True
                        buttonWasPressed = True
                        activateOutput(io_board=io_board, output=MANUAL_BUTTON_VALVE, on=True)
                        #wait for button release
                        count = 0
                        while not GPIO.input(BUTTON_SWITCH_GPIO):
                            time.sleep(0.25)
                            if count > 240: #60000/250:
                                print >> sys.stderr, '[ERROR] Timeout waiting for button relase'
                                break
                        print "Button Released"
                        activateOutput(io_board=io_board, output=MANUAL_BUTTON_VALVE, on=False)
                    else:
                        #button was pressed but no glass present, ignore
                        time.sleep(2)
                else:
                    if buttonWasPressed == True:
                        #button was pressed, wait for glass removal then rinse
                        count = 0
                        while not GPIO.input(PUMP_BOTTOM_SWITCH_GPIO):
                            time.sleep(0.25)
                            count = count + 1
                            if count > DRINK_REMOVE_TIMEOUT_MS/250:
                                print >> sys.stderr, '[ERROR] Timeout waiting for drink removal'
                                break
                            elif not GPIO.input(BUTTON_SWITCH_GPIO):
                                activateOutput(io_board=io_board, output=MANUAL_BUTTON_VALVE, on=True)
                                #wait for button release
                                count = 0
                                while not GPIO.input(BUTTON_SWITCH_GPIO):
                                    time.sleep(0.125)
                                    if count > 480: #60000/125:
                                        print >> sys.stderr, '[ERROR] Timeout waiting for button relase'
                                        break
                                print "Button Released"
                                activateOutput(io_board=io_board, output=MANUAL_BUTTON_VALVE, on=False)
                                count = 0
                        #Drink removed, wait a brief period
                        time.sleep(1)
                        #RINSE THE CHAMBER
                        rinseCycle(io_board=io_board, time_ms=RINSE_FILL_TIME_MS)
                        #we're done, remove lock
                        lock = False
                        buttonWasPressed = False
                    else:
                        #we're sitting idle
                        time.sleep(0.5)
            else:
                #we're locked out idle, no button was pressed
                time.sleep(0.5)
    except:
        raise



###############################################################################
#Main Program
###############################################################################
#GLOBAL DATA
io_board = {}
stop = False        #Flag to stop threads
lock = False        #Lock to decline further connections during a processing job
LED_pattern = 0     #Current Pattern For LEDs
station_j = {}      #Dictionary of retrieved station JSON data
matchedLiquids = {} #Dictionary of the specific station connected liquids to use, with key values of
                    #the generic recipe liquids id
garnishes = []      #List of garnishe objects to add after drink is made
onHandLiquids = {}  #Dictionary of not-connected liquids to add after drink is made
threads = []
maintainHeight = False    #If true, the maintainHeight thread will activate the pump if the top or bottom
                    #limit switches become unactivated due to any air leaks in the column

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
    try:
        # Start Maintain Height Thread to keep column at height during pour if it leaks air
        heightThread = threading.Thread(target=maintainHeightWorker)
        threads.append(heightThread)
        heightThread.start()
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup Maintain Height thread'
    try:
        # Start Button Thread to handle manual button pours
        buttonThread = threading.Thread(target=buttonWorker)
        threads.append(buttonThread)
        buttonThread.start()
    except:
        print >> sys.stderr, '[ERROR] Could Not Setup Maintain Height thread'
    print >> sys.stderr, '[INFO] Attempting To Pull Station Data from ' + BASE_API_HOST_URL + STATIONQUERY_URL
    try:
        STATION_ID = parser.get('API', 'station_id')
        STATION_AUTH = parser.get('API', 'station_auth')
        if STATION_ID == "": raise Exception("No Station ID configured. Please set using GUI")
        if STATION_AUTH == "": raise Exception("No Station Authorization configured. Please set using GUI")
    except Exception as e:
        print >> sys.stderr, '[WARNING] ' + e[0]
    try:
        pullStationData()
        print >> sys.stderr, '[INFO] Got Station data'
    except:
        print >> sys.stderr, '[ERROR] Unable to pull station data'
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, '[INFO] Starting Socket Server at ' + BIND_IP + ':' + str(BIND_PORT)
    try:
        s.bind((BIND_IP,BIND_PORT))
    except socket.error as msg:
        print >> sys.stderr, '[ERROR] Bind failed. Error Code: ' + str(msg[0]) + ' Message: ' + msg[1]

    s.listen(5)
    print ('***** Press Ctrl-C To Quit *****')
    while not stop:
        print >> sys.stderr, '[INFO] TOB Waiting For Connection'
        try:
            conn, addr = s.accept()
            print >> sys.stderr, '[INFO] TOB Client Connected:', addr
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
    GPIO.cleanup()
    print '\r\nGoodbye!\r\n'
