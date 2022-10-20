from ctypes import *
from sys import exit

from audio import Audio
from memory import Memory

# Most instruction run in a specific amount of cycles which can be turned into a LUT
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

class Registers(Structure):
    """Uses ctypes structs and unions to let the programmer access the registers as a whole or in smaller parts"""
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


    class Shift(Union):
        class Shift_8_8(BigEndianStructure):
            _fields_ = [("shift_lo", c_uint8, 8), ("shift_hi", c_uint8, 8)]

        _anonymous_ = ("Shift8_8",)
        _fields_ = [("shift_full", c_uint16), ("Shift8_8", Shift_8_8)]


    _anonymous_ = ("status", "BC16", "DE16", "HL16", "shift",)
    _fields_ = [("A", c_uint8), ("status", StatusReg), ("BC16", BC_16), ("DE16", DE_16), ("HL16", HL_16), ("sp", c_uint16),
                ("pc", c_uint16), ("shift", Shift), ("shift_off", c_uint8), ("input1", c_uint8), ("input2", c_uint8)]


class CPU:
    """The main part of the emulator, an Intel 8080 interpreter"""
    def __init__(self, mem: Memory, audio: Audio) -> None:
        self.regs = Registers()
        self.regs.flags.unus1 = True
        self.regs.flags.unus3 = False
        self.regs.flags.unus5 = False

        self.mem = mem.mem
        self.audio = audio
        self.interrupts_enabled = False

        self.jump_table = (self.Instr_NOP, self.Instr_LXI, self.Instr_STAX, self.Instr_INX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_RLC,
                           self.Instr_NOP, self.Instr_DAD, self.Instr_LDAX, self.Instr_DCX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_RRC,
                           self.Instr_NOP, self.Instr_LXI, self.Instr_STAX, self.Instr_INX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_RAL,
                           self.Instr_NOP, self.Instr_DAD, self.Instr_LDAX, self.Instr_DCX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_RAR,
                           self.Instr_NOP, self.Instr_LXI, self.Instr_SHLD, self.Instr_INX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_DAA,
                           self.Instr_NOP, self.Instr_DAD, self.Instr_LHLD, self.Instr_DCX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_CMA,
                           self.Instr_NOP, self.Instr_LXI, self.Instr_STA , self.Instr_INX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_STC,
                           self.Instr_NOP, self.Instr_DAD, self.Instr_LDA , self.Instr_DCX, self.Instr_INR, self.Instr_DCR, self.Instr_MVI, self.Instr_CMC,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_HLT, self.Instr_MOV,
                           self.Instr_MOV, self.Instr_MOV, self.Instr_MOV , self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV, self.Instr_MOV,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.InstrGrp1, self.InstrGrp1, self.InstrGrp1 , self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1, self.InstrGrp1,
                           self.Instr_CMP, self.Instr_CMP, self.Instr_CMP , self.Instr_CMP, self.Instr_CMP, self.Instr_CMP, self.Instr_CMP, self.Instr_CMP,
                           self.Instr_RCC, self.Instr_POP, self.Instr_JCC , self.Instr_JMP, self.Instr_CCC, self.Instr_PUSH,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_RET, self.Instr_JCC , self.Instr_JMP, self.Instr_CCC, self.Instr_CALL,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_POP, self.Instr_JCC , self.Instr_OUT, self.Instr_CCC, self.Instr_PUSH,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_RET, self.Instr_JCC , self.Instr_IN,  self.Instr_CCC, self.Instr_CALL,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_POP, self.Instr_JCC , self.Instr_XTHL,self.Instr_CCC, self.Instr_PUSH,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_PCHL,self.Instr_JCC , self.Instr_XCHG,self.Instr_CCC, self.Instr_CALL,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_POP, self.Instr_JCC , self.Instr_DI,  self.Instr_CCC, self.Instr_PUSH,self.InstrGrp2, self.Instr_RST,
                           self.Instr_RCC, self.Instr_SPHL,self.Instr_JCC , self.Instr_EI,  self.Instr_CCC, self.Instr_CALL,self.Instr_CPI, self.Instr_RST)

    def SetFlagsZSP(self, val: int) -> None:
        """Sets the zero, sign and parity flags based on the argument"""
        self.regs.flags.zero = val == 0
        self.regs.flags.sign = val >> 7
        self.regs.flags.parity = not bin(val).count('1') & 1

    def IsConditionTrue(self, cond: int) -> bool:
        """Return whether the condition is true or false"""
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

    def Push16(self, val: int) -> None:
        """Pushes a 2 bytes onto the stack"""
        self.mem[self.regs.sp - 1] = val >> 8
        self.mem[self.regs.sp - 2] = val & 0xff
        self.regs.sp -= 2

    def Pop16(self) -> int:
        """Pops 2 bytes from the stack"""
        val = (self.mem[self.regs.sp + 1] << 8) | self.mem[self.regs.sp]
        self.regs.sp += 2
        return val

    def Step(self) -> int:
        """Executes 1 instruction"""
        instr = self.mem[self.regs.pc]
        imm0 = self.mem[self.regs.pc + 1]
        imm1 = self.mem[self.regs.pc + 2]

        # These two have to be single element arrays so that they get passed to the instruction handlers by reference
        keep_pc = [False]
        cycles = [CYCLE_LUT[instr]]

        #print(hex(self.regs.pc) + ': ' + hex(instr) + ' ' + hex(imm0) + ' ' + hex(imm1))
        self.jump_table[instr](instr, imm0, imm1, keep_pc, cycles)

        # A simplification for instructions that didn't modify the program counter and only have a length of 1
        # Instructions with immediate values still have to increment pc by the number of their immediates
        if not keep_pc[0]:
            self.regs.pc += 1

        return cycles[0]

    def GenerateInterrupt(self, interrupt_num: int) -> None:
        """Injects an interrupt that was generated during rendering"""
        self.mem[self.regs.sp - 1] = self.regs.pc >> 8
        self.mem[self.regs.sp - 2] = self.regs.pc & 0xFF
        self.regs.sp -= 2
        self.regs.pc = interrupt_num * 8
        self.interrupts_enabled = False


    ########################
    # Instruction handlers #
    ########################

    # Many of them are used in several instruction variants

    def Instr_NOP(self, instr, imm0, imm1, keep_pc, cycles):
        pass

    def Instr_LXI(self, instr, imm0, imm1, keep_pc, cycles):
        setattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3], (imm1 << 8) | imm0)
        self.regs.pc += 2

    def Instr_STAX(self, instr, imm0, imm1, keep_pc, cycles):
        addr = getattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3])
        self.mem[addr] = self.regs.A

    def Instr_INX(self, instr, imm0, imm1, keep_pc, cycles):
        reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
        reg_pair_val = getattr(self.regs, reg_pair)
        setattr(self.regs, reg_pair, reg_pair_val + 1)

    def Instr_INR(self, instr, imm0, imm1, keep_pc, cycles):
        reg = REGS[(instr >> 3) & 0x7]
        if(reg == "mem"):
            self.regs.flags.aux = ((self.mem[self.regs.HL] & 0xf) + 1) > 0xf
            self.mem[self.regs.HL] += 1
            self.SetFlagsZSP(self.mem[self.regs.HL])
        else:
            val = getattr(self.regs, reg)
            self.regs.flags.aux = ((val & 0xf) + 1) > 0xf
            setattr(self.regs, reg, val + 1)
            self.SetFlagsZSP(val + 1)

    def Instr_DCR(self, instr, imm0, imm1, keep_pc, cycles):
        reg = REGS[(instr >> 3) & 0x7]
        if(reg == "mem"):
            self.regs.flags.aux = ((self.mem[self.regs.HL] & 0xf) - 1) < 0
            self.mem[self.regs.HL] = (self.mem[self.regs.HL] - 1) & 0xff
            self.SetFlagsZSP(self.mem[self.regs.HL])
        else:
            val = getattr(self.regs, reg)
            self.regs.flags.aux = ((val & 0xf) - 1) < 0
            setattr(self.regs, reg, val - 1)
            self.SetFlagsZSP(val - 1)

    def Instr_MVI(self, instr, imm0, imm1, keep_pc, cycles):
        reg = REGS[(instr >> 3) & 0x7]
        if(reg == "mem"):
            self.mem[self.regs.HL] = imm0
        else:
            setattr(self.regs, reg, imm0)
        self.regs.pc += 1

    def Instr_RLC(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.flags.carry = self.regs.A >> 7
        self.regs.A = self.regs.A << 1 | self.regs.flags.carry

    def Instr_DAD(self, instr, imm0, imm1, keep_pc, cycles):
        reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
        reg_pair_val = getattr(self.regs, reg_pair)
        self.regs.flags.carry = (self.regs.HL + reg_pair_val) > 0xffff
        self.regs.HL = self.regs.HL + reg_pair_val

    def Instr_LDAX(self, instr, imm0, imm1, keep_pc, cycles):
        addr = getattr(self.regs, REG_PAIRS[(instr >> 4) & 0x3])
        self.regs.A = self.mem[addr]

    def Instr_DCX(self, instr, imm0, imm1, keep_pc, cycles):
        reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
        reg_pair_val = getattr(self.regs, reg_pair)
        setattr(self.regs, reg_pair, reg_pair_val - 1)

    def Instr_RRC(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.flags.carry = self.regs.A & 1
        self.regs.A = (self.regs.flags.carry << 7) | (self.regs.A >> 1)

    def Instr_RAL(self, instr, imm0, imm1, keep_pc, cycles):
        carry_saved = self.regs.flags.carry
        self.regs.flags.carry = self.regs.A >> 7
        self.regs.A = self.regs.A << 1 | carry_saved

    def Instr_RAR(self, instr, imm0, imm1, keep_pc, cycles):
        carry_saved = self.regs.flags.carry
        self.regs.flags.carry = self.regs.A & 1
        self.regs.A = (carry_saved << 7) | (self.regs.A >> 1)

    def Instr_SHLD(self, instr, imm0, imm1, keep_pc, cycles):
        mem_loc = (imm1 << 8) | imm0
        self.mem[mem_loc] = self.regs.L
        self.mem[mem_loc + 1] = self.regs.H
        self.regs.pc += 2

    def Instr_DAA(self, instr, imm0, imm1, keep_pc, cycles):
        if((self.regs.A & 0xf) > 9 or self.regs.flags.aux):
            self.regs.flags.aux = (self.regs.A & 0xf) > 9
            self.regs.A += 6
        
        if((self.regs.A >> 4) > 9 or self.regs.flags.carry):
            self.regs.flags.carry = (self.regs.A + (6 << 4)) > 0xff
            self.regs.A += 6 << 4

        self.SetFlagsZSP(self.regs.A)

    def Instr_LHLD(self, instr, imm0, imm1, keep_pc, cycles):
        mem_loc = (imm1 << 8) | imm0
        self.regs.L = self.mem[mem_loc]
        self.regs.H = self.mem[mem_loc + 1]
        self.regs.pc += 2

    def Instr_CMA(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.A = ~self.regs.A

    def Instr_STA(self, instr, imm0, imm1, keep_pc, cycles):
        mem_loc = (imm1 << 8) | imm0
        self.mem[mem_loc] = self.regs.A
        self.regs.pc += 2

    def Instr_STC(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.flags.carry = True

    def Instr_LDA(self, instr, imm0, imm1, keep_pc, cycles):
        mem_loc = (imm1 << 8) | imm0
        self.regs.A = self.mem[mem_loc]
        self.regs.pc += 2

    def Instr_CMC(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.flags.carry = not self.regs.flags.carry

    def Instr_MOV(self, instr, imm0, imm1, keep_pc, cycles):
        reg1 = REGS[(instr >> 3) & 0x7]
        reg2 = REGS[instr & 0x7]
        if(reg1 == "mem"):
            self.mem[self.regs.HL] = getattr(self.regs, reg2)
        elif(reg2 == "mem"):
            setattr(self.regs, reg1, self.mem[self.regs.HL])
        else:
            setattr(self.regs, reg1, getattr(self.regs, reg2))

    def Instr_HLT(self, instr, imm0, imm1, keep_pc, cycles):
        exit(0, "Halt instruction")

    def InstrGrp1(self, instr, imm0, imm1, keep_pc, cycles):
        reg = REGS[instr & 0x7]
        if(reg == "mem"):
            reg_val = self.mem[self.regs.HL]
        else:
            reg_val = getattr(self.regs, reg)
        
        if (instr >= 0x80 and instr <= 0x87): # ADD
            self.regs.flags.carry = (self.regs.A + reg_val) > 0xff
            self.regs.flags.aux = ((self.regs.A & 0xf) + (reg_val & 0xf)) > 0xf
            self.regs.A += reg_val
        elif (instr >= 0x88 and instr <= 0x8f): # ADC
            carry_saved = self.regs.flags.carry
            self.regs.flags.carry = (self.regs.A + reg_val + self.regs.flags.carry) > 0xff
            self.regs.flags.aux = ((self.regs.A & 0xf) + (reg_val & 0xf) + self.regs.flags.carry) > 0xf
            self.regs.A += reg_val + carry_saved
        elif (instr >= 0x90 and instr <= 0x97): # SUB
            self.regs.flags.carry = self.regs.A < reg_val
            self.regs.flags.aux = (self.regs.A & 0xf) < (reg_val & 0xf)
            self.regs.A -= reg_val
        elif (instr >= 0x98 and instr <= 0x9f): # SBB
            carry_saved = self.regs.flags.carry
            self.regs.flags.carry = self.regs.A < reg_val + self.regs.flags.carry
            self.regs.flags.aux = (self.regs.A & 0xf) < (reg_val & 0xf) + self.regs.flags.carry
            self.regs.A -= reg_val + carry_saved
        elif (instr >= 0xa0 and instr <= 0xa7): # ANA
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A &= reg_val
        elif (instr >= 0xa8 and instr <= 0xaf): # XRA
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A ^= reg_val
        elif (instr >= 0xb0 and instr <= 0xb7): # ORA
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A |= reg_val
            
        self.SetFlagsZSP(self.regs.A)
    
    def Instr_CMP(self, instr, imm0, imm1, keep_pc, cycles):
        reg = REGS[instr & 0x7]
        if(reg == "mem"):
            reg_val = self.mem[self.regs.HL]
        else:
            reg_val = getattr(self.regs, reg)
        self.regs.flags.carry = (self.regs.A - reg_val) < 0
        self.regs.flags.aux = ((self.regs.A & 0xf) - (reg_val & 0xf)) < 0
        self.SetFlagsZSP(self.regs.A - reg_val)

    def Instr_RCC(self, instr, imm0, imm1, keep_pc, cycles):
        cond = (instr >> 3) & 0x7
        if(self.IsConditionTrue(cond)):
            self.regs.pc = self.Pop16()
            cycles[0] += 6
            keep_pc[0] = True

    def Instr_POP(self, instr, imm0, imm1, keep_pc, cycles):
        val = self.Pop16()
        reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
        if(reg_pair == "sp"):
            self.regs.sr = val & 0xff
            assert(self.regs.flags.unus1 == True)
            assert(self.regs.flags.unus3 == False)
            assert(self.regs.flags.unus5 == False)
            self.regs.A = val >> 8
        else:
            setattr(self.regs, reg_pair, val)

    def Instr_JCC(self, instr, imm0, imm1, keep_pc, cycles):
        cond = (instr >> 3) & 0x7
        if(self.IsConditionTrue(cond)):
            self.regs.pc = (imm1 << 8) | imm0
            keep_pc[0] = True
        else:
            self.regs.pc += 2

    def Instr_JMP(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.pc = (imm1 << 8) | imm0
        keep_pc[0] = True

    def Instr_CCC(self, instr, imm0, imm1, keep_pc, cycles):
        cond = (instr >> 3) & 0x7
        if(self.IsConditionTrue(cond)):
            self.Push16(self.regs.pc + 3)
            self.regs.pc = (imm1 << 8) | imm0
            cycles[0] += 6
            keep_pc[0] = True
        else:
            self.regs.pc += 2

    def Instr_PUSH(self, instr, imm0, imm1, keep_pc, cycles):
        reg_pair = REG_PAIRS[(instr >> 4) & 0x3]
        if(reg_pair == "sp"):
            self.Push16((self.regs.A << 8) | self.regs.sr)
        else:
            reg_pair_val = getattr(self.regs, reg_pair)
            self.Push16(reg_pair_val)

    def InstrGrp2(self, instr, imm0, imm1, keep_pc, cycles):
        if(instr == 0xc6): # ADI
            self.regs.flags.carry = (self.regs.A + imm0) > 0xff
            self.regs.flags.aux = ((self.regs.A & 0xf) + (imm0 & 0xf)) > 0xf
            self.regs.A += imm0
        elif(instr == 0xce): # ACI
            carry_saved = self.regs.flags.carry
            self.regs.flags.carry = (self.regs.A + imm0 + self.regs.flags.carry) > 0xff
            self.regs.flags.aux = ((self.regs.A & 0xf) + (imm0 & 0xf) + self.regs.flags.carry) > 0xf
            self.regs.A += imm0 + carry_saved
        elif(instr == 0xd6): # SUI
            self.regs.flags.carry = self.regs.A < imm0
            self.regs.flags.aux = (self.regs.A & 0xf) < (imm0 & 0xf)
            self.regs.A -= imm0
        elif(instr == 0xde): # SBI
            carry_saved = self.regs.flags.carry
            self.regs.flags.carry = self.regs.A < imm0 + self.regs.flags.carry
            self.regs.flags.aux = (self.regs.A & 0xf) < (imm0 & 0xf) + self.regs.flags.carry
            self.regs.A -= imm0 + carry_saved
        elif(instr == 0xe6): # ANI
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A &= imm0
        elif(instr == 0xee): # XRI
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A ^= imm0
        elif(instr == 0xf6): # ORI
            self.regs.flags.carry = False
            self.regs.flags.aux = False
            self.regs.A |= imm0
        
        self.SetFlagsZSP(self.regs.A)
        self.regs.pc += 1

    def Instr_CPI(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.flags.carry = self.regs.A < imm0
        self.regs.flags.aux = (self.regs.A & 0xf) < (imm0 & 0xf)
        res = (self.regs.A - imm0) & 0xff
        self.SetFlagsZSP(res)
        self.regs.pc += 1

    def Instr_RST(self, instr, imm0, imm1, keep_pc, cycles):
        self.Push16(self.regs.pc + 1)
        self.regs.pc = instr & 0x38

    def Instr_RET(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.pc = self.Pop16()
        keep_pc[0] = True

    def Instr_CALL(self, instr, imm0, imm1, keep_pc, cycles):
        if((imm1 << 8) | imm0 == 0x5):  # Output hack
                if(self.regs.C == 0x9):
                    offset = self.regs.DE
                    i = 0
                    output = ""
                    while(not output.endswith("$")):
                        output += chr(self.mem[offset + i])
                        i += 1
                    print(output, hex(self.regs.HL))
                    
                elif(self.regs.C == 0x2):
                    print(chr(self.regs.E), end='')

        self.Push16(self.regs.pc + 3)
        self.regs.pc = (imm1 << 8) | imm0

        keep_pc[0] = True

    def Instr_OUT(self, instr, imm0, imm1, keep_pc, cycles):
        port = imm0
        if(port == 2):
            self.regs.shift_off = self.regs.A & 0x7
        elif(port == 3):
            self.audio.PlaySound3(self.regs.A)
        elif(port == 4):
            self.regs.shift_lo = self.regs.shift_hi
            self.regs.shift_hi = self.regs.A
        elif(port == 5):
            self.audio.PlaySound5(self.regs.A)
        self.regs.pc += 1

    def Instr_IN(self, instr, imm0, imm1, keep_pc, cycles):
        port = imm0
        if(port == 1):
            self.regs.A = self.regs.input1
        elif(port == 2):
                self.regs.A = self.regs.input2
        elif(port == 3):
                self.regs.A = (self.regs.shift_full >> (8 - self.regs.shift_off)) & 0xff
        self.regs.pc += 1

    def Instr_XTHL(self, instr, imm0, imm1, keep_pc, cycles):
        stack_saved = self.Pop16()
        self.Push16(self.regs.HL)
        self.regs.HL = stack_saved

    def Instr_PCHL(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.pc = self.regs.HL
        keep_pc[0] = True

    def Instr_XCHG(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.HL, self.regs.DE = self.regs.DE, self.regs.HL

    def Instr_DI(self, instr, imm0, imm1, keep_pc, cycles):
        self.interrupts_enabled = False

    def Instr_EI(self, instr, imm0, imm1, keep_pc, cycles):
        self.interrupts_enabled = True

    def Instr_SPHL(self, instr, imm0, imm1, keep_pc, cycles):
        self.regs.sp = self.regs.HL
