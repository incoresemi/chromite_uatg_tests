# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from typing import Dict, List, Union, Any

from uatg.instruction_constants import base_reg_file
from yapsy.IPlugin import IPlugin


class uatg_bypass_trap(IPlugin):

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
        Checking pipeline flushes and invoking 
        trap handler by creating misaligned loads
        """

        reg_file = base_reg_file.copy()
        asm = f"\tla {reg_file[1]} ,sample_data\n\taddi " \
              f"{reg_file[2]},{reg_file[0]} ,5\n"
        # initializing register x2
        asm += f"\taddi {reg_file[3]},{reg_file[0]} ,7\n"
        # initializing register x3
        asm += f"\tandi {reg_file[31]} ,{reg_file[0]} ,0\n"
        # clearing the bits in register x31
        asm += f"\tmul {reg_file[8]} ,{reg_file[3]} ,{reg_file[2]}\n"
        # x8<-- 7*5=35
        asm += f"\tlw {reg_file[5]} ,0({reg_file[1]})\n"
        # expected address misalign --> jumps to trap handler -->
        # expected pipeline flush
        asm += f"\tsra {reg_file[31]} ,{reg_file[8]} ,{reg_file[2]}\n"
        # Signature register should store arithmetic right shifted '35' by
        # 5 bits if the trap wasn't taken.
        # if the misaligned trap is taken,
        # then it'll have the reset  values (expected)
        asm += f"\tbnez {reg_file[31]}, flag\n\tj end\nflag:\n\t" \
               f"addi {reg_file[7]} ,{reg_file[0]} ,10\nend:\n\tfence.i\n"

        # return asm_code and sig_code
        yield ({
            'asm_code': asm,
            'asm_sig': '',
            'compile_macros': []
        })
