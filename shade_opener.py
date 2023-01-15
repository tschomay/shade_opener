# Runs window shade control

import sys
import os
# GPIO setting require sudo, but wiringpi is only in user directory
# Quick hack to resolve the path
user = os.getlogin()
sys.path.append(f'/home/{user}/.local/lib/python3.7/site-packages')

import logging
import time
import wiringpi
import RPi.GPIO as GPIO
from datetime import datetime, timezone, timedelta
from astral import LocationInfo
from astral.sun import sun

# Setup Logger
log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'shade_opener.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %I:%M:%S%p')
logging.info('Program started')

class Servo:
    def __init__(self, delay=0.01, pin=18):
        self.r_min = 50  # Range minimum default 50
        self.r_max = 250  # Range maximum default 250
        self.state = self.r_max  # Placeholder for current state
        self.delay = delay
        self.gpio_pin = pin  # GPIO pin on rpi board
        
        
    def s_open(self):
        '''
        Set servo to full open position
        '''
        logging.debug('Opening')
        for pulse in range(self.state, self.r_max, 1):
            wiringpi.pwmWrite(self.gpio_pin, pulse)
            self.state = pulse
            time.sleep(self.delay)
            
        
    def s_close(self):
        '''
        Set servo to full closed position
        '''
        logging.debug('Closing')
        for pulse in range(self.state, self.r_min, -1):
            wiringpi.pwmWrite(self.gpio_pin, pulse)
            self.state = pulse
            time.sleep(self.delay)
        

class Button:
    def __init__(self, servo):
        self.servo = servo
        
        
    def button_press(self, channel):
        '''
        Move servo to other extreme on button press
        servo: object of the Servo class
        '''
        logging.debug('Button Press')
        midpoint = round((self.servo.r_max + self.servo.r_min) / 2)
        if self.servo.state > midpoint:
            self.servo.s_close()
        else:
            self.servo.s_open()
        
    
def main():
    # Set constants
    SERVO_PIN = 18  # PWM signal GPIO pin
    BUTTON_PIN = 24  # GPIO pin to detect button
    
    # Button Setup
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Set initial val off
    
    # Servo Setup
    # use 'GPIO naming'
    wiringpi.wiringPiSetupGpio()
    # set #18 to be a PWM output
    wiringpi.pinMode(SERVO_PIN, wiringpi.GPIO.PWM_OUTPUT)
    # set the PWM mode to milliseconds stype
    wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS)
    # divide down clock
    wiringpi.pwmSetClock(192)
    wiringpi.pwmSetRange(2000)
    
    # Instantiate the servo
    servo = Servo()
    b = Button(servo=servo)
    
    # Watch for button presses and act on them
    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=b.button_press, bouncetime=5000)
    
    # Automate open/close with sun
    city = LocationInfo("Durham", "NC", "New York", 35.9, -79.0)
    try:
        while True:
            current_time = datetime.now(timezone.utc)
            sun_data = sun(city.observer, date=current_time)
            
            open_time = sun_data['dawn']
            close_time = sun_data['dusk']
            if current_time < open_time:
                logging.info('Will open at dawn %s UTC' % open_time)
                delay = (open_time - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                servo.s_open() 
            elif (current_time > open_time) & (current_time < close_time):
                logging.info('Will close at dusk %s UTC' % close_time)
                delay = (close_time - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                servo.s_close()
            elif current_time > close_time:
                logging.info('Will open at dawn tomorrow %s UTC' % (open_time + datetime.timedelta(days=1)))
                delay = (open_time + datetime.timedelta(days=1) - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                servo.s_open()
            # Avoid immediate open/close events since next event time is projected
            time.sleep(300)
    except KeyboardInterrupt as e:
        GPIO.cleanup()
        logging.critical('Program ended by keyboard interrupt', exc_info=True)
    finally:
        GPIO.cleanup()
        logging.info('Program ended, cleaning up.', exc_info=True)
        

if __name__ == "__main__":
    main()