import pygame

from audio import Audio
from cpu import CPU
from memory import Memory

CLOCKSPEED = 2000000
REFRESH_RATE = 60
CYCLES_PER_FRAME = CLOCKSPEED // REFRESH_RATE
CYCLES_PER_HALF_FRAME = CYCLES_PER_FRAME // 2


class Emulator:
    """The foundation that ties together the other modules"""
    def __init__(self, rom_path: str, debug: bool) -> None:
        pygame.init()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed((pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT))

        pygame.display.set_icon(pygame.image.load("icon.bmp"))
        pygame.display.set_caption("Space Invaders")
        self.scaled = pygame.display.set_mode((672, 768))

        self.audio = Audio()
        self.memory = Memory(rom_path, debug)
        self.mem = self.memory.mem
        self.cpu = CPU(self.memory, self.audio)

        # Most of the debug ROMs are loaded at address 0x100
        if(debug):
            self.cpu.regs.pc = 0x100

        self.running = True

    def Run(self) -> None:
        """Runs the main loop of the emulation"""
        clock = pygame.time.Clock()
        while(self.running):
            clock.tick(REFRESH_RATE)
            self.HandleEvents()
            self.RunFrame()
            self.DrawFrame()

    def RunFrame(self) -> None:
        """Runs the emulation for one complete frame"""
        first_interrupt = True
        cycle_tot = cycle_var = 0
        while(cycle_tot <= CYCLES_PER_FRAME):
            cycles = self.cpu.Step()
            cycle_tot += cycles
            cycle_var += cycles

            if(cycle_var >= CYCLES_PER_HALF_FRAME - 19 and self.cpu.interrupts_enabled):
                if(first_interrupt):
                    self.cpu.GenerateInterrupt(1)
                    first_interrupt = False
                    cycle_var = 0
                else:
                    self.cpu.GenerateInterrupt(2)

    def DrawFrame(self) -> None:
        """Load the data contained in the VRAM into the surface that the user sees"""
        surface = pygame.Surface((256, 224))
        pixelarray = pygame.PixelArray(surface)
        for i, vram_byte in enumerate(self.mem[0x2400: 0x4000]):
            for j in range(8):
                if((vram_byte >> j) & 1):
                    pixelarray[((i*8) + j) % 256, (i*8) // 256] = 0xffffff # White

        pygame.transform.scale(pygame.transform.rotate(surface, 90.0), (672, 768), self.scaled)
        pygame.display.flip()

    def HandleEvents(self) -> None:
        """Handles keyboard presses and the quit event"""
        for event in pygame.event.get():
            """
            Controls: Player 1: A - left    Player 2 : left arrow  - left
                                D - right              right arrow - right
                                W - shoot              up arrow    - shoot
                                E - start              right CTRL  - start

                      space       - tilt
                      enter       - insert coin
                      numbers 0-3 - sets the amount of lives to: pressed number + 3
                      numbers 4-5 - bonus life at 4: 1000 points
                                                  5: 1500 points
                      numbers 6-7 - coin info 6: off
                                              7: on
            """
            match event.type:
                case pygame.KEYDOWN: # A.W.D for player 1, left.up.right for player 2
                    key = pygame.key.name(event.key)
                    if(key == "a"): self.cpu.regs.input1 |= 0b00100000
                    elif(key == "d"): self.cpu.regs.input1 |= 0b01000000
                    elif(key == "w"): self.cpu.regs.input1 |= 0b00010000
                    elif(key == "e"): self.cpu.regs.input1 |= 0b00000100
                    elif(key == "left"): self.cpu.regs.input2 |= 0b00100000
                    elif(key == "right"): self.cpu.regs.input2 |= 0b01000000
                    elif(key == "up"): self.cpu.regs.input2 |= 0b00010000
                    elif(key == "right ctrl"): self.cpu.regs.input1 |= 0b00000010
                    elif(key == "space"): self.cpu.regs.input2 |= 0b00000100
                    # Dipswitches(they don't need a keyup event) and exit:
                    elif(key == "return"): self.cpu.regs.input1 &= 0b11111110
                    elif(key == "`"): self.cpu.regs.input2 &= 0b11111100
                    elif(key == "1"): self.cpu.regs.input2 &= 0b11111100; self.cpu.regs.input2 += 1
                    elif(key == "2"): self.cpu.regs.input2 &= 0b11111100; self.cpu.regs.input2 += 2
                    elif(key == "3"): self.cpu.regs.input2 &= 0b11111100; self.cpu.regs.input2 += 3
                    elif(key == "4"): self.cpu.regs.input2 |= 0b00001000
                    elif(key == "5"): self.cpu.regs.input2 &= 0b11110111
                    elif(key == "6"): self.cpu.regs.input2 |= 0b10000000
                    elif(key == "7"): self.cpu.regs.input2 &= 0b01111111
                    elif(key == "escape"): self.running = False
                case pygame.KEYUP:
                    key = pygame.key.name(event.key)
                    if(key == "a"): self.cpu.regs.input1 &= 0b11011111
                    elif(key == "d"): self.cpu.regs.input1 &= 0b10111111
                    elif(key == "w"): self.cpu.regs.input1 &= 0b11101111
                    elif(key == "e"): self.cpu.regs.input1 &= 0b11111011
                    elif(key == "left"): self.cpu.regs.input2 &= 0b11011111
                    elif(key == "right"): self.cpu.regs.input2 &= 0b10111111
                    elif(key == "up"): self.cpu.regs.input2 &= 0b11101111
                    elif(key == "right ctrl"): self.cpu.regs.input1 &= 0b11111101
                    elif(key == "space"): self.cpu.regs.input2 &= 0b11111011
                    elif(key == "return"): self.cpu.regs.input1 |= 0b1
                case pygame.QUIT:
                    self.running = False
