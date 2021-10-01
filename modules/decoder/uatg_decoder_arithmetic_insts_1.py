from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions


class uatg_decoder_arithmetic_insts_1(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    add-sub register register instructions.
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
            It creates asm for the following instructions based upon ISA
                add, addw, addd, sub, subw, subd
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in arithmetic_instructions['rv32-add-reg']

        asm = '#'*5 + ' add/sub reg, reg, reg ' + '#'*5 + '\n'
        for rd in base_reg_file:
            for rs1 in base_reg_file:
                for rs2 in base_reg_file:
                    assert isinstance(arithmetic_instructions, dict)
                    for inst in arithmetic_instructions[
                                                     f'{self.isa_bit}-add-reg']:
                        asm += f'{inst} {rd}, {rs1}, {rs2}\n'
        return asm

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv
