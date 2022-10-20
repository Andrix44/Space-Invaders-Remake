from argparse import ArgumentParser 

from emulator import Emulator


if __name__ == "__main__":
    argp = ArgumentParser("python main.py")
    argp.add_argument("rompath", type=str, help="Path to the ROM file")
    argp.add_argument("--debug", action="store_true")
    args = argp.parse_args()
    
    emu = Emulator(args.rompath, args.debug)
    emu.Run()
