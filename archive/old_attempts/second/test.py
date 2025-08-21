import pyvisa
from pyvisa import constants as vi


def open_owon_via_visa_asrl():
    rm = pyvisa.ResourceManager()
    resources = [r for r in rm.list_resources() if r.startswith("ASRL")]
    if not resources:
        raise RuntimeError("No ASRL resources found")

    for res in resources:
        inst = rm.open_resource(res)
        # ----- Serial (ASRL) parameters: 115200-8-N-1 -----
        inst.baud_rate = 115200
        inst.data_bits = 8
        inst.parity = vi.Parity.none
        inst.stop_bits = vi.StopBits.one
        # Line endings
        inst.write_termination = "\n"
        inst.read_termination = "\n"
        inst.timeout = 3000  # ms

        try:
            idn = inst.query("*IDN?")
            if "OWON" in idn.upper() and "AG" in idn.upper():
                print(f"Connected on {res}: {idn.strip()}")
                return inst
        except Exception as e:
            try:
                inst.close()
            except Exception:
                pass

    raise RuntimeError("OWON AG not found on ASRL ports")


if __name__ == "__main__":
    awg = open_owon_via_visa_asrl()  # <— THIS creates `awg`

    # Clean start
    awg.write("*RST")
    awg.write("*CLS")

    # CH1: Sine 1 kHz, 2 Vpp, 0 V offset
    awg.write(":SOUR1:FUNC SINE")
    awg.write(":SOUR1:FREQ 1000")
    awg.write(":SOUR1:VOLT 2")
    awg.write(":SOUR1:VOLT:OFFS 0")
    awg.write(":OUTP1 ON")

    # Read back + error check
    print("CH1 func:", awg.query(":SOUR1:FUNC?"))
    print("CH1 freq:", awg.query(":SOUR1:FREQ?"))
    print("CH1 vpp:", awg.query(":SOUR1:VOLT?"))
    print("CH1 offset:", awg.query(":SOUR1:VOLT:OFFS?"))
    print("Error:", awg.query(":SYST:ERR?"))

    awg.close()
