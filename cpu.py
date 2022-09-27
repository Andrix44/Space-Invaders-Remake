from ctypes import *
from sys import exit

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
    _fields_ = [("A", c_uint8), ("status", StatusReg), ("BC16", BC_16), ("DE16", DE_16), ("HL16", HL_16), ("sp", c_uint16), ("pc", c_uint16)]


class CPU: # !!! BCD-related things are not supported !!!
    def __init__(self, mem: Memory) -> None:
        self.regs = Registers()
        self.regs.flags.unus1 = True
        self.regs.flags.unus3 = False
        self.regs.flags.unus5 = False

        self.mem = mem.mem
        self.interrupts = False

    def SetFlagsZSP(self, val: int) -> None:
        self.regs.flags.zero = val == 0
        self.regs.flags.sign = val >> 7
        self.regs.flags.parity = not bin(val).count('1') & 1

    def IsConditionTrue(self, cond: int) -> bool:
        match cond:
            case 0: # Not zero
                return not self.regs.flags.zero
            case 1: # Zero
                return self.regs.flags.zero
            case 2: # No carry
                return not self.regs.flags.carry
            case 3: # Carry
                return self.regs.flags.carry
            case 4: # Parity odd
                return not self.regs.flags.parity
            case 5: # Parity even
                return self.regs.flags.parity
            case 6: # Plus
                return not self.regs.flags.sign
            case 7: # Minus
                return self.regs.flags.sign

    def Step(self) -> int:
        instr = self.mem[self.regs.pc]
        imm0 = self.mem[self.regs.pc + 1]
        imm1 = self.mem[self.regs.pc + 2]

        jump_taken = False
        cycles = CYCLE_LUT[instr]
        print(hex(self.regs.pc) + ': ' + hex(instr) + ' ' + hex(imm0) + ' ' + hex(imm1))
        #with open("log.txt", 'a') as f:
        #    f.write(f"[{self.regs.sp}] {hex(self.regs.pc)}: {hex(instr)}: {hex(self.regs.A)} {hex(self.regs.B)} {hex(self.regs.C)} {hex(self.regs.D)} {hex(self.regs.E)} {hex(self.regs.H)} {hex(self.regs.L)} {bool(self.regs.flags.sign)} {bool(self.regs.flags.zero)} {bool(self.regs.flags.parity)} {bool(self.regs.flags.carry)}\n")
        

        match instr:
            case 0x00 | 0x08 | 0x10 | 0x18 | 0x20 | 0x28 | 0x30 | 0x38: # NOP
                pass

            case 0x01 | 0x11 | 0x21 | 0x31: # LXI
                setattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3], (imm1 << 8) | imm0)
                self.regs.pc += 2

            case 0x02 | 0x12: # STAX
                addr = getattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3])
                self.mem[addr] = self.regs.A


            case 0x03 | 0x13 | 0x23 | 0x33: # INX
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                val = getattr(self.regs, reg_pair)
                setattr(self.regs, reg_pair, val + 1)


            case 0x04 | 0x0c | 0x14 | 0x1c | 0x24 | 0x2c| 0x34 | 0x3c: # INR
                reg = REGS[(instr >> 3) & 0x7]
                if(reg == "mem"):
                    self.mem[self.regs.HL] += 1
                    self.SetFlagsZSP(self.mem[self.regs.HL])
                else:
                    val = getattr(self.regs, reg)
                    setattr(self.regs, reg, val + 1)
                    self.SetFlagsZSP(val + 1)


            case 0x05 | 0x0d | 0x15 | 0x1d | 0x25 | 0x2d| 0x35 | 0x3d: # DCR
                reg = REGS[(instr >> 3) & 0x7]
                if(reg == "mem"):
                    self.mem[self.regs.HL] -= 1
                    self.SetFlagsZSP(self.mem[self.regs.HL])
                else:
                    val = getattr(self.regs, reg)
                    setattr(self.regs, reg, val - 1)
                    self.SetFlagsZSP(val - 1)


            case 0x06 | 0x0e | 0x16 | 0x1e | 0x26 | 0x2e| 0x36 | 0x3e: # MVI
                reg = REGS[(instr >> 3) & 0x7]
                setattr(self.regs, reg, imm0)
                self.regs.pc += 1

            case 0x07: # RLC
                self.regs.flags.carry = self.regs.A >> 7
                self.regs.A = self.regs.A << 1 | self.regs.flags.carry


            case 0x09 | 0x19 | 0x29 | 0x39: # DAD
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                reg_pair_val = getattr(self.regs, reg_pair)
                self.regs.carry = (self.regs.HL + reg_pair_val) > 0xffff
                self.regs.HL = self.regs.HL + reg_pair_val


            case 0x0a | 0x1a: # LDAX
                addr = getattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3])
                self.regs.A = self.mem[addr]


            case 0x0b | 0x1b | 0x2b | 0x3b: # DCX
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                reg_pair_val = getattr(self.regs, reg_pair)
                setattr(self.regs, reg_pair, reg_pair_val + 1)


            case 0x0f: # RRC
                self.regs.flags.carry = self.regs.A & 1
                self.regs.A = self.regs.A >> 1 | self.regs.flags.carry


            case 0x17: # RAL
                carry_saved = self.regs.flags.carry
                self.regs.flags.carry = self.regs.A >> 7
                self.regs.A = self.regs.A << 1 | carry_saved


            case 0x1f: # RAR
                carry_saved = self.regs.flags.carry
                self.regs.flags.carry = self.regs.A & 1
                self.regs.A = self.regs.A >> 1 | carry_saved 


            case 0x22: # SHLD
                mem_loc = (imm1 << 8) | imm0
                self.mem[mem_loc] = self.regs.L
                self.mem[mem_loc + 1] = self.regs.H
                self.regs.pc += 2

            case 0x27: # DAA
                exit(1, "DAA is not implemented!")


            case 0x2a: # LHLD
                mem_loc = (imm1 << 8) | imm0
                self.regs.L = self.mem[mem_loc]
                self.regs.H = self.mem[mem_loc + 1]
                self.regs.pc += 2

            case 0x2f: # CMA
                self.regs.A = ~self.regs.A


            case 0x32: # STA
                mem_loc = (imm1 << 8) | imm0
                self.mem[mem_loc] = self.regs.A
                self.regs.pc += 2

            case 0x37: # STC
                self.regs.flags.carry = True


            case 0x3a: # LDA
                mem_loc = (imm1 << 8) | imm0
                self.regs.A = self.mem[mem_loc]
                self.regs.pc += 2

            case 0x3f: # CMC
                self.regs.flags.carry = not self.regs.flags.carry


            case _ if (instr >= 0x40 and instr <= 0x7f and instr != 0x76): # MOV
                reg1 = REGS[(instr >> 3) & 0x7]
                reg2 = REGS[instr & 0x7]
                if(reg1 == "mem"):
                    self.mem[self.regs.HL] = getattr(self.regs, reg2)
                elif(reg2 == "mem"):
                    setattr(self.regs, reg1, self.mem[self.regs.HL])
                else:
                    setattr(self.regs, reg1, getattr(self.regs, reg2))


            case 0x76: # HLT
                exit(0, "Halt instruction")


            case _ if (instr >= 0x80 and instr <= 0xb7):
                reg = REGS[instr & 0x7]
                if(reg == "mem"):
                    reg_val = self.mem[self.regs.HL]
                else:
                    reg_val = getattr(self.regs, reg)
                
                if (instr >= 0x80 and instr <= 0x87): # ADD
                    self.regs.flags.carry = (self.regs.A + reg_val) > 0xff
                    self.regs.A += reg_val
                elif (instr >= 0x88 and instr <= 0x8f): # ADC
                    carry_saved = self.regs.flags.carry
                    self.regs.flags.carry = (self.regs.A + reg_val + self.regs.flags.carry) > 0xff
                    self.regs.A += reg_val + carry_saved
                elif (instr >= 0x90 and instr <= 0x97): # SUB
                    self.regs.flags.carry = (self.regs.A - reg_val) < 0
                    self.regs.A -= reg_val
                elif (instr >= 0x98 and instr <= 0x9f): # SBB
                    carry_saved = self.regs.flags.carry
                    self.regs.flags.carry = (self.regs.A - reg_val - self.regs.flags.carry) < 0
                    self.regs.A -= reg_val + carry_saved
                elif (instr >= 0xa0 and instr <= 0xa7): # ANA
                    self.regs.flags.carry = False
                    self.regs.A &= reg_val
                elif (instr >= 0xa8 and instr <= 0xaf): # XRA
                    self.regs.flags.carry = False
                    self.regs.A ^= reg_val
                elif (instr >= 0xb0 and instr <= 0xb7): # ORA
                    self.regs.flags.carry = False
                    self.regs.A |= reg_val
                    
                self.SetFlagsZSP(self.regs.A)
            
            case _ if (instr >= 0xb8 and instr <= 0xbf): # CMP
                reg = REGS[instr & 0x7]
                if(reg == "mem"):
                    reg_val = self.mem[self.regs.HL]
                else:
                    reg_val = getattr(self.regs, reg)
                res = (self.regs.A - reg_val) < 0
                self.SetFlagsZSP(res)

            case 0xc0 | 0xc8 | 0xd0 | 0xd8 | 0xe0 | 0xe8 | 0xf0 | 0xf8: # RCC
                cond = (instr >> 3) & 0x7
                if(self.IsConditionTrue(cond)):
                    self.regs.pc = (self.mem[self.regs.sp + 1] << 8) | self.mem[self.regs.sp]
                    self.regs.sp += 2
                    jump_taken = True


            case 0xc1 | 0xd1 | 0xe1 | 0xf1: # POP
                val = (self.mem[self.regs.sp + 1] << 8) | self.mem[self.regs.sp]
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                if(reg_pair == "sp"):
                    self.regs.sr = self.mem[self.regs.sp]
                    assert(self.regs.flags.unk1 == True)
                    assert(self.regs.flags.unk3 == False)
                    assert(self.regs.flags.unk5 == False)
                    self.regs.A = self.mem[self.regs.sp + 1]
                else:
                    setattr(self.regs, reg_pair, val)
                self.regs.sp += 2

            case 0xc2 | 0xca | 0xd2 | 0xda | 0xe2 | 0xea | 0xf2 | 0xfa: # JCC
                cond = (instr >> 3) & 0x7
                if(self.IsConditionTrue(cond)):
                    self.regs.pc = (imm1 << 8) | imm0
                    jump_taken = True
                else:
                    self.regs.pc += 2

            case 0xc3 | 0xcb: # JMP
                self.regs.pc = (imm1 << 8) | imm0
                jump_taken = True

            case 0xc4 | 0xcc | 0xd4 | 0xdc | 0xe4 | 0xec | 0xf4 | 0xfc: # CCC
                cond = (instr >> 3) & 0x7
                if(self.IsConditionTrue(cond)):
                    self.mem[self.regs.sp - 1] = self.regs.pc >> 8
                    self.mem[self.regs.sp - 2] = self.regs.pc & 0xff
                    self.regs.sp -= 2
                    self.regs.pc = (imm1 << 8) | imm0
                    jump_taken = True
                else:
                    self.regs.pc += 2

            case 0xc5 | 0xd5 | 0xe5 | 0xf5: # PUSH
                reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
                if(reg_pair == "sp"):
                    self.mem[self.regs.sp - 1] = self.regs.A
                    self.mem[self.regs.sp - 2] = self.regs.sr
                else:
                    reg_pair_val = getattr(self.regs, reg_pair)
                    self.mem[self.regs.sp - 1] = reg_pair_val >> 8
                    self.mem[self.regs.sp - 2] = reg_pair_val & 0xff
                self.regs.sp -= 2

            case 0xc6 | 0xce | 0xd6 | 0xde | 0xe6 | 0xee | 0xf6:
                if(instr == 0xc6): # ADI
                    self.regs.flags.carry = (self.regs.A + imm0) > 0xff
                    self.regs.A += imm0
                elif(instr == 0xce): # ACI
                    carry_saved = self.regs.flags.carry
                    self.regs.flags.carry = (self.regs.A + imm0 + self.regs.flags.carry) > 0xff
                    self.regs.A += imm0 + carry_saved
                elif(instr == 0xd6): # SUI
                    self.regs.flags.carry = (self.regs.A - imm0) < 0
                    self.regs.A -= imm0
                elif(instr == 0xde): # SBI
                    carry_saved = self.regs.flags.carry
                    self.regs.flags.carry = (self.regs.A - imm0 - self.regs.flags.carry) < 0
                    self.regs.A -= imm0 + carry_saved
                elif(instr == 0xe6): # ANI
                    self.regs.flags.carry = False
                    self.regs.A &= imm0
                elif(instr == 0xee): # XRI
                    self.regs.flags.carry = False
                    self.regs.A ^= imm0
                elif(instr == 0xf6): # ORI
                    self.regs.flags.carry = False
                    self.regs.A |= imm0
                
                self.SetFlagsZSP(self.regs.A)
                self.regs.pc += 1

            case 0xfe: # CPI
                self.regs.flags.carry = (self.regs.A - imm0) < 0
                res: c_uint8 = self.regs.A - imm0
                self.SetFlagsZSP(res)
                self.regs.pc += 1

            case 0xc7 | 0xcf | 0xd7 | 0xdf | 0xe7 | 0xef | 0xf7 | 0xff: # RST
                self.mem[self.regs.sp - 1] = self.regs.pc >> 8
                self.mem[self.regs.sp - 2] = self.regs.pc & 0xff
                self.regs.sp -= 2
                self.regs.pc = 8 * ((instr >> 3) & 7)

            case 0xc9 | 0xd9: # RET
                self.regs.pc = (self.mem[self.regs.sp + 1] << 8) | self.mem[self.regs.sp]
                self.regs.sp += 2

            case 0xcd | 0xdd | 0xed | 0xfd: # CALL
                self.mem[self.regs.sp - 1] = self.regs.pc >> 8
                self.mem[self.regs.sp - 2] = self.regs.pc & 0xff
                self.regs.sp -= 2
                self.regs.pc = (imm1 << 8) | imm0
                jump_taken = True

            case 0xd3: # OUT
                pass

            case 0xdb: # IN
                pass

            case 0xe3: # XTHL
                self.regs.L, self.mem[self.regs.sp] = self.mem[self.regs.sp], self.regs.L
                self.regs.H, self.mem[self.regs.sp + 1] = self.mem[self.regs.sp + 1], self.regs.H

            case 0xe9: # PCHL
                self.regs.pc = self.regs.HL

            case 0xeb: # XCHG
                self.regs.HL, self.regs.DE = self.regs.DE, self.regs.HL

            case 0xf3: # DI
                self.interrupts = False

            case 0xfb: # EI
                self.interrupts = True

            case 0xf9: # SPHL
                self.regs.sp = self.regs.HL

            case _:
                print("Unsupported instruction: " + hex(instr))
                exit(1)

        if(jump_taken):
            cycles += 6
        else:
            self.regs.pc += 1
        return cycles
