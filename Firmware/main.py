"""
Arrow Key Firmware for XIAO-RP2040-DIP
=======================================
Hardware:
  - PB1 → GPIO1  →  ↑ Up
  - PB2 → GPIO2  →  → Right
  - PB3 → GPIO3  →  ↓ Down
  - PB4 → GPIO4  →  ← Left
  - SK6812 LEDs  →  GPIO0 (2 chained)

Behavior:
  - Acts as a real USB HID keyboard (arrow keys)
  - Each arrow lights the LEDs a unique color while held
  - LEDs return to dim white on release
  - Supports key repeat while held (like a real keyboard)

Requirements:
  - MicroPython >= 1.23 for RP2040 (has usb.device built-in)
  - Copy both main.py and hid_keyboard.py to the board
"""

import time
from machine import Pin
from neopixel import NeoPixel
from hid_keyboard import HIDKeyboard, KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT

# ─── PIN CONFIGURATION ────────────────────────────────────────────────────────

BUTTON_MAP = {
    'UP':    {'pin': 1, 'keycode': KEY_UP,    'color': (0,   150, 255)},  # blue
    'RIGHT': {'pin': 2, 'keycode': KEY_RIGHT, 'color': (0,   255, 80)},   # green
    'DOWN':  {'pin': 3, 'keycode': KEY_DOWN,  'color': (255, 80,  0)},    # orange
    'LEFT':  {'pin': 4, 'keycode': KEY_LEFT,  'color': (200, 0,   255)},  # purple
}

LED_PIN  = 0
NUM_LEDS = 2

IDLE_COLOR   = (5, 5, 5)    # dim white at rest
DEBOUNCE_MS  = 20           # ms before registering press
REPEAT_DELAY = 400          # ms before key repeat starts
REPEAT_RATE  = 80           # ms between repeated keypresses

# ─── SETUP ────────────────────────────────────────────────────────────────────

# Buttons: input with pull-up (active LOW — press connects to GND)
buttons = {
    name: Pin(cfg['pin'], Pin.IN, Pin.PULL_UP)
    for name, cfg in BUTTON_MAP.items()
}

# SK6812 LEDs
np = NeoPixel(Pin(LED_PIN), NUM_LEDS)

def set_leds(color):
    for i in range(NUM_LEDS):
        np[i] = color
    np.write()

# HID keyboard
kbd = HIDKeyboard()

# ─── STATE TRACKING ───────────────────────────────────────────────────────────

state = {
    name: {'press_time': 0, 'last_repeat': 0}
    for name in BUTTON_MAP
}

# ─── STARTUP ──────────────────────────────────────────────────────────────────

set_leds(IDLE_COLOR)
print("Arrow key firmware ready.")

# Short boot delay so USB HID enumerates properly
time.sleep_ms(500)

# ─── MAIN LOOP ────────────────────────────────────────────────────────────────

current_key    = None
debounce_key   = None
debounce_start = 0

while True:
    now     = time.ticks_ms()
    raw_key = None

    # Scan buttons (simple direct read — not matrix, all individual pins)
    for name, btn in buttons.items():
        if btn.value() == 0:
            raw_key = name
            break  # one key at a time

    # ── Debounce ──────────────────────────────────────────────────────────────
    if raw_key != debounce_key:
        debounce_key   = raw_key
        debounce_start = now

    if time.ticks_diff(now, debounce_start) < DEBOUNCE_MS:
        time.sleep_ms(5)
        continue

    confirmed_key = debounce_key

    # ── Key just pressed ──────────────────────────────────────────────────────
    if confirmed_key and confirmed_key != current_key:
        # Release previous key if any
        if current_key:
            kbd.release()

        current_key = confirmed_key
        cfg = BUTTON_MAP[current_key]

        kbd.press(cfg['keycode'])
        set_leds(cfg['color'])
        print(f"Arrow: {current_key}")

        state[current_key]['press_time']  = now
        state[current_key]['last_repeat'] = now

    # ── Key held — handle repeat ───────────────────────────────────────────────
    elif confirmed_key and confirmed_key == current_key:
        s        = state[current_key]
        cfg      = BUTTON_MAP[current_key]
        held_for = time.ticks_diff(now, s['press_time'])

        if held_for > REPEAT_DELAY:
            if time.ticks_diff(now, s['last_repeat']) >= REPEAT_RATE:
                kbd.press(cfg['keycode'])
                s['last_repeat'] = now

    # ── Key released ──────────────────────────────────────────────────────────
    elif not confirmed_key and current_key:
        kbd.release()
        set_leds(IDLE_COLOR)
        current_key = None

    time.sleep_ms(5)
