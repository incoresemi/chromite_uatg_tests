from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from uatg.utils import rvtest_data


class uatg_decoder_arith_insts_4(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    ADD immediate instructions.
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'

    def execute(self, _decoder_dict) -> bool:
        self.isa = _decoder_dict['isa']
        for i in ['rv32', 'rv64', 'rv128']:
            if i in self.isa.lower():
                self.isa_bit = i
        return True

    def generate_asm(self) -> str:
        """
            Generates the ASM instructions for R type arithmetic instructions.
            It creates asm for the following instructions (based upon input isa)
                addi', 'addiw', 'addid
        """
        # Iterate through the 32 register combinations and all 32/64 shift
        # for every instruction in arithmetic_instructions['rv32-shift-imm']
        asm = '\n\n' + '#' * 5 + 'Shift immediate insts' + '#' * 5 + '\n'
        for rd in base_reg_file:
            for rs in base_reg_file:
                for inst in arithmetic_instructions[f'{self.isa_bit}-shift-' \
                                                    f'imm']:
                    if self.isa_bit == 'rv32':
                        for imm_val in range(32):
                            asm += f'la {rs}, RAND_VAL\n' \
                                   f'{inst} {rd}, {rs}, {imm_val}\n'

                    elif self.isa_bit == 'rv64':
                        if inst[-1] == 'w':
                            for imm_val in range(32):
                                asm += f'la {rs}, RAND_VAL\n' \
                                       f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'i':
                            for imm_val in range(64):
                                asm += f'la {rs}, sample_data\n' \
                                       f'{inst} {rd}, {rs}, {imm_val}\n'

                    if self.isa_bit == 'rv128':
                        if inst[-1] == 'w':
                            for imm_val in range(32):
                                asm += f'la {rs}, sample_data\n' \
                                       f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'd':
                            for imm_val in range(64):
                                asm += f'la {rs}, sample_data\n' \
                                       f'{inst} {rd}, {rs}, {imm_val}\n'
                        if inst[-1] == 'i':
                            for imm_val in range(128):
                                asm += f'la {rs}, sample_data\n' \
                                       f'{inst} {rd}, {rs}, {imm_val}\n'

        asm += '\nRVTEST_CODE_END\nRVMODEL_HALT\n\n' + '\nRVTEST_DATA_BEGIN\n'
        asm += rvtest_data(bit_width=32, num_vals=5, random=True, signed=False,
                           align=4) + '\nRVTEST_DATA_END\n\n'
        return asm

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv
