#!/bin/env python3

# requires cffi >= 1.4 (install with pip to get a up-to-date version!)

from cffi import FFI
builder = FFI()

builder.set_source("py8051core", """
#include "emu8051.h"
""", sources=["core.c", "opcodes.c", "disasm.c"])

builder.cdef("""
struct em8051;

// Operation: returns number of ticks the operation should take
typedef int (*em8051operation)(struct em8051 *aCPU); 

// Decodes opcode at position, and fills the buffer with the assembler code. 
// Returns how many bytes the opcode takes.
typedef int (*em8051decoder)(struct em8051 *aCPU, int aPosition, char *aBuffer);

// Callback: some exceptional situation occurred. See EM8051_EXCEPTION enum, below
typedef void (*em8051exception)(struct em8051 *aCPU, int aCode);

// Callback: an SFR register is about to be read (not called for 'a' ops nor psw changes)
// Default is to return the value in the SFR register. Ports may act differently.
typedef int (*em8051sfrread)(struct em8051 *aCPU, int aRegister);

// Callback: an SFR register has changed (not called for 'a' ops)
// Default is to do nothing
typedef void (*em8051sfrwrite)(struct em8051 *aCPU, int aRegister);

// Callback: writing to external memory
// Default is to update external memory
// (can be used to control some peripherals)
typedef void (*em8051xwrite)(struct em8051 *aCPU, int aAddress, int aValue);

// Callback: reading from external memory
// Default is to return the value in external memory 
// (can be used to control some peripherals)
typedef int (*em8051xread)(struct em8051 *aCPU, int aAddress);


struct em8051
{
    unsigned char *mCodeMem; // 1k - 64k, must be power of 2
    int mCodeMemSize; 
    unsigned char *mExtData; // 0 - 64k, must be power of 2
    int mExtDataSize;
    unsigned char *mLowerData; // 128 bytes
    unsigned char *mUpperData; // 0 or 128 bytes; leave to NULL if none
    unsigned char *mSFR; // 128 bytes; (special function registers)
    int mPC; // Program Counter; outside memory area
    int mTickDelay; // How many ticks should we delay before continuing
    em8051operation op[256]; // function pointers to opcode handlers
    em8051decoder dec[256]; // opcode-to-string decoder handlers    
    em8051exception except_cb; // callback: exceptional situation occurred
    em8051sfrread sfrread; // callback: SFR register being read
    em8051sfrwrite sfrwrite; // callback: SFR register written
    em8051xread xread; // callback: external memory being read
    em8051xwrite xwrite; // callback: external memory being written

    // Internal values for interrupt services etc.
    int mInterruptActive;
    // Stored register values for interrupts (exception checking)
    int int_a[2];
    int int_psw[2];
    int int_sp[2];
};

// set the emulator into reset state. Must be called before tick(), as
// it also initializes the function pointers. aWipe tells whether to reset
// all memory to zero.
void reset(struct em8051 *aCPU, int aWipe);

// run one emulator tick, or 12 hardware clock cycles.
// returns 1 if a new operation was executed.
int tick(struct em8051 *aCPU);

// decode the next operation as character string.
// buffer must be big enough (64 bytes is very safe). 
// Returns length of opcode.
int decode(struct em8051 *aCPU, int aPosition, unsigned char *aBuffer);

// Load an intel hex format object file. Returns negative for errors.
int load_obj(struct em8051 *aCPU, char *aFilename);

// Alternate way to execute an opcode (switch-structure instead of function pointers)
int do_op(struct em8051 *aCPU);


enum EM8051_EXCEPTION
{
    EXCEPTION_STACK,  // stack address > 127 with no upper memory, or roll over
    EXCEPTION_ACC_TO_A, // acc-to-a move operation; illegal (acc-to-acc is ok, a-to-acc is ok..)
    EXCEPTION_IRET_PSW_MISMATCH, // psw not preserved over interrupt call (doesn't care about P, F0 or UNUSED)
    EXCEPTION_IRET_SP_MISMATCH,  // sp not preserved over interrupt call
    EXCEPTION_IRET_ACC_MISMATCH, // acc not preserved over interrupt call
    EXCEPTION_ILLEGAL_OPCODE     // for the single 'reserved' opcode in the architecture
};

// SFR register locations
enum SFR_REGS
{
    REG_ACC  =  """ + str(0xE0 - 0x80) + """,
    REG_B    =  """ + str(0xF0 - 0x80) + """,
    REG_PSW  =  """ + str(0xD0 - 0x80) + """,
    REG_SP   =  """ + str(0x81 - 0x80) + """,
    REG_DPL  =  """ + str(0x82 - 0x80) + """,
    REG_DPH  =  """ + str(0x83 - 0x80) + """,
    REG_P0   =  """ + str(0x80 - 0x80) + """,
    REG_P1   =  """ + str(0x90 - 0x80) + """,
    REG_P2   =  """ + str(0xA0 - 0x80) + """,
    REG_P3   =  """ + str(0xB0 - 0x80) + """,
    REG_IP   =  """ + str(0xB8 - 0x80) + """,
    REG_IE   =  """ + str(0xA8 - 0x80) + """,
    REG_TMOD =  """ + str(0x89 - 0x80) + """,
    REG_TCON =  """ + str(0x88 - 0x80) + """,
    REG_TH0  =  """ + str(0x8C - 0x80) + """,
    REG_TL0  =  """ + str(0x8A - 0x80) + """,
    REG_TH1  =  """ + str(0x8D - 0x80) + """,
    REG_TL1  =  """ + str(0x8B - 0x80) + """,
    REG_SCON =  """ + str(0x98 - 0x80) + """,
    REG_PCON =  """ + str(0x87 - 0x80) + """
};

enum PSW_BITS
{
    PSW_P = 0,
    PSW_UNUSED = 1,
    PSW_OV = 2,
    PSW_RS0 = 3,
    PSW_RS1 = 4,
    PSW_F0 = 5,
    PSW_AC = 6,
    PSW_C = 7
};

enum PSW_MASKS
{
    PSWMASK_P = 0x01,
    PSWMASK_UNUSED = 0x02,
    PSWMASK_OV = 0x04,
    PSWMASK_RS0 = 0x08,
    PSWMASK_RS1 = 0x10,
    PSWMASK_F0 = 0x20,
    PSWMASK_AC = 0x40,
    PSWMASK_C = 0x80
};


// Callbacks into python

// Callback: some exceptional situation occurred. See EM8051_EXCEPTION enum, below
extern "Python" void em8051exception_callback(struct em8051 *aCPU, int aCode);

// Callback: an SFR register is about to be read (not called for 'a' ops nor psw changes)
// Default is to return the value in the SFR register. Ports may act differently.
extern "Python" int em8051sfrread_callback(struct em8051 *aCPU, int aRegister);

// Callback: an SFR register has changed (not called for 'a' ops)
// Default is to do nothing
extern "Python" void em8051sfrwrite_callback(struct em8051 *aCPU, int aRegister);

// Callback: writing to external memory
// Default is to update external memory
// (can be used to control some peripherals)
extern "Python" void em8051xwrite_callback(struct em8051 *aCPU, int aAddress, int aValue);

// Callback: reading from external memory
// Default is to return the value in external memory 
// (can be used to control some peripherals)
extern "Python" int em8051xread_callback(struct em8051 *aCPU, int aAddress);

""")

if __name__ == "__main__":
    builder.compile(verbose=True)
