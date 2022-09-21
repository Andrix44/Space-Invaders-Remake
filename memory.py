

class Memory:
    def __init__(self) -> None:
        self.mem = bytearray()

    def LoadRom(self, rom_path) -> None:
        with open(rom_path, 'rb') as f:
            data = f.read()
            if(len(data) == 0x5ad and data[3:0x45] == b"MICROCOSM ASSOCIATES 8080/8085 CPU DIAGNOSTIC VERSION 1.0 (C) 1980"):
                self.mem.extend(bytearray(0x100))
                self.mem.extend(data)
            else:
                self.mem.extend(bytearray(data))
        self.mem.extend(bytearray(0x4000 - len(self.mem)))
