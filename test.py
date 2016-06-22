#!/bin/env python3

from py8051 import ffi, lib

class Emulator:

    def __init__(self):
        self.emu = ffi.new("struct em8051 *")

        self.code_memory = ffi.new("char[65536]")
        self.ext_memory  = ffi.new("char[65536]")

        self.emu.mCodeMem = self.code_memory
        self.emu.mCodeMemSize = 65536
        self.emu.mExtData = self.ext_memory
        self.emu.mExtDataSize = 65536

        self.lower_data = ffi.new("char[128]")
        self.upper_data = ffi.new("char[128]")
        self.SFR        = ffi.new("char[128]")

        self.emu.mLowerData = self.lower_data
        self.emu.mUpperData = self.upper_data
        self.emu.mSFR       = self.SFR

        # TODO: initialize callbacks!

        lib.reset(self.emu, 1)


    def loadHEX(self, filename):
        result = lib.load_obj(self.emu, filename.encode('ascii'));

        if result == -1:
            raise IOError("File not found.")
        elif result == -2:
            raise IOError("Bad file format.")
        elif result == -3:
            raise IOError("Unsupported HEX file version.")
        elif result == -4:
            raise IOError("Checksum failure.")
        elif result == -5:
            raise IOError("No end of data marker found.")


    def tick(self):
        return lib.tick(self.emu)

    def step(self, instructions=1):
        while instructions > 0:
            if self.tick() > 0:
                instructions -= 1


if __name__ == "__main__":
    e = Emulator()
    e.loadHEX("[INSERT SOME HEX FILE HERE]")

    while e.lower_data[0x60] == b'\x00':
        e.step()

    print(hex(ord(e.lower_data[0x60])))
