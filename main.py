from emulator import Emulator


if __name__ == "__main__":
    #rom_path = "./ROMS/cpudiag.rom"
    rom_path = "./ROMS/Space Invaders.rom"
    emu = Emulator(rom_path)
    emu.Run()
    pass
