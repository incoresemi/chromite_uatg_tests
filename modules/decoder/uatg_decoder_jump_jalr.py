from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, jump_instructions
from uatg.instruction_constants import bit_walker
from typing import List, Dict, Any, Union
import random


class uatg_decoder_jump_jalr(IPlugin):
    """
    This class contains the methods to generate and validate tests for
    jump instructions in RISCV-I extension
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV64I'
        self.isa_bit = 'rv64'
        self.offset_inc = 8
        self.xlen = 64
        self.num_rand_var = 100

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        if 'rv32' in self.isa:
            self.isa_bit = 'rv32'
            self.xlen = 32
            self.offset_inc = 4
        else:
            self.isa_bit = 'rv64'
            self.xlen = 64
            self.offset_inc = 8
        return True

    def generate_asm(self) -> List[Dict[str,
                                        Union[Union[str, List[str]], Any]]]:
        """
        This method generates Assembly Jump instructions of varied immediate 
        values. 
        The test will generate the tests jalr instruction
        """

        # assembly format
        # jalr -> jalr rd, imm(rs1)

        # for the jalr instruction, the rs1 as well as rd will be
        # iterated through the 32 possible registers in RISC-V

        reg_file = base_reg_file.copy()

        rs1_reg_file = base_reg_file.copy()

        # remove x0 from source reg list
        rs1_reg_file.remove('x0')

        test_dict = []

        inst = jump_instructions['jalr'][0]

        for rs1 in rs1_reg_file:

            asm_code = '\n\n' + '#' * 10 + f'{inst} test' + '#' * 10 + '\n'

            # intializing thge signature pointer
            swreg = 'x31'

            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initilializing temp_register
            temp_reg = 'x1'

            # initial offset
            offset = 0

            # variable to hold the total signature bytes to be used
            sig_bytes = 0

            imm = []

            ones = [val for val in range(1, 13)]
            for number in ones:
                imm += [val for val in bit_walker(12, number, False)]

            trap_sigbytes = 0

            count = 0

            for rd in reg_file:
                for imm_val in imm:

                    # if signature register needs to be used for operations
                    # then first choose a new signature pointer and move the
                    # value to it.
                    if swreg in [rd, rs1]:
                        newswreg = random.choice(
                            [x for x in reg_file if x not in [rd, rs1, 'x0']])
                        asm_code += f'mv {newswreg}, {swreg}\n'
                        swreg = newswreg

                    # if tempreg is used for operation, we switch temp_reg to
                    # some other register.
                    if temp_reg in [rd, rs1, swreg]:
                        new_temp_reg = random.choice([
                            x for x in reg_file
                            if x not in [rd, rs1, swreg, 'x0']
                        ])
                        temp_reg = new_temp_reg

                    # macro format
                    # TEST_JALR_OP(tempreg, rd, rs1, imm, swreg, offset,adj)

                    # perform required assembly operation
                    asm_code += f'\ninst_{count}:'
                    asm_code += f'\n#operation: {inst}\n#rs1: {rs1}, rd: {rd}' \
                                f', imm: {imm_val}, temp_reg: {temp_reg}' \
                                f', swreg: {swreg}\n'
                    asm_code += f'TEST_JALR_OP({temp_reg}, {rd}, {rs1}, ' \
                                f'{imm_val}, {swreg}, {offset}, 0)\n'

                    # adjust the offset. reset to 0 if it crosses 2048 and
                    # increment the current signature pointer with the
                    # current offset value
                    if offset + self.offset_inc >= 2048:
                        asm_code += f'addi {swreg}, {swreg},{offset}\n'
                        offset = 0

                    # Signbytes allocation for trap handler
                    trap_sigbytes = trap_sigbytes + (3 * self.offset_inc)

                    # increment offset by the amount of bytes updated in
                    # signature by each test-macro.
                    offset = offset + self.offset_inc

                    # keep track of the total number of signature bytes used
                    # so far.
                    sig_bytes = sig_bytes + self.offset_inc

                    count = count + 1

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes / 4))
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

            # return asm_code and sig_code
            test_dict.append({
                'asm_code': asm_code,
                'asm_data': asm_data,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': f'rs1_{rs1}'
            })

        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ''
        return sv
