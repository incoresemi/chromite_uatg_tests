# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from typing import Dict, List, Union, Any

from uatg.instruction_constants import base_reg_file
from yapsy.IPlugin import IPlugin


class uatg_regfiles_r1(IPlugin):

    def __init__(self) -> None:
        super().__init__()
        self.offset_inc = None
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.xlen = 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        if 'RV32' in self.isa:
            self.isa_bit = 'rv32'
            self.xlen = 32
            self.offset_inc = 4
        else:
            self.isa_bit = 'rv64'
            self.xlen = 64
            self.offset_inc = 8
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Checking hardwired value of x0
        branch taken if value of x0 not 0
        x7 = 10 if x0 not equal to 0
        """

        reg_file = base_reg_file.copy()
        asm = f"\taddi {reg_file[1]},{reg_file[0]} ,0\n"
        # to store zero in another register used later for comparision
        asm += f"\taddi {reg_file[4]},{reg_file[0]} ,2\n"
        # initializing a temporary register (iterative variable)
        asm += f"\taddi {reg_file[5]},{reg_file[0]} ,20\n"
        # initializing a temporary register (to end for loop)

        asm += f"\tsub {reg_file[31]}, {reg_file[0]}, {reg_file[0]}\n\t" \
               f"bnez {reg_file[31]}, flag\nfor:\n\tbeq x4,x5, end_for\n\t" \
               f"add {reg_file[0]},{reg_file[0]},{reg_file[4]}\n\t" \
               f"addi {reg_file[4]},{reg_file[4]},2\n\tj for\nend_for:\n\t" \
               f"bne {reg_file[0]},{reg_file[1]},flag\n"
        # if the register zero takes a nonzero value then ,
        # register7 takes the value of 10
        # thus giving us the indication of bug!!
        asm += "\tj end\nflag:\n\taddi {reg_file[7]},{reg_file[1]},10\n" \
               "end:\n\tfence.i\n"

        # compile macros for the test

        # return asm_code and sig_code
        yield ({
            'asm_code': asm,
            'asm_sig': '',
            'compile_macros': []
        })
