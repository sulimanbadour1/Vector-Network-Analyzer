# pip install pyvisa
# This code is used to find the RTB and print the IDN

import pyvisa

rm = pyvisa.ResourceManager()  # uses the system’s default VISA (R&S/NI/Keysight)
print("Found:", rm.list_resources())
inst = rm.open_resource(
    next(
        r
        for r in rm.list_resources()
        if "RTB" in r or "0x0AAD" in r or r.startswith("TCPIP0::")
    )
)
inst.read_termination = "\n"
inst.write_termination = "\n"
inst.timeout = 5000
print("IDN:", inst.query("*IDN?"))


########### The code below is used to get the data from the RTB and print the first 5 samples to verify the connection
import pyvisa, numpy as np

RES = "USB0::0x0AAD::0x01D6::203356::INSTR"  # your scope
rm = pyvisa.ResourceManager()
rtb = rm.open_resource(RES)
rtb.read_termination = "\n"
rtb.write_termination = "\n"
rtb.timeout = 5000

print("IDN:", rtb.query("*IDN?"))

# full-resolution float data from CH1
rtb.write("FORM REAL,32; FORM:BORD LSBF")
rtb.write("CHAN1:STAT 1")
rtb.write("CHAN1:DATA:POIN MAX")
rtb.write("SING")
rtb.query("*OPC?")  # wait for acquisition
y = rtb.query_binary_values("CHAN1:DATA?", datatype="f", is_big_endian=False)
print("Samples:", len(y), "First 5:", y[:5])

rtb.close()
rm.close()


import pyvisa, numpy as np

RES = "USB0::0x0AAD::0x01D6::203356::INSTR"  # your RTB resource
rm = pyvisa.ResourceManager()
rtb = rm.open_resource(RES)
rtb.timeout = 30000
rtb.chunk_size = 1024 * 1024
rtb.write("SYST:HEAD OFF; HIST:STAT OFF; ACQ:AVER:STAT OFF; ACQ:STOPA SEQ")
rtb.write("FORM REAL,32; FORM:BORD LSBF")
rtb.write("CHAN1:STAT 1; CHAN2:STAT 1")
rtb.write("TIM:SCAL 1e-4")
rtb.write("SING")
rtb.query("*OPC?")
rtb.write("CHAN1:DATA:POIN 10000")
y = rtb.query_binary_values("CHAN1:DATA?", datatype="f", is_big_endian=False)
print("Samples:", len(y), "first 5:", y[:5])
rtb.close()
rm.close()
