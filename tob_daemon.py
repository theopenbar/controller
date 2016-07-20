#Python Server Daomon to run The Open Bar Control Board and Neo Pixel

import sys
import socket
import time

from Adafruit_GPIO import MCP230xx

from neopixel import *
from thread import *

# LED strip configuration:
LED_COUNT      = 16      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = True   # True to invert the signal (when using NPN transistor level shift)


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


###############################################################################
###############################################################################

DRAIN_TIME_MS = 1000
RINSE_FILL_TIME_MS = 100
RINSE_DRAIN_TIME_MS = 1000
LINE_PURGE_TIME_MS =300

NUM_INGREDIENTS = 18
MAX_POUR = 8 #oz

PRESSURE_RELEASE_PIN = 2
VAC_SOURCE_CHAMBER_PIN = 3
VAC_SOURCE_DRAIN_PIN = 4
DRAIN_PIN = 5
RINSE_TANK_PIN = 6
AIR_PURGE_PIN = 7


mcp1 = MCP230xx.MCP23008(address=0x20)
mcp2 = MCP230xx.MCP23008(address=0x21)
mcp3 = MCP230xx.MCP23008(address=0x22)
mcp4 = MCP230xx.MCP23008(address=0x23)

mcp1.write_gpio(0x00)
mcp2.write_gpio(0x00)
mcp3.write_gpio(0x00)
mcp4.write_gpio(0x00)

mcp1.write_gppu(0xFF)
mcp2.write_gppu(0xFF)
mcp3.write_gppu(0xFF)
mcp4.write_gppu(0xFF)

mcp1.write_iodir(0x00)
mcp2.write_iodir(0x00)
mcp3.write_iodir(0x00)
mcp4.write_iodir(0x00)


def dispense_ingredient(ingredient_num, amount):
    if ingredient_num <= NUM_INGREDIENTS & amount > 0 & amount <= MAX_POUR:
        valve = ingredient_num - 1
        time_ms=amount*flow_factor[valve]
        if valve >=0 & valve <8:
            pin = valve
            mcp1.output(pin,GPIO.HIGH)
            time.sleep(time_ms/1000.0)
            mcp1.output(pin,GPIO.LOW)
        elif valve >=8 & valve <16:
            pin = valve-8
            mcp2.output(pin,GPIO.HIGH)
            time.sleep(time_ms/1000.0)
            mcp1.output(pin,GPIO.LOW)
        elif valve >=16 & valve <24:
            pin = valve-16
            mcp3.output(pine,GPIO.HIGH)
            time.sleep(time_ms/1000.0)
            mcp1.output(pin,GPIO.LOW)
        elif valve >=24 & valve <32:
            pin = valve-24
            mcp4.output(pin,GPIO.HIGH)
            time.sleep(time_ms/1000.0)
            mcp1.output(pin,GPIO.LOW)

def vac_onoff(on, vac_source):
    if on:
        if vac_source == "CHAMBER":
            mcp4.output(PUMP_PIN, GPIO.HIGH)
            mcp4.output(VAC_SOURCE_CHAMBER_PIN, GPIO.HIGH)
            mcp4.output(VAC_SOURCE_DRAIN_PIN, GPIO.LOW)
        elif vac_source == "DRAIN":
            mcp4.output(PUMP_PIN, GPIO.HIGH)
            mcp4.output(VAC_SOURCE_CHAMBER_PIN, GPIO.LOW)
            mcp4.output(VAC_SOURCE_DRAIN_PIN, GPIO.HIGH)
	else:
            mcp4.output(PUMP_PIN, GPIO.LOW)
            mcp4.output(VAC_SOURCE_CHAMBER_PIN, GPIO.LOW)
            mcp4.output(VAC_SOURCE_DRAIN_PIN, GPIO.LOW)
    else:
        mcp4.output(PUMP_PIN, GPIO.LOW)
        mcp4.output(VAC_SOURCE_CHAMBER_PIN, GPIO.LOW)
        mcp4.output(VAC_SOURCE_DRAIN_PIN, GPIO.LOW)


#def dispense_pressurized_ingredients(drink):
    #get pressurized ingredients

    #dispense each ingredient for required amount



#def dispense_vacuum_ingredients(drink):
    #get vaccuum ingredients

    #dispense each ingredient for required amount


def purge_line():
    mcp4.output(AIR_PURGE_PIN, GPIO.HIGH)
    time.sleep(LINE_PURGE_TIME_MS/1000.0)
    mcp4.output(AIR_PURGE_PIN, GPIO.LOW)

def drain_drink():
    mcp4.output(PRESSURE_RELEASE_PIN, GPIO.HIGH)
    mcp4.output(DRAIN_PIN, GPIO.HIGH)
    time.sleep(DRAIN_TIME_MS/1000.0)
    mcp4.output(DRAIN_PIN, GPIO.LOW)
    mcp4.output(PRESSURE_RELEASE_PIN, GPIO.LOW)

def fill_rinse():
    vac_onoff(True, "CHAMBER")
    mcp4.output(RINSE_TANK_PIN,GPIO.HIGH)
    time.sleep(RINSE_FILL_TIME_MS/1000.0)
    mcp4.output(RINSE_TANK_PIN,GPIO.LOW)
    vac_onoff()

def drain_rinse():
    mcp4.output(PRESSURE_RELEASE_PIN, GPIO.HIGH)
    vac_onoff(True, "DRAIN")
    time.sleep(RINSE_DRAIN_TIME_MS/1000.0)
    vac_onoff()
    mcp4.output(PRESSURE_RELEASE_PIN, GPIO.LOW)

def pourdrink(drink):
    vac_onoff(True, "CHAMBER")
    dispense_pressurized_ingredients(drink)
    dispense_vacuum_ingredients(drink)
    purge_line
    vac_onoff()
    drain_drink()

def clientthread(conn):
    try:
	conn.send('Welcome to the server. Type something and hit enter\n')
	print >> sys.stderr, 'TOB client connected:', addr
	while True:
            data = conn.recv(16)
            print 'Received: "%s"' % data
            if data:
                conn.sendall(data)
            else:
                break
    finally:
        conn.close()

# Main program logic follows:
if __name__ == '__main__':
    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print >> sys.stderr, 'Starting Server on localhost port 1000'

    try:
        s.bind(('192.168.0.5',1000))
    except socket.error as msg:
        print >> sys.stderr, 'Bind failed. Error Code : ' + str(msg[0]) + ' Message: ' + msg[1]
        sys.exit

    s.listen(5)

    print ('Press Ctrl-C to quit.')
    while True:
        print >> sys.stderr, 'TOB waiting for connection'
        conn, addr = s.accept()
        start_new_thread(clientthread,(conn,))


    s.close()
		# Color wipe animations.
"""		colorWipe(strip, Color(255, 0, 0))  # Red wipe
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
"""
