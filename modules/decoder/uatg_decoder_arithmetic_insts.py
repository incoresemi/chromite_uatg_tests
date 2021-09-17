from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions,\
    bit_walker


class uatg_decoder_arith_tests(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    arithmetic instructions.
    """
    # TODO: Find way to pass ISA to tests Presently hardcoded to RV32
    def __init__(self) -> None:
        super().__init__()

    def execute(self, _null) -> bool:
        return True

    def generate_asm(self) -> str:
        """
            Generates the ASM instructions for R type arithmetic instructions.

            Presently it creates asm for
                add rd, rs1, rs2
                sub rd, rs1, rs2
                sll rd, rs1, rs2
                sllw rd, rs1, rs2
                sra rd, rs1, rs2
                sraw rd, rs1, rs2
                srl rd, rs1, rs2
                srlw rd, rs1, rs2
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in arithmetic_instructions['rv32-add-reg']

        asm = '#'*5 + ' add/sub reg, reg, reg ' + '#'*5 + '\n'
        for rd in base_reg_file:
            for rs1 in base_reg_file:
                for rs2 in base_reg_file:
                    for inst in arithmetic_instructions['rv32-add-reg']:
                        asm += f'{inst} {rd}, {rs1}, {rs2}\n'

        # Again rd, rs1, rs2 iterate through the 32 register combinations for
        # every instruction in arithmetic_instructions['rv32-shift-reg']
        asm += '\n\n' + '#' * 5 + ' shift_inst reg, reg, reg ' + '#' * 5 + '\n'

        for inst in arithmetic_instructions['rv32-shift-reg']:
            for rd in base_reg_file:
                for rs in base_reg_file:
                    for sh_amt in range(0, 2 ** 5 - 1):
                        asm += f'{inst} {rd}, {rs}, {sh_amt}\n'

        # Iterate through the 32 register combinations and 12-bit walking ones
        # for every instruction in arithmetic_instructions['rv32-add-imm']
        asm += '\n\n' + '#' * 5 + 'ADDI, ADDIW immediate insts' + '#' * 5 + '\n'
        for inst in arithmetic_instructions['rv32-add-imm']:
            # Bit walking through 11 bits for immediate field
            imm = [val for i in range(1, 8) for val in
                   bit_walker(bit_width=11, n_ones=i, invert=False)]
            for rd in base_reg_file:
                for rs in base_reg_file:
                    for imm_val in imm:
                        asm += f'{inst} {rd}, {rs}, {imm_val}\n'
        return asm

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv
