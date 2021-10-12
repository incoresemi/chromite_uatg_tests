from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, logic_instructions, \
    bit_walker
from uatg.utils import rvtest_data
import random
from typing import Dict


class uatg_decoder_logical_insts_2(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    logical register register instructions.
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
            Generates the ASM instructions for logical immediate instructions.
            It creates asm for the following instructions based upon ISA
            andi, ori, slti, sltiu, xori
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in logical_instructions['logic-imm']
        reg_file = base_reg_file.copy()
        test_dict = []

        for inst in logic_instructions['logic-imm']:
    
            asm_code = '\n\n' + '#' * 5 + ' shift_inst reg, reg, reg ' + '#' * 5+'\n'
            
            # initial register to use as signature pointer
            swreg = 'x31'
    
            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'
           
            # initial offset to with respect to signature label
            offset = 0
    
            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0
            # Bit walking through 11 bits for immediate field
            imm = [val for i in range(1, 8) for val in
                   bit_walker(bit_width=11, n_ones=i, invert=False)]
            for rd in reg_file:
                for rs1 in reg_file:
                    for imm_val in imm:


                        rs1_val = hex(random.getrandbits(self.xlen))
                        # if signature register needs to be used for operations
                        # then first choose a new signature pointer and move the
                        # value to it.
                        if swreg in [rd, rs1]:
                            newswreg = random.choice([x for x in reg_file if x not in [rd, rs1, 'x0']])
                            asm_code += f'mv {newswreg}, {swreg}\n'
                            swreg = newswreg

                        # perform the  required assembly operation
                        asm_code += f'\n#operation: {inst}, rs1={rs1}, imm={imm_val}, rd={rd}\n'
                        asm_code += f'TEST_IMM_OP({inst}, {rd}, {rs1}, 0, {rs1_val}, {imm_val}, {swreg}, {offset}, x0)\n'

                        # adjust the offset. reset to 0 if it crosses 2048 and
                        # increment the current signature pointer with the
                        # current offset value
                        if offset+self.offset_inc >= 2048:
                            asm_code += f'addi {swreg}, {offset}\n'
                            offset = 0

                        # increment offset by the amount of bytes updated in
                        # signature by each test-macro.
                        offset = offset + self.offset_inc

                        # keep track of the total number of signature bytes used
                        # so far.
                        sig_bytes = sig_bytes + self.offset_inc

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef'.format(int(sig_bytes/4))

            # return asm_code and sig_code
            test_dict.append({'asm_code': asm_code, 'asm_data': '', 'asm_sig': sig_code})
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
