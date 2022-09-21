import pygame

from audio import Audio
from cpu import CPU
from memory import Memory

CLOCKSPEED = 2000000
REFRESH_RATE = 60
CYCLES_PER_FRAME = CLOCKSPEED // REFRESH_RATE
CYCLES_PER_HALF_FRAME = CYCLES_PER_FRAME // 2


class Emulator:
    def __init__(self, rom_path) -> None:
        pygame.init()
        pygame.event.set_blocked(None)
        pygame.event.set_allowed((pygame.KEYDOWN, pygame.KEYUP, pygame.QUIT))

        pygame.display.set_icon(pygame.image.load("icon.bmp"))
        pygame.display.set_caption("Space Invaders")
        self.native = pygame.Surface((224, 256))
        self.scaled = pygame.display.set_mode((672, 768))

        self.audio = Audio()
        self.mem = Memory()
        self.cpu = CPU(self.mem)

        self.mem.LoadRom(rom_path)
        self.running = True

    def Run(self) -> None:
        clock = pygame.time.Clock()
        while(self.running):
            clock.tick(REFRESH_RATE)
            self.HandleEvents()
            self.RunFrame()
            self.DrawFrame()

    def RunFrame(self) -> None:
        first_interrupt = True
        cycle_tot = cycle_var = 0
        while(cycle_tot <= CYCLES_PER_FRAME):
            cycles = self.cpu.Step()
            cycle_tot += cycles
            cycle_var += cycles

            #if(cycle_var >= CYCLES_PER_HALF_FRAME - 19 and self.i8080.interrupt):
            #    if(first_interrupt):
            #        self.interp.GenerateInterrupt(self.i8080, 1)
            #        first_interrupt = False
            #        cycle_var = 0
            #    else:
            #        self.interp.GenerateInterrupt(self.i8080, 2)

    def DrawFrame(self) -> None:
        self.native.fill(pygame.Color(0, 0, 0, 0))
        #hotcode.GenBitmap(self.native, self.i8080.memory)
        pygame.transform.scale(self.native, (672, 768), self.scaled)
        pygame.display.update()

    def HandleEvents(self) -> None:
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
                    if(key == "a"): pass
                    elif(key == "d"): pass
                    elif(key == "w"): pass
                    elif(key == "e"): pass
                    elif(key == "left"): pass
                    elif(key == "right"): pass
                    elif(key == "up"): pass
                    elif(key == "right ctrl"): pass
                    elif(key == "space"): pass
                    # Dipswitches(they don't need a keyup event) and exit:
                    elif(key == "return"): pass
                    elif(key == "`"): pass
                    elif(key == "1"): pass
                    elif(key == "2"): pass
                    elif(key == "3"): pass
                    elif(key == "4"): pass
                    elif(key == "5"): pass
                    elif(key == "6"): pass
                    elif(key == "7"): pass
                    elif(key == "escape"): self.running = False
                case pygame.KEYUP:
                    key = pygame.key.name(event.key)
                    if(key == "a"): pass
                    elif(key == "d"): pass
                    elif(key == "w"): pass
                    elif(key == "e"): pass
                    elif(key == "left"): pass
                    elif(key == "right"): pass
                    elif(key == "up"): pass
                    elif(key == "right ctrl"): pass
                    elif(key == "space"): pass
                    elif(key == "return"): pass
                case pygame.QUIT:
                    self.running = False
