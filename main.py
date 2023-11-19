import machine
import network
import socket
import ure
import gc
import ntptime
import time

from machine import RTC, SoftI2C, Pin, Timer
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

# --- RTC Time with LCD Display ---
# Set your timezone offset (in seconds) from UTC
TIMEZONE_OFFSET = 1 * 3600  # UTC+1

# Synchronize time with NTP server
ntptime.settime()
rtc = RTC()

# Get the current time in UTC
(year, month, day, weekday, hours, minutes, seconds, subseconds) = rtc.datetime()

# Adjust the time to the specified timezone
sec = time.mktime((year, month, day, hours, minutes, seconds, 0, 0))
sec += TIMEZONE_OFFSET
(year, month, day, hours, minutes, seconds, weekday, yearday) = time.localtime(sec)

# Set the adjusted time to the RTC
rtc.datetime((year, month, day, weekday, hours, minutes, seconds, 0))

# Initialize LCD
I2C_ADDR = 0x27
totalRows = 2
totalColumns = 16
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=10000)
lcd = I2cLcd(i2c, I2C_ADDR, totalRows, totalColumns)

def update_lcd(timer):
    # Get the current time and date
    (year, month, day, weekday, hours, minutes, seconds, subseconds) = rtc.datetime()

    # Format the time and date as strings
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    date_str = "{:04d}-{:02d}-{:02d}".format(year, month, day)

    # Move to the appropriate positions on the display and update the time and date
    lcd.move_to(0, 0)
    lcd.putstr(time_str)
    lcd.move_to(0, 1)
    lcd.putstr(date_str)

# Set up a timer to update the LCD every second
lcd_timer = Timer(0)
lcd_timer.init(period=1000, mode=Timer.PERIODIC, callback=update_lcd)

# ---Set up PWM for LED and Initialize pin sensor ---
pwms = [machine.PWM(machine.Pin(pin), freq=500, duty=0) for pin in led_pins]


# ---Set up relay pins ---
relay_pins = [machine.Pin(pin, machine.Pin.OUT) for pin in relay_pins]

relay1_pin, relay2_pin, relay3_pin, relay4_pin = relay_pins

def toggle_all_relays():
    global relay1_state, relay2_state, relay3_state, relay4_state
    for relay_pin in relay_pins:
        relay_pin.on() if relay_pin.value() == 0 else relay_pin.off()

    relay1_state = "ON" if relay1_pin.value() == 1 else "OFF"
    relay2_state = "ON" if relay2_pin.value() == 1 else "OFF"
    relay3_state = "ON" if relay3_pin.value() == 1 else "OFF"
    relay4_state = "ON" if relay4_pin.value() == 1 else "OFF"

def read_html_file(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except Exception as e:
        print('Error reading HTML file:', e)
        return ''
    
def handle_request(s, relay1_pin, relay2_pin, relay3_pin, relay4_pin, pwms):
    relay1_state = "OFF"
    relay2_state = "OFF"
    relay3_state = "OFF"
    relay4_state = "OFF"

    try:
        if gc.mem_free() < 102000: #Checks if the free memory is less than 102000 and if so, triggers a garbage collection to free up memory.
            gc.collect() 

        conn, addr = s.accept() #Accepts a new connection on the socket s. conn is a new socket object representing the connection, and addr is the address of the client.
        # conn.settimeout(3.0)
        # print('Received HTTP GET connection request from %s' % str(addr))
        request = conn.recv(1024) #Receives data (up to 1024 bytes) from the client and stores it in the variable request.
        conn.settimeout(None) #Resets the timeout on the connection to None, effectively disabling the timeout.
        request = str(request) #Converts the received data to a string.
        # print('GET Rquest Content = %s' % request)

    
        relay_on = request.find('/?relay_13_on')
        relay_off = request.find('/?relay_13_off')
        if relay_on == 6:
            print('Relay1 ON -> GPIO13')
            relay1_state = "ON"
            relay1_pin.on()
        if relay_off == 6:
            print('Relay1 OFF -> GPIO13')
            relay1_state = "OFF"
            relay1_pin.off()

        relay2_on = request.find('/?relay_14_on')
        relay2_off = request.find('/?relay_14_off')
        if relay2_on == 6:
            print('Relay2 ON -> GPIO14')
            relay2_state = "ON"
            relay2_pin.on()
        if relay2_off == 6:
            print('Relay2 OFF -> GPIO14')
            relay2_state = "OFF"
            relay2_pin.off()

        relay3_on = request.find('/?relay_26_on')
        relay3_off = request.find('/?relay_26_off')
        if relay3_on == 6:
            print('Relay3 ON -> GPIO26')
            relay3_state = "ON"
            relay3_pin.on()
        if relay3_off == 6:
            print('Relay3 OFF -> GPIO26')
            relay3_state = "OFF"
            relay3_pin.off()

        relay4_on = request.find('/?relay_27_on')
        relay4_off = request.find('/?relay_27_off')
        if relay4_on == 6:
            print('Relay4 ON -> GPIO27')
            relay4_state = "ON"
            relay4_pin.on()
        if relay4_off == 6:
            print('Relay4 OFF -> GPIO27')
            relay4_state = "OFF"
            relay4_pin.off()

         # --- Handle toggle_all_relays request ---
        toggle_all_relays_request = request.find('/?toggle_all_relays')
        if toggle_all_relays_request == 6:
            toggle_all_relays()

        # --- Handle brightness control request ---
        match_brightness = ure.search("GET /set_brightness\?value=(\d+)", request)
        if match_brightness:
            brightness_value = int(match_brightness.group(1))
            for pwm in pwms:
                pwm.duty(brightness_value)

        # --- Handle individual LED control request ---
        match_led = ure.search("GET /set_led\?led=(\d+)&value=(\d+)", request)
        if match_led:
            led = int(match_led.group(1)) - 1
            led_value = int(match_led.group(2))
            pwms[led].duty(led_value)

       
        html_content_led = read_html_file('testt.html')
        html_content_brightness = read_html_file('testt1.html')
       
        if 'testt1.html' in request:
            html_content = html_content_brightness
        else:
        # --- To send HTML documents to a socket client in response to a request, 
        # create a response variable and provide the reference of the web_page function to the response variable. ---
            html_content = html_content_led.replace('{{relay1_state}}', relay1_state) \
                                .replace('{{relay2_state}}', relay2_state) \
                                .replace('{{relay3_state}}', relay3_state) \
                                .replace('{{relay4_state}}', relay4_state)

        # --- At the end send the web page content to a socket client using the 
        # send() and sendall() methods and close the connection using close method. ---
        conn.send('HTTP/1.1 200 OK\n') #Sends HTTP headers to the client indicating a successful response and the content type.
        conn.send('Content-Type: text/html\n')
        conn.send('Connection: close\n\n')
        conn.sendall(html_content) #Sends the content of the html_content variable to the client.
        conn.close()

    except OSError as e:
        #Catches an OSError exception, closes the connection, and prints a message indicating that the connection has been closed. 
        # This is useful for handling errors that may occur during the execution of the code inside the try block.
        conn.close()
        print('Connection closed')
        

# Inicjalizacja czujnika PIR
pir_pin = machine.Pin(25, machine.Pin.IN)  # Załóżmy, że czujnik PIR jest podłączony do pinu GPIO12

def detect_motion():
    if pir_pin.value() == 1:
        print("Motion Detected!")
    else:
        print("Motion NoT Detected!")

# ---Create a socket and start the server ---
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 80))
s.listen(5)

print('Listening on port 80...')

while True:
    handle_request(s, relay1_pin, relay2_pin, relay3_pin, relay4_pin, pwms)
    #detect_motion()
    #asdasdsddsa
    #adasdasd