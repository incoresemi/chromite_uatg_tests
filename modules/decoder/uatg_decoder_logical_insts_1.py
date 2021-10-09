from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, logic_instructions
from uatg.utils import rvtest_data


class uatg_decoder_logical_insts_1(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    logical register register instructions.
    """

    def __init__(self) -> None:
        super().__init__()

    def execute(self, _decoder_dict) -> bool:
        # Since logical register instructions exist in all RISCV implementations
        # return True always
        return True

    def generate_asm(self) -> str:
        """
            Generates the ASM instructions for logical register instructions.
            It creates asm for the following instructions based upon ISA
            and, or, slt, sltu, xor
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in logical_instructions['logic-reg']

        asm_code = '#' * 5 + ' and/or/xor/slt.. reg, reg, reg ' + '#' * 5 + '\n'
        for rd in base_reg_file:
            for rs1 in base_reg_file:
                for rs2 in base_reg_file:
                    assert isinstance(logic_instructions, dict)
                    for inst in logic_instructions['logic-reg']:
                        asm_code += f'{inst} {rd}, {rs1}, {rs2}\n'
        return asm_code

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
