import pygame

from audio import Audio
from cpu import CPU
from memory import Memory


class Emulator:
    def __init__(self, rom_path) -> None:
        pygame.init()

        self.audio = Audio()
        self.cpu = CPU()
        self.mem = Memory()

        self.mem.LoadRom(rom_path)
        pass
