from ctypes import *


class Registers(Structure):

    class StatusReg(Union):
        class Flags(BigEndianStructure):
            _fields_ = [("sign", c_uint8, 1), ("zero", c_uint8, 1),
                        ("unus5", c_uint8, 1), ("aux", c_uint8, 1),
                        ("unus3", c_uint8, 1), ("parity", c_uint8, 1),
                        ("unus1", c_uint8, 1), ("carry", c_uint8, 1)]

        _fields_ = [("sr", c_uint8), ("flags", Flags)]


    class BC_16(Union):
        class BC_8_8(BigEndianStructure):
            _fields_ = [("C", c_uint8, 8), ("B", c_uint8, 8)]

        _anonymous_ = ("BC8_8",)
        _fields_ = [("BC", c_uint16), ("BC8_8", BC_8_8)]


    class DE_16(Union):
        class DE_8_8(BigEndianStructure):
            _fields_ = [("E", c_uint8, 8), ("D", c_uint8, 8)]

        _anonymous_ = ("DE8_8",)
        _fields_ = [("DE", c_uint16), ("DE8_8", DE_8_8)]

    _anonymous_ = ("status", "BC16", "DE16", )
    _fields_ = [("status", StatusReg), ("BC16", BC_16), ("DE16", DE_16)]


    class HL_16(Union):
        class HL_8_8(BigEndianStructure):
            _fields_ = [("L", c_uint8, 8), ("H", c_uint8, 8)]

        _anonymous_ = ("HL8_8",)
        _fields_ = [("HL", c_uint16), ("HL8_8", HL_8_8)]

    _anonymous_ = ("status", "BC16", "DE16", "HL16",)
    _fields_ = [("status", StatusReg), ("BC16", BC_16), ("DE16", DE_16), ("HL16", HL_16), ("sp", c_uint16), ("pc", c_uint16)]


class CPU:
    def __init__(self) -> None:
        self.regs = Registers()
