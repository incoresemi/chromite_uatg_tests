from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions,\
    bit_walker


class uatg_decoder_arithmetic_insts_3(IPlugin):
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
        # Iterate through the 32 register combinations and 12-bit walking ones
        # for every instruction in arithmetic_instructions['rv32-add-imm']
        asm = '\n\n' + '#' * 5 + 'ADDI, ADDIW immediate insts' + '#' * 5 + '\n'
        for inst in arithmetic_instructions[f'{self.isa_bit}-add-imm']:
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
