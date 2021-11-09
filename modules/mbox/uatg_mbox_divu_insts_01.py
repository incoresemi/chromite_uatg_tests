from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions
from typing import Dict, List, Union, Any
import random


class uatg_mbox_divu_insts_01(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    mbox module
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
        if 'M' in self.isa or 'Zmmul' in self.isa:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """x
            Generates the ASM instructions for divider and stores both quotient
            and remainder in rd and rd1 reg respectively.
            It creates asm for the following instructions based upon ISA
            div[w], divu[w], rem[w], remu[w] 
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in m_extension_instructions

        test_dict = []

        reg_file = base_reg_file.copy()

        reg_file.remove('x0')

        instructions = []

        if 'M' in self.isa:
            instructions += mext_instructions[f'{self.isa_bit}-div']

        instruction_list = [x for x in instructions if 'u' in x]

        for inst in instruction_list:
            for rs1 in reg_file:
                asm_code = '#' * 5 + ' divu[w]/remu[w] reg, reg, reg ' \
                           + '#' * 5 + '\n'

                # initial register to use as signature pointer
                swreg = 'x31'

                # initialize swreg to point to signature_start label
                asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

                # initial offset to with respect to signature label
                offset = 0
                # variable to hold the total number of signature bytes to be
                # used.
                sig_bytes = 0
                inst_count = 0

                for rd in reg_file:
                    for rd1 in reg_file: 
                        for rs2 in reg_file:

                            rs1_val = hex(random.getrandbits(self.xlen))
                            rs2_val = hex(random.getrandbits(self.xlen))

                            # if signature register needs to be used for ops
                            # then first choose a new signature pointer and move
                            # the value to it.
                            if swreg in [rd, rd1, rs1, rs2]:
                                new_swreg = random.choice([
                                    x for x in reg_file
                                    if x not in [rd, rd1, rs1, rs2, 'x0']
                                ])
                                asm_code += f'mv {new_swreg}, {swreg}\n'
                                swreg = new_swreg

                            if rd1 in [rd, swreg, rs1, rs2]:
                                new_rd1 = random.choice([
                                    x for x in reg_file
                                    if x not in [rd, swreg, rs2, rs1]
                                ])
                                rd1 = new_rd1

                            if rd in [rs1, rd1, rs2, swreg]:
                                new_rd = random.choice([
                                    x for x in reg_file
                                    if x not in [rd1, swreg, rs2, rs1]
                                ])
                                rd = new_rd

                            # perform the required assembly operation
                            asm_code += f'\ninst_{inst_count}:'
                            asm_code += f'\n#operation: {inst}, rs1={rs1}' \
                                        f', rs2={rs2}, rd={rd}\n' \
                                        f'TEST_RR_OP({inst}, {rd}, {rs1}' \
                                        f', {rs2}, 0, {rs1_val}, ' \
                                        f'{rs2_val}, {swreg}, {offset}' \
                                        f', x0)\n'

                            if f'{inst}' == 'div':
                                asm_code += f'TEST_RR_OP(rem, {rd1}, ' \
                                            f'{rs1}, {rs2}, 0, {rs1_val}' \
                                            f', {rs2_val}, {swreg}, ' \
                                            f'{offset}, x0)\n'
                            elif f'{inst}' == 'divu':
                                asm_code += f'TEST_RR_OP(remu, {rd1}, ' \
                                            f'{rs1}, {rs2}, 0, {rs1_val}' \
                                            f', {rs2_val}, {swreg}, ' \
                                            f'{offset}, x0)\n'
                            elif f'{inst}' == 'divuw':
                                asm_code += f'TEST_RR_OP(remuw, {rd1}, ' \
                                            f'{rs1}, {rs2}, 0, {rs1_val}' \
                                            f', {rs2_val}, {swreg}, ' \
                                            f'{offset}, x0)\n'
                            elif f'{inst}' == 'divw':
                                asm_code += f'TEST_RR_OP(remw, {rd1}, ' \
                                            f'{rs1}, {rs2}, 0, {rs1_val}' \
                                            f', {rs2_val}, {swreg}, ' \
                                            f'{offset}, x0)\n'

                            # adjust the offset. reset to 0 if it crosses 2048
                            # and increment the current signature pointer with
                            # the current offset value
                            if offset + self.offset_inc >= 2048:
                                asm_code += f'addi {swreg}, {swreg}, {offset}\n'
                                offset = 0

                            # increment offset by the amount of bytes updated in
                            # signature by each test-macro.
                            offset = offset + self.offset_inc

                            # keep track of the total number of signature bytes
                            # used so far.
                            sig_bytes = sig_bytes + self.offset_inc

                            inst_count += 1

                # asm code to populate the signature region
                sig_code = 'signature_start:\n'
                sig_code += ' .fill {0}, 4, 0xdeadbeef\n'.format(
                    int(sig_bytes / 4))

                # compile macros for the test
                compile_macros = []

                # return asm_code and sig_code
                test_dict.append({
                    'asm_code': asm_code,
                    'asm_data': '',
                    'asm_sig': sig_code,
                    'compile_macros': compile_macros,
                    'name_postfix': f'{inst}_rs1_{rs1}'
                })
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
