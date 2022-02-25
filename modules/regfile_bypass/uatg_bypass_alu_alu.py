# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from typing import Dict, List, Union, Any

from uatg.instruction_constants import base_reg_file
from yapsy.IPlugin import IPlugin


class uatg_bypass_alu_alu(IPlugin):

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
        Bypassing checked for base ISA alu operation
        """

        reg_file = base_reg_file.copy()
        asm = f"\taddi {reg_file[1]} ,{reg_file[0]} ,4\n\t" \
              f"addi {reg_file[2]} ,{reg_file[0]} ,5\n\t" \
              f"addi {reg_file[3]} ,{reg_file[0]} ,2\n\t" \
              f"add {reg_file[3]} ,{reg_file[1]} ,{reg_file[2]}\n\t" \
              f"add {reg_file[4]} ,{reg_file[3]} ,{reg_file[2]}\n" \
              f"\taddi {reg_file[5]} ,{reg_file[0]} ,14\n\t" \
              f"beq {reg_file[5]} ,{reg_file[4]} ,flag\n\tj end\nflag:\n\t" \
              f"addi {reg_file[7]} ,{reg_file[0]} ,10\nend:\n\tfence.i\n"
        # if this branch is taken then it implies that
        # bypassing hasn't happened properly

        # compile macros for the test
        compile_macros = []

        # return asm_code and sig_code
        yield ({
            'asm_code': asm,
            'asm_sig': '',
            'compile_macros': compile_macros,
        })
