from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions, \
    bit_walker
from typing import Dict, List, Union, Any
import random


class uatg_decoder_arithmetic_insts_ui(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    ADD immediate instructions.
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100

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
            Generates the ASM instructions for R type arithmetic instructions.
            It creates asm for the following instructions (based upon input isa)
                auipc, lui
        """
        reg_file = base_reg_file.copy()

        test_dict = []

        inst_count = 0

        for inst in arithmetic_instructions[f'{self.isa_bit}-ui']:

            asm_code = '\n\n' + '#' * 5 + ' auipc/lui reg ' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x31'

            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            # Bit walking through 11 bits for immediate field
            imm = [
                val for i in range(1, 4)
                for val in bit_walker(bit_width=20, n_ones=i, invert=False,
                                      signed=False)
            ]
            imm = imm + [
                val for i in range(1, 4)
                for val in bit_walker(bit_width=20, n_ones=i, invert=True,
                                      signed=False)
            ]
            for rd in reg_file:
                for imm_val in imm:

                    # if signature register needs to be used for operations
                    # then first choose a new signature pointer and move the
                    # value to it.
                    if swreg in [rd]:
                        newswreg = random.choice(
                            [x for x in reg_file if x not in [rd, 'x0']])
                        asm_code += f'mv {newswreg}, {swreg}\n'
                        swreg = newswreg

                    # perform the  required assembly operation
                    asm_code += f'\ninst_{inst_count}:'
                    asm_code += f'\n#operation: {inst}, imm={imm_val}, ' \
                                f'rd={rd}\n'
                    if 'auipc' in inst:
                        asm_code += f'TEST_AUIPC({inst}, {rd}, 0, {imm_val}, ' \
                                    f'{swreg}, {offset}, x0)\n'
                    elif 'lui' in inst:
                        asm_code += f'TEST_CASE(x0, {rd}, 0, {swreg}, ' \
                                    f'{offset}, lui {rd}, {imm_val})\n'

                    # adjust the offset. reset to 0 if it crosses 2048 and
                    # increment the current signature pointer with the
                    # current offset value
                    if offset + self.offset_inc >= 2048:
                        asm_code += f'addi {swreg}, {swreg},{offset}\n'
                        offset = 0

                    # increment offset by the amount of bytes updated in
                    # signature by each test-macro.
                    offset = offset + self.offset_inc

                    # keep track of the total number of signature bytes used
                    # so far.
                    sig_bytes = sig_bytes + self.offset_inc

                    inst_count += 1

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef'.format(int(sig_bytes / 4))

            # compile macros for the test
            compile_macros = []

            # return asm_code and sig_code

            test_dict.append({
                'asm_code': asm_code,
                'asm_data': '',
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': inst
            })
        yield test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
