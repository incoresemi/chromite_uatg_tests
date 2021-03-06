# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file
from typing import Dict, List, Union, Any


class uatg_bypass_mul_load_store(IPlugin):

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
        Branch operation happens if bypass doesn't happen correctly
        Bypassing checked for muldiv ISA alu operation
        Bypassing checked for load/store instructions as well
        """

        reg_file = base_reg_file.copy()
        asm = f"\tla {reg_file[1]} ,sample_data\n\taddi {reg_file[2]} ," \
              f"{reg_file[0]} ,5\n\taddi {reg_file[3]} ,{reg_file[0]} ,7\n\t" \
              f"addi {reg_file[4]} ,{reg_file[0]} ,1\n\t" \
              f"mul {reg_file[4]} ,{reg_file[2]} ,{reg_file[3]}\n"
        # a multi-cycle instruction
        asm += f"\tsw {reg_file[4]} ,4({reg_file[1]})\n"
        # store the product into memory

        asm += f"\tlw {reg_file[5]} ,4({reg_file[1]})\n"
        # load the stored product from the memory
        asm += f"\taddi {reg_file[6]} ,{reg_file[0]} ,35\n"
        # store the product(5*7) to verify in the next step

        asm += f"\tbeq {reg_file[5]} ,{reg_file[6]} ,flag\n"
        asm += "\tj end\nflag:\n\taddi {reg_file[7]} ,{reg_file[0]} ,10\n"
        asm += "end:\n\tfence.i\n"
        # if this branch is taken then it implies that
        # bypassing hasn't happened properly

        # compile macros for the test
        compile_macros = []

        # return asm_code and sig_code
        yield({
            'asm_code': asm,
            # 'asm_data': '',
            'asm_sig': '',
            'compile_macros': compile_macros,
            # 'name_postfix': inst
        })
