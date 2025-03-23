# ScentConnect: Bringing Love Closer Through Scent  

## Overview  
Long-distance relationships come with unique challenges—missing your partner’s presence, longing for shared moments, and feeling the void of physical closeness. While technology enables visual and auditory communication, the sense of smell remains neglected.  

**ScentConnect** bridges this gap by allowing partners to send each other comforting scents in real-time. Using motion detection and wireless communication, this smart fragrance dispenser enhances emotional connection beyond screens.  

## How It Works  
ScentConnect consists of two identical devices, each with:  
- **Motion Detection**: Detects movement and triggers a signal to the partner's device.  
- **Scent Activation**: Dispenses a predefined scent when movement is detected.  
- **LED Feedback System**:  
  - **White**: Motion detected.  
  - **Green**: Signal successfully sent.  
  - **Red**: Error in scent dispersal.  
  - **Partner’s Color (e.g., Blue/Purple)**: Scent successfully released.  

## Hardware Components  
We built ScentConnect using the following components:  
- **Raspberry Pi Pico W** (for Wi-Fi communication)  
- **HC-SR04 Distance Sensor** (to detect movement)  
- **L293D Motor Driver** (to control the scent dispenser)  
- **DC Motor** (reverse-engineered from a battery-operated air freshener)  
- **RGB LED** (to indicate system states)  
- **Red LED** (indicates device power status)  
- **Switch** (to turn the device on/off)  

## Reverse Engineering Air Fresheners  
ScentConnect was developed by reverse-engineering a commercial air freshener that operates on a timed interval. The circuit and logic behind its motor operation were analyzed and adapted to allow wireless, motion-triggered scent release. This approach also enables possible integration with **smart home systems**.  

## Software Overview  
The software consists of two main scripts:  

### `access_point.py` (Pico A)  

### `station.py` (Pico B)  

### Communication Mechanism  
The devices communicate via **UDP broadcasting** on a local Wi-Fi network

## Circuit and Concept Visualization  
- **[Circuit Diagram](circuit.png)** - Shows the hardware connections.  
- **[Concept Illustration](concept.png)** - Visual representation of how the system works.  

## Installation & Setup  
1. **Flash the firmware** onto both Raspberry Pi Pico W devices.  
2. **Upload `access_point.py` to Pico A** (acts as the Wi-Fi host).  
3. **Upload `station.py` to Pico B** (connects as a client).  
4. **Assemble hardware** as per the circuit diagram.  
5. **Power the devices on** and enjoy the scent-triggered connection!  

## Project Details  
- **University Project**: WS 24/25  
- **WordPress Blog**: [ScentConnect – Bringing Love Closer Through Scent](https://blockpraktikumexperiencedesign.wordpress.com/2025/03/14/scentconnect-bringing-love-closer-through-scent/)  

## License  
This project is open-source. Feel free to modify and extend it!  

---

Enjoy a new dimension of emotional connection with **ScentConnect**! 🌸💙
