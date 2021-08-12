# python program to generate an assembly file which checks if mis-predictions
# occur In addition to this, the GHR is also filled with ones (additional
# test case) uses assembly macros

# To-Do -> Create another function which prints the includes and other
# assembler directives complying to the test format spec

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from configparser import ConfigParser

class decompressor(IPlugin):

    def __init__(self):
        super().__init__()
        pass

    def execute(self, _bpu_dict):
        return True
    
    def generate_asm(self):
        """This function will return all the compressed instructions"""
        asm = "\n\n## test: decompressor ##\n\n"
        asm += """##LOAD INSTRUCTIONS CI FORMAT

#c.lwsp x3, 8(x2) ## load word stack pointer scaled by 4

#c.ldsp x4, 64(x2) ## load double word stack pointer scaled by 8 (RV64C/128C)

#c.flwsp x6, 16(x2) ## single precision floating point scaled by 4(32FC)

#c.fldsp x7, 24(x2) ## double precision floating point scaled by 8 (RV32DC/RV64DC)

##STORE INSTRUCTIONS CSS FORMAT

#C.swsp x3, 20(x2) ## store word stack pointer scaled by 4

#c.sdsp x4, 32(x2) ## store double stack pointer scaled by 8(RV64C/RV128C)

#c.fswsp x6, 24(x2) ## single precision floating point scaled by 4(RV32C)

#c.fsdsp x7, 16(x2) ## double precision floating point scaled by 8 (RV32DC/RV64DC)

##REGISTER BASED LOAD INSTRUCTIONS CL FORMAT

#c.lw x8, 16(x9) ## load word scaled by 4

#c.ld x9, 24(x10) ## load double word scaled by 8(RV64C/128C)

#c.flw f8, 40(x8) ## single precision floating point scaled by 4(RV32FC)

#c.fld f9, 32(x9) ## double precision floating point scaled by 8 (RV32DC/RV64DC)

## REGISTER BASED STORE INSTRUCTIONS CS FORMAT

#c.sw x8, 8(x9) ##store word scaled by 4

#c.sd x9, 80(x10) ##store double scaled by 8 (64C/128C)

#c.fsw f11, 40(x12) ##single precision floating point scaled by 4(RV32FC)

#c.fsd f12, 88(x13) ##double precision floating point scaled by 8 (RV32DC/RV64DC)

## CONTROL TRANSFER INSTRUCTIONS

#c.j x0,6 ##jump instructions

#c.jal x1,22 ## jump and link instructions (RV32C)

#c.jr x0, 0(x3) ## jump register -CR format

#c.jalr x1, 0(x4) ## jump and link register-CR format

#c.beqz x0,7 ##branch equal to zero instruction -CB format

#c.bnez x9,6 ##branch not equal to zero - CB format

##INTEGER COMPUTATIONAL INSTRUCTIONS

#c.li x3,5 ##load instructions

#c.lui x3,4 ## load unsigned instructions

## INTEGER REGISTER IMMEDIATE INSTRUCTIONS

c.addi x3,7 ## add instructions (CI format)

c.addiw x4,8 ## add instruction (RV64C/128C)

#c.addi16sp x2,200 ## add stack pointer instruction

#c.addi4spn x7, x2,8 ## stack pointer scaled by 4 (CIW format)

#c.slli x3, 64 ## logical left shift instruction (CI format)

#c.srli x8, 64 ## logical right shift (CB format)

#c.srai x9,96 ## arithmetic right shift (CB format)

c.andi x9,16 ## bitwise AND (CB format)

##INTEGER REGISTER-REGISTER INSTRUCTIONS

c.mv x3, x4 ## move (CR format)

c.add x3, x5 ## add (CR format)

c.and x8, x9 ## bitwise AND (CA format)

c.or x8, x10 ##bitwise OR (CA format)

c.xor x8, x11 ##bitwise xor (CA format)

c.sub x8, x12 ## bitwise sub (CA format)

c.addw x9, x10 ## (RV64C/128C) (CA format)

c.subw x9, x11 ## (RV64C/128C) (CA format)\n"""

        return asm

    def check_log(self):
        return None
