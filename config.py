# LED strip configuration:
LED_COUNT      = 16      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)

#Connection Information For Database API
#This should point to the server hosting the GUI interface, which provides the API to the database
BIND_IP = '192.168.0.5'
BIND_PORT = 1000

API_HOST = 'interface-dwaq.c9users.io:443'
BASE_API_HOST_URL = 'https://interface-dwaq.c9users.io'

RECIPE_URL = '/api/drinks/'
USERQUERY_URL = '/api/users/'
STATIONQUERY_URL = '/api/station/'
STATIONPOST_URL = '/api/station/ingredient/'
STATION_ID = '56a2be2d5d08dd13939871de'
STATION_AUTH = ''

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
