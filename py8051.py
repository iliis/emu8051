#!/bin/env python3

from py8051core import ffi, lib


@ffi.def_extern()
def em8051exception_callback(aCPU, aCode):
    if aCode == -1:
        raise Exception("Breakpoint reached") # TODO: call callback or something here
    elif aCode == lib.EXCEPTION_STACK:
        raise Exception("SP exception: stack address > 127 with no upper memory, or SP roll over.")
    elif aCode == lib.EXCEPTION_ACC_TO_A:
        raise Exception("Invalid operation: acc-to-a move operation")
    elif aCode == lib.EXCEPTION_IRET_PSW_MISMATCH:
        raise Exception("PSW not preserved over interrupt call")
    elif aCode == lib.EXCEPTION_IRET_SP_MISMATCH:
        raise Exception("SP not preserved over interrupt call")
    elif aCode == lib.EXCEPTION_IRET_ACC_MISMATCH:
        raise Exception("ACC not preserved over interrupt call")
    elif aCode == lib.EXCEPTION_ILLEGAL_OPCODE:
        raise Exception("Invalid opcode: 0xA5 encountered")
    else:
        raise Exception("Unknown exception")

@ffi.def_extern()
def em8051sfrread_callback(aCPU, aRegister):
    pass

@ffi.def_extern()
def em8051sfrwrite_callback(aCPU, aRegister):
    pass

@ffi.def_extern()
def em8051xwrite_callback(aCPU, aAddress, aValue):
    pass

@ffi.def_extern()
def em8051xread_callback(aCPU, aAddress):
    pass



class Emulator8051:

    def __init__(self, aCPU = None):

        if aCPU:
            self.emu = aCPU
            return

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

        self.emu.except_cb = lib.em8051exception_callback
        # no callback = default behaviour = read from internal memory
        #self.emu.sfrread   = lib.em8051sfrread_callback

        lib.reset(self.emu, 1)

    def reset(self, wipeMemory = False):
        if wipeMemory:
            lib.reset(self.emu, 1)
        else:
            lib.reset(self.emu, 0)


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


    def ACC(self):
        return self.SFR[lib.REG_ACC]

    def PSW(self):
        return self.SFR[lib.REG_PSW]

    # convenience function to access current register bank
    def r(self, n):

        if n < 0 or n > 7:
            raise ValueError("Invalid register index: " + str(n))

        RX_ADDRESS = n + 8 * ((int.from_bytes(self.PSW(), byteorder='little') & (lib.PSWMASK_RS0|lib.PSWMASK_RS1))>>lib.PSW_RS0)
        return self.lower_data[RX_ADDRESS]



if __name__ == "__main__":
    e = Emulator8051()
    e.loadHEX("test.ihx")

    while e.lower_data[0x60] != b'\xFA':
        print(e.ACC(), e.r(0), e.r(1), e.r(2))
        e.step()

    print(hex(ord(e.lower_data[0x60])))

    print(lib.REG_ACC)
