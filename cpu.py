from ctypes import *
import operator

from memory import Memory


CYCLE_LUT = (4, 10, 7,  5,  5,  5,  7,  4,  4, 10, 7,  5,  5,  5,  7, 4,   # 0x0X
             4, 10, 7,  5,  5,  5,  7,  4,  4, 10, 7,  5,  5,  5,  7, 4,   # 0x1X
             4, 10, 16, 5,  5,  5,  7,  4,  4, 10, 16, 5,  5,  5,  7, 4,   # 0x2X
             4, 10, 13, 5,  10, 10, 10, 4,  4, 10, 13, 5,  5,  5,  7, 4,   # 0x3X
             5, 5,  5,  5,  5,  5,  7,  5,  5, 5,  5,  5,  5,  5,  7, 5,   # 0x4X
             5, 5,  5,  5,  5,  5,  7,  5,  5, 5,  5,  5,  5,  5,  7, 5,   # 0x5X
             5, 5,  5,  5,  5,  5,  7,  5,  5, 5,  5,  5,  5,  5,  7, 5,   # 0x6X
             7, 7,  7,  7,  7,  7,  7,  7,  5, 5,  5,  5,  5,  5,  7, 5,   # 0x7X
             4, 4,  4,  4,  4,  4,  7,  4,  4, 4,  4,  4,  4,  4,  7, 4,   # 0x8X
             4, 4,  4,  4,  4,  4,  7,  4,  4, 4,  4,  4,  4,  4,  7, 4,   # 0x9X
             4, 4,  4,  4,  4,  4,  7,  4,  4, 4,  4,  4,  4,  4,  7, 4,   # 0xAX
             4, 4,  4,  4,  4,  4,  7,  4,  4, 4,  4,  4,  4,  4,  7, 4,   # 0xBX
             5, 10, 10, 10, 11, 11, 7,  11, 5, 10, 10, 10, 11, 17, 7, 11,  # 0xCX
             5, 10, 10, 10, 11, 11, 7,  11, 5, 10, 10, 10, 11, 11, 7, 11,  # 0xDX
             5, 10, 10, 18, 11, 11, 7,  11, 5, 5,  10, 5,  11, 11, 7, 11,  # 0xEX
             5, 10, 10, 4,  11, 11, 7,  11, 5, 5,  10, 4,  11, 11, 7, 11)  # 0xFX

REG_PAIRS = ("BC", "DE", "HL", "sp")
REGS = ("B", "C", "D", "E", "H", "L", "mem", "A")
OPERATORS = {}

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


class CPU: # !!! BCD-related things are not supported !!!
    def __init__(self, mem: Memory) -> None:
        self.regs = Registers()
        self.regs.flags.unus1 = True
        self.regs.flags.unus3 = False
        self.regs.flags.unus5 = False

        self.last_jump_taken = False

        self.mem = mem.mem

    def SetFlagsZSP(self, val) -> None:
        self.regs.flags.zero = val == 0
        self.regs.flags.sign = val >> 7
        self.regs.flags.parity = bin(val).count('1') & 1

    def Step(self) -> int:
        instr = self.mem[self.regs.pc]
        imm0 = self.mem[self.regs.pc + 1]
        imm1 = self.mem[self.regs.pc + 2]

        match instr:
            case 0x00 | 0x08 | 0x10 | 0x18 | 0x20 | 0x28 | 0x30 | 0x38: # NOP
                self.regs.pc += 1

            case 0x01 | 0x11 | 0x21 | 0x31: # LXI
                setattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3], (imm1 << 8) | imm0)
                self.regs.pc += 3

            case 0x02 | 0x12: # STAX
                addr = getattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3])
                self.mem[addr] = self.regs.A
                self.regs.pc += 1

            case 0x03 | 0x13 | 0x23 | 0x33: # INX
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                val = getattr(self.regs, reg_pair)
                setattr(self.regs, reg_pair, val + 1)
                self.regs.pc += 1

            case 0x04 | 0x0c | 0x14 | 0x1c | 0x24 | 0x2c| 0x34 | 0x3c: # INR
                reg = REGS[(instr >> 3) & 0x7]
                if(reg == "mem"):
                    self.mem[self.regs.HL] += 1
                    self.SetFlagsZSP(self.mem[self.regs.HL])
                else:
                    val = getattr(self.regs, reg)
                    setattr(self.regs, reg, val + 1)
                    self.SetFlagsZSP(val + 1)
                self.regs.pc += 1

            case 0x05 | 0x0d | 0x15 | 0x1d | 0x25 | 0x2d| 0x35 | 0x3d: # DCR
                reg = REGS[(instr >> 3) & 0x7]
                if(reg == "mem"):
                    self.mem[self.regs.HL] -= 1
                    self.SetFlagsZSP(self.mem[self.regs.HL])
                else:
                    val = getattr(self.regs, reg)
                    setattr(self.regs, reg, val - 1)
                    self.SetFlagsZSP(val - 1)
                self.regs.pc += 1

            case 0x06 | 0x0e | 0x16 | 0x1e | 0x26 | 0x2e| 0x36 | 0x3e: # MVI
                reg = REGS[(instr >> 3) & 0x7]
                setattr(self.regs, reg, imm0)
                self.regs.pc += 2

            case _:
                print(hex(instr))
                assert(False)


        cycles = CYCLE_LUT[instr]
        if(self.last_jump_taken):
            cycles += 6
            self.last_jump_taken = False
        return cycles
