#!/usr/bin/env python3
"""
probe_ag1022_serial.py

Robust serial probe for AG1022/virtual-COM devices.
Tries all discovered ports, multiple baud rates and line terminators,
and toggles DTR/RTS to coax a reply. Looks for '*IDN?' responses
containing OWON/AG1022.

Usage:
  python probe_ag1022_serial.py
"""

import time
import serial
import serial.tools.list_ports

GOOD_KEYWORDS = ("OWON", "AG1022", "AG-1022", "AG1022F")

BAUDS = (115200, 9600, 19200, 38400)
TERMINATORS = ("\r\n", "\n", "\r")
TRY_TOGGLES = (False, True)  # toggling DTR/RTS off/on


def probe_port(dev):
    print("\n-- probing", dev.device, "--")
    print("  desc:", dev.description)
    print("  hwid:", dev.hwid)
    for baud in BAUDS:
        for dtr in TRY_TOGGLES:
            for rts in TRY_TOGGLES:
                try:
                    s = serial.Serial(dev.device, baudrate=baud, timeout=1)
                except Exception as e:
                    # can't open at that baud -> try next
                    # print(" open failed:", e)
                    continue
                try:
                    s.dtr = dtr
                    s.rts = rts
                    # small settle after toggle
                    time.sleep(0.08)
                    for term in TERMINATORS:
                        try:
                            s.reset_input_buffer()
                            s.reset_output_buffer()
                            cmd = "*IDN?" + term
                            s.write(cmd.encode("ascii", errors="ignore"))
                            # try multiple short reads to accumulate data
                            data = b""
                            for _ in range(6):
                                time.sleep(0.08)
                                data += s.read(256)
                                if data:
                                    break
                            resp = data.decode(errors="ignore").strip()
                            if resp:
                                print(
                                    f"  -> reply on {dev.device}@{baud} (dtr={dtr},rts={rts},term={repr(term)}):"
                                )
                                print("     ", repr(resp))
                                # check keywords
                                if any(k in resp.upper() for k in GOOD_KEYWORDS):
                                    print(
                                        "     **** Looks like AG1022/OWON (keyword matched) ****"
                                    )
                                    s.close()
                                    return True, (
                                        dev.device,
                                        baud,
                                        dtr,
                                        rts,
                                        term,
                                        resp,
                                    )
                                else:
                                    print(
                                        "     (reply received but vendor keywords not found)"
                                    )
                        except Exception:
                            pass
                finally:
                    try:
                        s.close()
                    except Exception:
                        pass
    return False, None


def main():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports detected.")
        return 2
    print("Detected serial ports:")
    for p in ports:
        print(" ", p.device, "-", p.description, "-", p.hwid)
    for p in ports:
        ok, info = probe_port(p)
        if ok:
            print("\nSUCCESS:", info)
            return 0

    print("\nNo instrument replied to *IDN? on any port.")
    print("Suggestions:")
    print(" - Try unplugging/replugging the device and re-run this script.")
    print(
        " - Close other apps that might be holding the COM port (Arduino IDE, serial monitors, PyVISA sessions)."
    )
    print(" - Try switching the cable/USB port (prefer a USB2.0 port).")
    return 1


if __name__ == "__main__":
    exit(main())
