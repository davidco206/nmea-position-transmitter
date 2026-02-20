# SPDX-FileCopyrightText: 2026
# SPDX-License-Identifier: MIT
"""
CircuitPython NMEA 0183 position broadcaster for Adafruit QT Py + MAX3485.

Wiring (typical):
- QT Py TX -> MAX3485 DI
- QT Py RX -> MAX3485 RO (optional, not used)
- QT Py GPIO (DE/RE) -> MAX3485 DE+RE (tied together)
- MAX3485 A/B -> NMEA 0183 input (verify polarity)
    - A is on Pin 6 (non-inverting) and B is on Pin 8 (inverting) of the MAX 34385
    - Stanbdard Horizon GX1700B: NMEA_IN+ is green, and NMEA_IN- is white 
"""

import time
import board
import busio
import digitalio

# ----------------------- USER CONFIG -----------------------
# Fixed position in decimal degrees
# Mowgli Island BC Dock: 48.972657, -123.610603
LATITUDE = 48.972657   # positive = N, negative = S
LONGITUDE = -123.610603  # positive = E, negative = W

# Fixed UTC date (DDMMYY) and start time (HHMMSS). Time will tick from this.
START_DATE_DDMMYY = "190226"
START_TIME_HHMMSS = "120000"

# NMEA settings
BAUDRATE = 4800
UPDATE_HZ = 1.0

# Pin assignments (adjust for your QT Py variant)
TX_PIN = board.TX
RX_PIN = board.RX  # not used, but required by UART on some ports
DE_RE_PIN = None  # e.g. board.D5 if you wired DE/RE to a GPIO
# -----------------------------------------------------------


def _to_nmea_latlon(value, is_lat=True):
    """Convert decimal degrees to NMEA ddmm.mmmm format + hemisphere."""
    hemi = "N" if is_lat else "E"
    if value < 0:
        hemi = "S" if is_lat else "W"
    abs_val = abs(value)
    degrees = int(abs_val)
    minutes = (abs_val - degrees) * 60.0
    if is_lat:
        return f"{degrees:02d}{minutes:07.4f}", hemi
    return f"{degrees:03d}{minutes:07.4f}", hemi


def _checksum(payload):
    csum = 0
    for ch in payload:
        csum ^= ord(ch)
    return f"{csum:02X}"


def _make_gpgga(utc_hhmmss, lat, lon):
    lat_str, lat_hemi = _to_nmea_latlon(lat, True)
    lon_str, lon_hemi = _to_nmea_latlon(lon, False)
    # Fix quality=1, satellites=08, HDOP=1.0, altitude=0.0 M
    payload = (
        f"GPGGA,{utc_hhmmss}.00,{lat_str},{lat_hemi},{lon_str},{lon_hemi},"
        "1,08,1.0,0.0,M,0.0,M,,"
    )
    return f"${payload}*{_checksum(payload)}\r\n"


def _make_gprmc(utc_hhmmss, date_ddmmyy, lat, lon):
    lat_str, lat_hemi = _to_nmea_latlon(lat, True)
    lon_str, lon_hemi = _to_nmea_latlon(lon, False)
    # Status=A (valid), speed=0.0 kn, course=0.0 deg
    payload = (
        f"GPRMC,{utc_hhmmss}.00,A,{lat_str},{lat_hemi},{lon_str},{lon_hemi},"
        "0.0,0.0,"
        f"{date_ddmmyy},,,A"
    )
    return f"${payload}*{_checksum(payload)}\r\n"


def _tick_time(start_hhmmss, seconds_elapsed):
    hh = int(start_hhmmss[0:2])
    mm = int(start_hhmmss[2:4])
    ss = int(start_hhmmss[4:6])
    total = hh * 3600 + mm * 60 + ss + int(seconds_elapsed)
    total %= 24 * 3600
    hh = total // 3600
    mm = (total % 3600) // 60
    ss = total % 60
    return f"{hh:02d}{mm:02d}{ss:02d}"


# UART setup
uart = busio.UART(TX_PIN, RX_PIN, baudrate=BAUDRATE, timeout=0.1)

# Optional DE/RE control for MAX3485
if DE_RE_PIN is not None:
    de_re = digitalio.DigitalInOut(DE_RE_PIN)
    de_re.direction = digitalio.Direction.OUTPUT
    de_re.value = False
else:
    de_re = None

start_time = time.monotonic()

while True:
    now = time.monotonic()
    utc_time = _tick_time(START_TIME_HHMMSS, now - start_time)

    gga = _make_gpgga(utc_time, LATITUDE, LONGITUDE)
    rmc = _make_gprmc(utc_time, START_DATE_DDMMYY, LATITUDE, LONGITUDE)

    if de_re is not None:
        de_re.value = True
        time.sleep(0.002)

    uart.write(gga.encode("ascii"))
    uart.write(rmc.encode("ascii"))

    if de_re is not None:
        time.sleep(0.002)
        de_re.value = False

    time.sleep(1.0 / UPDATE_HZ)
