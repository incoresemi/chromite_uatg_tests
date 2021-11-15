from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file
from typing import Dict, List, Union
import random


class uatg_mbox_div_by_zero(IPlugin):
    """
    This class contains methods to generate and validate the the division by
    zero operation with x0 as divisor(rs2)
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

    def generate_asm(self) -> List[Dict[str, Union[str, list]]]:
        """
            It creates asm for divided by zero operation using div instruction 
        """
        test_dict = []

        reg_file = ['x0', 'x1']

        for rs2 in reg_file:

            asm_code = '#' * 5 + ' Divide by Zero tests' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x31'

            # registers that are used as rs1, rs2 , rd,rd1
            rs1 = 'x2'
            rs2 = rs2
            rd = 'x3'
            rd1 = 'x4'

            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0
            
            # data to populate rs1 and rs2 registers 
            if 'RV32' in self.isa:
                rs1_val = '0x6ffff63c'  # dividend
                rs2_val = '0x00000000'  # divisor
            # rd=>quotient= , rd1=>reminder=###
            elif 'RV64' in self.isa:
                rs1_val = '0xdb97531eca86420'  # dividend
                rs2_val = '0x0000000000000000'  # divisor
            # rd=>quotient= , rd1=>reminder=  ###
            
            # assigning correct val
            if 'RV32' in self.isa:
                correct_val_div = '0xffffffff'
                correct_val_rem = rs1_val
            if 'RV64' in self.isa:
                correct_val_div = '0xffffffffffffffff'
                correct_val_rem = rs1_val

            # perform the required assembly operation
            asm_code += f'\n#operation: div, rs1={rs1}, rs2={rs2}, rd={rd}\n'
            
            asm_code += f'TEST_RR_OP(div, {rd}, {rs1}, {rs2}, '\
                        f'{correct_val_div}, {rs1_val}, ' \
                        f'{rs2_val}, {swreg}, {offset}, x10)\n'
            
            # increment offset by the amount of bytes updated in
            # signature by each test-macro.
            offset = offset + self.offset_inc

            # keep track of the total number of signature bytes used
            # so far.
            sig_bytes = sig_bytes + self.offset_inc
            
            asm_code += f'\n#operation: rem, rs1={rs1}, rs2={rs2}, rd={rd}\n'
            
            asm_code += f'TEST_RR_OP(rem, {rd1}, {rs1}, {rs2}, '\
                        f'{correct_val_rem}, {rs1_val}, ' \
                        f'{rs2_val}, {swreg}, {offset}, x10)\n'

            offset = offset + self.offset_inc
            sig_bytes = sig_bytes + self.offset_inc

            asm_code += f'\n#operation: divu, rs1={rs1}, rs2={rs2}, rd={rd}\n'
            
            asm_code += f'TEST_RR_OP(divu, {rd}, {rs1}, {rs2}, '\
                        f'{correct_val_div}, {rs1_val}, ' \
                        f'{rs2_val}, {swreg}, {offset}, x10)\n'

            offset = offset + self.offset_inc
            sig_bytes = sig_bytes + self.offset_inc

            asm_code += f'\n#operation: remu, rs1={rs1}, rs2={rs2}, rd={rd}\n'
            
            asm_code += f'TEST_RR_OP(remu, {rd1}, {rs1}, {rs2}, '\
                        f'{correct_val_rem}, {rs1_val}, ' \
                        f'{rs2_val}, {swreg}, {offset}, x10)\n'
                
            offset = offset + self.offset_inc
            sig_bytes = sig_bytes + self.offset_inc
            
            if 'RV64' in self.isa:
                # updating correct value to be the lower 32bits since the following
                # instructions are word instructions
                new_correct_val_div = '0x' + correct_val_div[-8:]
                new_correct_val_rem = '0x' + correct_val_rem[-8:]

                asm_code += f'\n#operation: divuw, rs1={rs1}, rs2={rs2}, rd={rd}\n'
                
                asm_code += f'TEST_RR_OP(divuw, {rd}, {rs1}, {rs2}, '\
                            f'{new_correct_val_div}, {rs1_val}, ' \
                            f'{rs2_val}, {swreg}, {offset}, x10)\n'
                
                offset = offset + self.offset_inc
                sig_bytes = sig_bytes + self.offset_inc

                asm_code += f'\n#operation: remuw, rs1={rs1}, rs2={rs2}, rd={rd}\n'
                
                asm_code += f'TEST_RR_OP(remuw, {rd1}, {rs1}, {rs2}, '\
                            f'{new_correct_val_rem}, {rs1_val}, ' \
                            f'{rs2_val}, {swreg}, {offset}, x10)\n'
                
                offset = offset + self.offset_inc
                sig_bytes = sig_bytes + self.offset_inc

                asm_code += f'\n#operation: divw, rs1={rs1}, rs2={rs2}, rd={rd}\n'
                
                asm_code += f'TEST_RR_OP(divw, {rd}, {rs1}, {rs2}, '\
                            f'{new_correct_val_div}, {rs1_val}, ' \
                            f'{rs2_val}, {swreg}, {offset}, x10)\n'
                
                offset = offset + self.offset_inc
                sig_bytes = sig_bytes + self.offset_inc

                asm_code += f'\n#operation: remw, rs1={rs1}, rs2={rs2}, rd={rd}\n'
                
                asm_code += f'TEST_RR_OP(remw, {rd1}, {rs1}, {rs2}, '\
                            f'{new_correct_val_rem}, {rs1_val}, ' \
                            f'{rs2_val}, {swreg}, {offset}, x10)\n'
                
                offset = offset + self.offset_inc
                sig_bytes = sig_bytes + self.offset_inc

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes / 4))

            # compile macros for the test
            compile_macros = []
            name = ''
            # name postfix
            if rs2 == 'x0':
                name = 'reg-x0'
            else:
                name = f'reg-{rs2}'

            # return asm_code and sig_code
            test_dict.append({
                'asm_code': asm_code,
                'asm_data': '',
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': name
            })
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv