from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions
from uatg.utils import rvtest_data
from typing import Dict, Any
from random import randint
import random


class uatg_mbox_div_by_x0(IPlugin):
    """
    This class contains methods to generate and validate the the division by zero operation with x0 as divisor(rs2)    """

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


    def generate_asm(self) -> Dict[str, str]:
        """
            It creates asm for divided by zero operation using div instruction 
        """
        test_dict = []

        reg_file = base_reg_file.copy()

        asm_code = '#' * 5 + ' div/rem reg, reg, reg ' + '#' * 5 + '\n'

        # initial register to use as signature pointer
        swreg = 'x31'

        # registers that are used as rs1, rs2 , rd,rd1
        rs1 = 'x1'
        rs2 = 'x0'
        rd  = 'x2'
        rd1 = 'x3'
        # initialize swreg to point to signature_start label
        asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

        # initial offset to with respect to signature label
        offset = 0

        # variable to hold the total number of signature bytes to be used.
        sig_bytes = 0
   
        # data to populate rs1 and rs2 registers 
        if 'RV32' in self.isa:
           rs1_val = '0x6ffff63c' #dividend
           rs2_val = '0x00000000' #divisor
        ###rd=>quotient= , rd1=>reminder=###
        if 'RV64' in self.isa:
           rs1_val = '0xdb97531eca86420' #dividend
           rs2_val = '0x0000000000000000' #divisor
        ## rd=>quotient= , rd1=>reminder=  ###
         
        # if signature register needs to be used for operations
        # then first choose a new signature pointer and move the value to it.
    
        if swreg in [rd, rs1, rs2]:
            newswreg = random.choice([
               x for x in reg_file
                if x not in [rd, rs1, rs2, rd1, 'x0']
            ])
            asm_code += f'mv {newswreg}, {swreg}\n'
            swreg = newswreg

        # perform the  required assembly operation
        asm_code += f'\n#operation: div, rs1={rs1}, rs2={rs2}, rd={rd}\n'
        asm_code += f'TEST_RR_OP(div, {rd}, {rs1}, {rs2}, 0, {rs1_val}, {rs2_val}, {swreg}, {offset}, x10)\n'
        asm_code += f'TEST_RR_OP(rem, {rd1}, {rs1}, {rs2}, 0, {rs1_val}, {rs2_val}, {swreg}, {offset}, x10)\n'

        # adjust the offset. reset to 0 if it crosses 2048 and
        # increment the current signature pointer with the
        # current offset value
        if offset + self.offset_inc >= 2048:
            asm_code += f'addi {swreg}, {swreg}, {offset}\n'
            offset = 0

        # increment offset by the amount of bytes updated in
        # signature by each test-macro.
        offset = offset + self.offset_inc

        # keep track of the total number of signature bytes used
        # so far.
        sig_bytes = sig_bytes + self.offset_inc

        # asm code to populate the signature region
        sig_code = 'signature_start:\n'
        sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes / 4))

        # compile macros for the test
        compile_macros = []

        # return asm_code and sig_code
        test_dict.append({
                'asm_code': asm_code,
                'asm_data': '',
                'asm_sig': sig_code,
                'compile_macros': compile_macros
             })
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv


