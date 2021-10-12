from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from uatg.utils import rvtest_data
from typing import Dict, Any
from random import randint


class uatg_decoder_arithmetic_insts_1(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    add-sub register register instructions.
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.isa_load = 'lw'
        self.load_inc = 4
        self.num_rand_var = 100

    def execute(self, _decoder_dict) -> bool:
        self.isa = _decoder_dict['isa']
        for (i, j, k) in [('rv32', 'lw', 4), ('rv64', 'ld', 8),
                          ('rv128', 'lq', 16)]:
            if i in self.isa.lower():
                self.isa_bit = i
                self.isa_load = j
                self.load_inc = k
        return True

    def generate_asm(self) -> Dict[str, str]:
        """x
            Generates the ASM instructions for R type arithmetic instructions.
            It creates asm for the following instructions based upon ISA
                add, addw, addd, sub, subw, subd
        """
        asm_data = rvtest_data(bit_width=int(self.isa_bit[2:]),
                               random=True,
                               num_vals=self.num_rand_var,
                               signed=False,
                               align=4)

        reg_file = base_reg_file.copy()
        reg_file.remove('x1')  # Removing X1 register to store Offset address

        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in arithmetic_instructions['rv32-add-reg']

        asm_code = '#' * 5 + ' add/sub reg, reg, reg ' + '#' * 5 + '\n'
        asm_code += 'la x1, DATA_SEC\n'

        for rd in reg_file:
            for rs1 in reg_file:
                for rs2 in reg_file:
                    assert isinstance(arithmetic_instructions, dict)
                    for inst in arithmetic_instructions[
                        f'{self.isa_bit}-add-reg']:
                        asm_code += f'{self.isa_load} {rs1}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                    f'{self.isa_load} {rs2}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                    f'{inst} {rd}, {rs1}, {rs2}\n'
        return {'asm_code': asm_code, 'asm_data': asm_data}

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
