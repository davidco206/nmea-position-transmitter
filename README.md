# NMEA Position Transmitter (QT Py + MAX3485)

Broadcasts a fixed GPS position as NMEA 0183 over RS-485 for a marine VHF radio.

## Hardware
- Adafruit QT Py (CircuitPython)
- MAX3485 RS-485 transceiver
- Marine VHF with NMEA 0183 input

## Wiring (typical)
- QT Py TX -> MAX3485 DI
- QT Py RX -> MAX3485 RO (optional)
- QT Py GPIO -> MAX3485 DE + RE (tied together) *(optional but recommended)*
- MAX3485 A/B -> Radio NMEA 0183 input (verify polarity)
- Shared GND

## Configure
Edit [code.py](code.py) to set:
- `LATITUDE`, `LONGITUDE`
- `START_DATE_DDMMYY`, `START_TIME_HHMMSS`
- `TX_PIN`, `RX_PIN`, `DE_RE_PIN` (match your QT Py variant and wiring)

NMEA defaults: 4800 baud, 1 Hz, 8N1.

## Notes
- If you don’t wire `DE_RE_PIN`, the MAX3485 must be permanently enabled.
- Some radios expect NMEA 0183 at 5V. Ensure proper level compatibility.
- This sends `$GPGGA` and `$GPRMC` sentences.
