"""
hid_keyboard.py
===============
Minimal USB HID Keyboard driver for XIAO RP2040 (MicroPython).
Uses the built-in 'usb.device' API available in MicroPython >= 1.23 for RP2040.

If your MicroPython build does NOT have 'usb.device', use the
'pico-sdk' UF2 from: https://micropython.org/download/RPI_PICO/
"""

import usb.device
from usb.device.hid import KeyboardInterface

# ─── HID KEYCODES ─────────────────────────────────────────────────────────────
KEY_UP    = 0x52
KEY_DOWN  = 0x51
KEY_LEFT  = 0x50
KEY_RIGHT = 0x4F

class HIDKeyboard:
    def __init__(self):
        self._kb = KeyboardInterface()
        usb.device.get().init(self._kb, builtin_driver=True)

    def press(self, keycode):
        """Send key down then key up."""
        self._kb.send_keys([keycode])

    def release(self):
        """Release all keys."""
        self._kb.send_keys([])
