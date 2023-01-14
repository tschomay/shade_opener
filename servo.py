

# Servo Control


import sys
# GPIO setting require sudo, but wiringpi is only in user directory
# Quick hack to resolve the path
sys.path.append('/home/pi/.local/lib/python3.7/site-packages')

import time
import wiringpi
import RPi.GPIO as GPIO
from datetime import datetime, timezone, timedelta
from astral import LocationInfo
from astral.sun import sun




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
        for pulse in range(self.state, self.r_max, 1):
            wiringpi.pwmWrite(self.gpio_pin, pulse)
            self.state = pulse
            time.sleep(self.delay)
            
        
    def s_close(self):
        '''
        Set servo to full closed position
        '''
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
        print('Button Press')
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
    #GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Set initial val off
    
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
    s = Servo()
    b = Button(servo=s)
    
    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING, callback=b.button_press, bouncetime=5000)
    city = LocationInfo("Durham", "NC", "New York", 35.9, -79.0)
    # Move back and forth
    try:
        while True:
            #GPIO.wait_for_edge(BUTTON_PIN, GPIO.RISING)
            #b.button_press(BUTTON_PIN)
            #time.sleep(1)
            
            # need to set obersvation date. Could make it tomor
            current_time = datetime.now(timezone.utc)
            s = sun(city.observer, date=current_time)
            
            dawn = s['dawn']
            dusk = s['dusk']
            if current_time < dawn:
                # open at dawn
                delay = (s['dawn'] - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                s.s_open() 
            elif (current_time > dawn) & (current_time < dusk):
                # Close at dusk
                delay = (s['dusk'] - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                s.s_close()
            elif current_time > dusk:
                # Open at dawn tomorrow
                delay = (s['dawn'] + datetime.timedelta(days=1) - datetime.now(timezone.utc)).total_seconds()
                time.sleep(delay)
                s.s_open()
            
            # Make sure clocks align
    except KeyboardInterrupt:
        GPIO.cleanup()
    finally:
        print('Cleaning up')
        GPIO.cleanup()
        

if __name__ == "__main__":
    main()