from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from uatg.utils import rvtest_data
from typing import Tuple, Any
from random import randint


class uatg_decoder_arithmetic_insts_4(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    ADD immediate instructions.
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

    def generate_asm(self) -> Tuple[str, Any]:
        """
            Generates the ASM instructions for R type arithmetic instructions.
            It creates asm for the following instructions (based upon input isa)
                addi', 'addiw', 'addid
        """
        # Iterate through the 32 register combinations and all 32/64 shift
        # for every instruction in arithmetic_instructions['rv32-shift-imm']

        asm_data = rvtest_data(bit_width=int(self.isa_bit[2:]), random=True,
                               num_vals=self.num_rand_var, signed=False,
                               align=4)

        reg_file = base_reg_file.copy()
        reg_file.remove('x1')  # Removing X1 register to store Offset address

        asm_code = '\n\n' + '#' * 5 + 'Shift immediate insts' + '#' * 5 + '\n'
        asm_code += 'la x1, DATA_SEC\n'

        for rd in reg_file:
            for rs in reg_file:
                for inst in arithmetic_instructions[f'{self.isa_bit}-shift-' \
                                                    f'imm']:
                    if self.isa_bit == 'rv32':
                        for imm_val in range(32):
                            asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                        f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                        f'{inst} {rd}, {rs}, {imm_val}\n'

                    elif self.isa_bit == 'rv64':
                        if inst[-1] == 'w':
                            for imm_val in range(32):
                                asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'i':
                            for imm_val in range(64):
                                asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{inst} {rd}, {rs}, {imm_val}\n'

                    if self.isa_bit == 'rv128':
                        if inst[-1] == 'w':
                            for imm_val in range(32):
                                asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'd':
                            for imm_val in range(64):
                                asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'i':
                            for imm_val in range(128):
                                asm_code += f'{self.isa_load} {rd}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{self.isa_load} {rs}, {randint(0, self.num_rand_var) * self.load_inc}(x1)\n' \
                                            f'{inst} {rd}, {rs}, {imm_val}\n'

        return asm_code, asm_data

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
