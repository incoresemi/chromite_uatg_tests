from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, load_store_instructions, \
    bit_walker
from uatg.utils import rvtest_data
from typing import Dict
from random import randint
import random


class uatg_decoder_memory_insts_1(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    Load operations
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100

    def execute(self, _decoder_dict) -> bool:
        self.isa = _decoder_dict['isa']
        if 'rv32' in self.isa:
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
            It creates asm for the following instructions (based upon input isa)
                lb[u], lh[u], lw[u], ld
        """
        rd_reg_file = base_reg_file.copy()
        rs_reg_file = base_reg_file.copy()

        ## remove 'x0' as base address
        rs_reg_file.remove('x0')

        test_dict = []


        for inst in load_store_instructions[f'{self.isa_bit}-loads']:

            asm_code = '\n\n' + '#' * 5 + ' load-inst rd, imm(rs1) ' + '#' * 5+'\n'

            align = [0,1,2,3,4,5,6,7] 
            # initial register to use as signature pointer
            swreg = 'x31'

            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'
           
            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            # Bit walking through 11 bits for immediate field
            imm = [val for i in range(1, 2) for val in
                   bit_walker(bit_width=12, n_ones=i, invert=False)]
            imm = imm + [val for i in range(1, 2) for val in
                   bit_walker(bit_width=12, n_ones=i, invert=True)]
            count = 0
            trap_sigbytes = 0
            trap_count = 0
            for rd in rd_reg_file:
                for rs1 in rs_reg_file:
                    for imm_val in imm:

                        rs1_val = hex(random.getrandbits(self.xlen))
                        adj = random.choices(align, weights= [50,5,10,5,20,5,10,5])[0]

                        if 'lh' in inst and adj in [1,3,5,7]:
                            trap_sigbytes = trap_sigbytes + (3*self.offset_inc)
                            trap_count = trap_count + 1
                        elif 'lw' in inst and adj in [1,2,3,5,6,7]:
                            trap_sigbytes = trap_sigbytes + (3*self.offset_inc)
                            trap_count = trap_count + 1
                        elif 'ld' in inst and adj in [1,2,3,4,5,6,7]:
                            trap_sigbytes = trap_sigbytes + (3*self.offset_inc)
                            trap_count = trap_count + 1

                        # if signature register needs to be used for operations
                        # then first choose a new signature pointer and move the
                        # value to it.
                        if swreg in [rd, rs1]:
                            newswreg = random.choice([x for x in rd_reg_file if x not in [rd, rs1, 'x0']])
                            asm_code += f'mv {newswreg}, {swreg}\n'
                            swreg = newswreg

                        # perform the  required assembly operation
                        asm_code += f'\ninst_{count}:'
                        asm_code += f'\n#operation: {inst}, rs1={rs1}, imm={imm_val}, rd={rd} align={adj}\n'
                        asm_code += f'TEST_LOAD({swreg}, x0, 0, {rs1}, {rd}, {imm_val}, {offset}, {inst}, {adj})\n'


                        # adjust the offset. reset to 0 if it crosses 2048 and
                        # increment the current signature pointer with the
                        # current offset value
                        if offset+self.offset_inc >= 2048:
                            asm_code += f'addi {swreg}, {swreg},{offset}\n'
                            offset = 0

                        # increment offset by the amount of bytes updated in
                        # signature by each test-macro.
                        offset = offset + self.offset_inc

                        # keep track of the total number of signature bytes used
                        # so far.
                        sig_bytes = sig_bytes + self.offset_inc
                        
                        count += 1

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes/4))
            sig_code += 'mtrap_count:\n'
            sig_code += ' .fill 1, 8, 0x0\n'
            sig_code += 'mtrap_sigptr:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(trap_sigbytes/4))

            # compile macros for the test
            compile_macros = ['rvtest_mtrap_routine']

            # return asm_code and sig_code

            asm_code = f'## inst_count: {count}, trap_count: {trap_count}' + \
                    asm_code

            asm_data = '\nrvtest_data:\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'
            
            test_dict.append({'asm_code': asm_code, 'asm_data': asm_data, 'asm_sig': sig_code, 'compile_macros':compile_macros})
        return test_dict
    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv

