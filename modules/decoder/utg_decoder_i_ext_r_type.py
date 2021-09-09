from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from random import randint


class utg_decoder_arith_tests(IPlugin):

    def __init__(self) -> None:
        pass

    def execute(self, _null) -> bool:
        return True

    def generate_asm(self) -> str:
        """
            Generates the ASM file containing R type instructions present in the I extension"
        """
        asm = '#'*5 + ' add/sub reg, reg, reg ' + '#'*5 + '\n'
        for inst in arithmetic_instructions['add-sub-reg']:
            for rd in base_reg_file:
                for rs1 in base_reg_file:
                    for rs2 in base_reg_file:
                        asm += f'{inst} {rd}, {rs1}, {rs2}\n'
        asm = '\n' * 2 + '#' * 5 + ' shift_inst reg, reg, reg ' + '#' * 5 + '\n'
        for inst in arithmetic_instructions['shift-rl-reg']:
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
