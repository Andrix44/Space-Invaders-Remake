

class Memory:
    """The emulator's memory module, mostly just a bytearray with ROM loading in the constructor"""
    def __init__(self, rom_path: str, debug: bool) -> None:
        self.mem = bytearray()
        with open(rom_path, 'rb') as f:
            data = f.read()
            if(debug): # 
                self.mem.extend(bytearray(0x100))
                self.mem.extend(data)
                self.mem[0x5] = 0xc9 # RET
            else:
                self.mem.extend(bytearray(data))
        self.mem.extend(bytearray(0x4000 - len(self.mem)))
