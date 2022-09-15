

class Memory:
    def __init__(self) -> None:
        self.mem = None

    def LoadRom(self, rom_path) -> None:
        self.mem = bytearray(open(rom_path, 'rb').read())
        self.mem.extend(bytearray(0x4000 - len(self.mem)))
