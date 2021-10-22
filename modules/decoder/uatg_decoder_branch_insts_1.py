from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, branch_instructions
from uatg.instruction_constants import bit_walker
from uatg.utils import rvtest_data
from typing import Dict
from random import randint
import random


class uatg_decoder_branch_insts_1(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    branch operations
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

    def generate_asm(self) -> Dict[str, str]:
        """
            Generates the ASM instructions for I type load instructions.
            It creates asm for the following instructions 
            beq, bne, bge, blt, bltu, bgeu
        """
        rs1_reg_file = base_reg_file.copy()
        rs2_reg_file = base_reg_file.copy()

        test_dict = []

        for inst in branch_instructions['branch']:

            jump_label = ['1b', '3f']

            for label in jump_label:

                for rs1 in rs1_reg_file:

                    asm_code = '\n\n' + '#' * 5 + f'{inst} rs1, rs2, label' + '#' * 5 + '\n'

                    # initial register to use as signature pointer
                    swreg = 'x31'

                    #initial temp register
                    temp_reg = 'x1'

                    # initialize swreg to point to signature_start label
                    asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

                    # initial offset to with respect to signature label
                    offset = 0

                    # variable to hold the total number of signature bytes to be used.
                    sig_bytes = 0

                    # Bit walking through 11 bits for immediate field
                    imm_address = [
                        val for i in range(1, 13) for val in bit_walker(
                            bit_width=12, n_ones=i, invert=False)
                    ]

                    count = 0
                    trap_sigbytes = 0

                    for rs2 in rs2_reg_file:
                        for imm_val in imm_address:

                            rs1_val = hex(random.getrandbits(self.xlen))
                            rs2_val = hex(random.getrandbits(self.xlen))

                            # if signature register needs to be used for operations
                            # then first choose a new signature pointer and move the
                            # value to it.
                            if swreg in [rs2, rs1]:
                                newswreg = random.choice([
                                    x for x in rs1_reg_file
                                    if x not in [rs2, rs1, 'x0']
                                ])
                                asm_code += f'mv {newswreg}, {swreg}\n'
                                swreg = newswreg

                            # if tempreg will be used for operation, we switch
                            # temp_reg to some other register.
                            if temp_reg in [rs1, rs2, swreg]:
                                newtemp_reg = random.choice([
                                    x for x in rs1_reg_file
                                    if x not in [rs2, rs1, swreg, 'x0']
                                ])
                                temp_reg = newtemp_reg

                            # perform the  required assembly operation
                            # TEST_BRANCH_OP(inst, tempreg, reg1, reg2, val1, val2, imm, label, swreg, offset,adj)
                            asm_code += f'\ninst_{count}:'
                            asm_code += f'\n#operation: {inst}, rs1: {rs1}, '\
                                        f'rs2: {rs2}, imm: {imm_val}\n'\
                                        f'# val1: {rs1_val}, val2:{rs2_val} '\
                                        f'label: {label}, swreg: {swreg}\n'
                            asm_code += f'TEST_BRANCH_OP({inst}, {temp_reg}, '\
                                        f'{rs1}, {rs2}, {rs1_val}, {rs2_val}, '\
                                        f'{imm_val}, {label}, {swreg}, {offset},0)\n'

                            # adjust the offset. reset to 0 if it crosses 2048 and
                            # increment the current signature pointer with the
                            # current offset value
                            if offset + self.offset_inc >= 2048:
                                asm_code += f'addi {swreg}, {swreg},{offset}\n'
                                offset = 0

                            # Signbytes allocation for trap handler
                            trap_sigbytes = trap_sigbytes +\
                                            (3 * self.offset_inc)

                            # increment offset by the amount of bytes updated in
                            # signature by each test-macro.
                            offset = offset + self.offset_inc

                            # keep track of the total number of signature bytes used
                            # so far.
                            sig_bytes = sig_bytes + self.offset_inc

                            count = count + 1

                    # asm code to populate the signature region
                    sig_code = 'signature_start:\n'
                    sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes / \
                                                                                4))
                    sig_code += 'mtrap_count:\n'
                    sig_code += ' .fill 1, 8, 0x0\n'
                    sig_code += 'mtrap_sigptr:\n'
                    sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                        int(trap_sigbytes / 4))

                    # compile macros for the test
                    compile_macros = ['rvtest_mtrap_routine']

                    asm_data = '\nrvtest_data:\n'
                    asm_data += '.word 0xbabecafe\n'
                    asm_data += '.word 0xbabecafe\n'
                    asm_data += '.word 0xbabecafe\n'
                    asm_data += '.word 0xbabecafe\n'

                    # for postfix
                    postfix_label = ''
                    if label == '3f':
                        postfix_label = 'forward'
                    elif label == '1b':
                        postfix_label = 'backward'

                    # return asm_code and sig_code

                    test_dict.append({
                        'asm_code': asm_code,
                        'asm_data': asm_data,
                        'asm_sig': sig_code,
                        'compile_macros': compile_macros,
                        'name_postfix': f'{inst}_rs1_{rs1}_{postfix_label}'
                    })

        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
