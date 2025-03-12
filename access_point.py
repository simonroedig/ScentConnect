from machine import Pin, PWM
import network
import socket
import time

# Helper function to compute broadcast address from an IP string
def get_broadcast_addr(ip):
    parts = ip.split('.')
    return "{}.{}.{}.255".format(parts[0], parts[1], parts[2])

# -----------------------
# Set up Access Point (Pico A)
ap = network.WLAN(network.AP_IF)
ap.active(True)
# Allow time for the AP to start up
time.sleep(2)
ssid = "Pico-Wlan"
password = "12345678"
ap.config(essid=ssid, password=password)
# Explicitly set a known IP configuration for the AP
ap.ifconfig(('192.168.4.1', '255.255.255.0', '192.168.4.1', '8.8.8.8'))
ap_ip = ap.ifconfig()[0]
broadcast_addr = get_broadcast_addr(ap_ip)
print("Pico A: AP started. SSID:", ssid)
print("Pico A: IP:", ap_ip, "Broadcast:", broadcast_addr)

device_id = "A"

# -----------------------
# Hardware setup

# DC Motor Pins
IN1_Pin = 17
IN2_Pin = 16  
ENA_Pin = 18 
in1 = Pin(IN1_Pin, Pin.OUT)
in2 = Pin(IN2_Pin, Pin.OUT)
pwm = PWM(Pin(ENA_Pin))
pwm.freq(1000)

# Distance sensor pins
echoPin = Pin(5, Pin.IN)
triggerPin = Pin(6, Pin.OUT)

# LED and button
red_led = Pin(10, Pin.OUT)
button = Pin(7, Pin.IN, Pin.PULL_UP)

# RGB LED pins
rgb_red = Pin(11, Pin.OUT)
rgb_green = Pin(12, Pin.OUT)
rgb_blue = Pin(13, Pin.OUT)

def set_rgb_color(r, g, b):
    rgb_red.value(r)
    rgb_green.value(g)
    rgb_blue.value(b)

def motor_run(speed, direction):
    if speed > 100:
        speed = 100
    if speed < 0:
        speed = 0
    pwm.duty_u16(int(speed / 100 * 65535))
    if direction > 0:
        in1.value(0)
        in2.value(1)
    elif direction < 0:
        in1.value(1)
        in2.value(0)
    else:
        in1.value(0)
        in2.value(0)

def get_distance():
    triggerPin.value(0)
    time.sleep_us(2)
    triggerPin.value(1)
    time.sleep_us(10)
    triggerPin.value(0)
    pulse_start = time.ticks_us()
    while echoPin.value() == 0:
        pulse_start = time.ticks_us()
    while echoPin.value() == 1:
        pulse_duration = time.ticks_us() - pulse_start
    distance = (pulse_duration * 0.0343) / 2
    return distance

def dcMotorTrigger():
    motor_run(100, -1)
    time.sleep(0.8)
    motor_run(100, 1)
    time.sleep(0.1)
    motor_run(0, 0)

# -----------------------
# Initial state variables
device_on = True
set_rgb_color(0, 0, 0)
red_led.value(0)
prev_device_on = device_on

# Setup UDP socket for communication on port 1234
udp_port = 1234
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.bind(('0.0.0.0', udp_port))
s.settimeout(0.2)

last_trigger_time = 0
trigger_cooldown = 5  # seconds

# -----------------------
# Main loop for Pico A
while True:
    # Continuously check the button state to update device_on
    if button.value() == 0:
        device_on = False
        red_led.value(1)
    else:
        device_on = True
        red_led.value(0)
        
    # Print state change if it has changed
    if device_on != prev_device_on:
        print("Pico A: Device switched to", "ON" if device_on else "OFF")
        prev_device_on = device_on

    current_time = time.time()
    
    # Process incoming UDP messages
    try:
        data, addr = s.recvfrom(1024)
        if data:
            print("Pico A: Received '{}' from {}".format(data, addr))
            if data == b"A_trigger" or data == b"A_ack":
                pass  # Ignore messages from ourselves
            elif data == b"B_trigger":
                print("Pico A: Received trigger from Pico B")
                if device_on:
                    set_rgb_color(0, 0, 1)  # Pink (red+blue)
                    dcMotorTrigger()
                    time.sleep(2)
                    set_rgb_color(0, 0, 0)  # Turn off RGB LED
                    s.sendto(b"A_ack", (broadcast_addr, udp_port))
                    print("Pico A: Sent A_ack to Pico B")
                else:
                    print("Pico A: Device is OFF. Ignoring trigger from Pico B.")
    except Exception:
        pass  # No message received

    # Check own distance sensor if device is on and cooldown has passed
    if device_on and (current_time - last_trigger_time > trigger_cooldown):
        distance = get_distance()
        if distance < 50:
            print("Pico A: Distance trigger detected (Distance: {:.2f} cm)".format(distance))
            set_rgb_color(1, 1, 1)  # White
            time.sleep(2)
            set_rgb_color(0, 0, 0)  # Turn off white LED
            s.sendto(b"A_trigger", (broadcast_addr, udp_port))
            print("Pico A: Sent A_trigger to Pico B")
            # Wait for acknowledgment up to 5 seconds
            ack_received = False
            ack_wait_start = time.time()
            while time.time() - ack_wait_start < 5:
                try:
                    data, addr = s.recvfrom(1024)
                    if data == b"B_ack":
                        ack_received = True
                        print("Pico A: Received B_ack from", addr)
                        break
                except Exception:
                    pass
            if ack_received:
                set_rgb_color(0, 1, 0)  # Green for success
                print("Pico A: Pico B acknowledged trigger. Lighting green.")
            else:
                set_rgb_color(1, 0, 0)  # Red for failure
                print("Pico A: No acknowledgment from Pico B. Lighting red.")
            time.sleep(2)
            set_rgb_color(0, 0, 0)  # Turn off LED after feedback
            last_trigger_time = time.time()
    
    time.sleep(0.1)