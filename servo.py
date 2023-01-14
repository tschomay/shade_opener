

# Servo Control
import time
import wiringpi
import RPi.GPIO as GPIO



class Servo:
    def __init__(self, delay=0.01, pin=18):
        self.r_min = 50  # Range minimum
        self.r_max = 250  # Range maximum
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
        
        
    def button_press(self):
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
    
    # Move back and forth
    try:
        while True:
            GPIO.wait_for_edge(BUTTON_PIN, GPIO.FALLING)
            b.button_press()
            time.sleep(1)
    finally:
        print('Cleaning up')
        GPIO.cleanup()
        

if __name__ == "__main__":
    main()