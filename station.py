from machine import Pin, PWM
import network
import socket
import time

# Helper function to compute broadcast address from an IP string
def get_broadcast_addr(ip):
    parts = ip.split('.')
    return "{}.{}.{}.255".format(parts[0], parts[1], parts[2])

# -----------------------
# Set up Station WiFi
sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.disconnect()  # Clear any previous connection state
time.sleep(1)

ssid = "Pico-Wlan"
password = "12345678"

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
# Main loop for Pico B
while True:
    # Update device_on based on the button state
    if button.value() == 0:
        device_on = False
        red_led.value(1)
    else:
        device_on = True
        red_led.value(0)
    
    # Print state change if it has changed
    if device_on != prev_device_on:
        print("Pico B: Device switched to", "ON" if device_on else "OFF")
        prev_device_on = device_on

    # --- Connection management based on device state ---
    if device_on:
        if not sta.isconnected():
            print("Pico B: Device is ON and not connected. Attempting to connect to AP:", ssid)
            sta.connect(ssid, password)
            connection_start = time.time()
            while not sta.isconnected() and device_on and (time.time() - connection_start < 10):
                print("Pico B: Waiting for connection...")
                time.sleep(1)
            if sta.isconnected():
                sta_ip = sta.ifconfig()[0]
                broadcast_addr = get_broadcast_addr(sta_ip)
                print("Pico B: Connected! IP:", sta_ip, "Broadcast:", broadcast_addr)
            else:
                print("Pico B: Failed to connect within timeout.")
    else:
        if sta.isconnected():
            print("Pico B: Device is OFF, disconnecting from AP.")
            sta.disconnect()
    
    current_time = time.time()
    
    # Process incoming UDP messages
    try:
        data, addr = s.recvfrom(1024)
        if data:
            print("Pico B: Received '{}' from {}".format(data, addr))
            if data == b"B_trigger" or data == b"B_ack":
                pass  # Ignore messages from ourselves
            elif data == b"A_trigger":
                print("Pico B: Received trigger from Pico A")
                if device_on:
                    set_rgb_color(1, 0, 1)  # Pink (red+blue)
                    dcMotorTrigger()
                    time.sleep(2)
                    set_rgb_color(0, 0, 0)
                    s.sendto(b"B_ack", (broadcast_addr, udp_port))
                    print("Pico B: Sent B_ack to Pico A")
                else:
                    print("Pico B: Device is OFF. Ignoring trigger from Pico A.")
    except Exception:
        pass

    # Check own distance sensor if device is on and cooldown has passed
    if device_on and (current_time - last_trigger_time > trigger_cooldown):
        distance = get_distance()
        if distance < 50:
            print("Pico B: Distance trigger detected (Distance: {:.2f} cm)".format(distance))
            set_rgb_color(1, 1, 1)  # White
            time.sleep(2)
            set_rgb_color(0, 0, 0)
            s.sendto(b"B_trigger", (broadcast_addr, udp_port))
            print("Pico B: Sent B_trigger to Pico A")
            ack_received = False
            ack_wait_start = time.time()
            while time.time() - ack_wait_start < 5:
                try:
                    data, addr = s.recvfrom(1024)
                    if data == b"A_ack":
                        ack_received = True
                        print("Pico B: Received A_ack from", addr)
                        break
                except Exception:
                    pass
            if ack_received:
                set_rgb_color(0, 1, 0)  # Green for success
                print("Pico B: Pico A acknowledged trigger. Lighting green.")
            else:
                set_rgb_color(1, 0, 0)  # Red for failure
                print("Pico B: No acknowledgment from Pico A. Lighting red.")
            time.sleep(2)
            set_rgb_color(0, 0, 0)
            last_trigger_time = time.time()
    
    time.sleep(0.1)