from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions


class uatg_decoder_arith_insts_2(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    arithmetic shift register register instructions.
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
            Generates the ASM instructions for R type shift instructions.
            It creates asm for the following instructions based upon the ISA
                sll, sra, srl, sllw, sraw, srlw slld, srad', srld
        """

        # For all rd, rs1, rs2 iterate through the 32 register combinations for
        # every instruction in arithmetic_instructions['rv32-shift-reg']
        asm = '\n\n' + '#' * 5 + ' shift_inst reg, reg, reg ' + '#' * 5 + '\n'

        for inst in arithmetic_instructions[f'{self.isa_bit}-shift-reg']:
            for rd in base_reg_file:
                for rs in base_reg_file:
                    for sh_amt in range(0, 2 ** 5 - 1):
                        asm += f'{inst} {rd}, {rs}, {sh_amt}\n'

        return asm

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv
