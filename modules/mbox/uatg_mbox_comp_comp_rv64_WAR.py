from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import  compressed_instructions
from uatg.utils import rvtest_data
from typing import Dict, Any
from random import randint
import random

class uatg_mbox_comp_comp_rv64_WAR(IPlugin):
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
        self.mul_stages_in = 1

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.mul_stages_in  = core_yaml['m_extension']['mul_stages_in']
        self.mul_stages_out = core_yaml['m_extension']['mul_stages_out']
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
            Generates the ASM instructions for compressed instructions with compressed instructions.
            It creates asm for the following instructions based upon ISA c.and, c.or, c.xor, c.sub 
            with compressed instructions(rv64-regCA) 
        """
        # compressed instructions for CA format has limit to use the registers it will support only the x8 to x15.
        # Test to validate the mextension instructions with compressed (rv64-regCA) instructions.
        test_dict = []
        
        reg_file = ['x' + str(reg_no) for reg_no in range(32)]  
        reg_file.remove('x0')

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += compressed_instructions[f'reg-regCA']
        if 'i' in self.isa:
            random_list += compressed_instructions[f'{self.isa_bit}-regCA']
        for inst in instruction_list:
            asm_code = '#' * 5 + ' mul reg, reg, reg ' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x2'
            testreg = 'x1'
            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            inst_count = 0

            code = ''
            rand_inst = random.choice(random_list)
            for i in range(self.mul_stages_in):
            
                 rs1 = 'x9'
                 rs2 = 'x10'
                 rd1 = 'x11'
                 rd2 = 'x12'
                 
                 code += f'{inst} {rd1},{rs1};\n'
                 for j in range(i):
                     rand_rs1 = random.choice(reg_file)
                     rand_rs2 = random.choice(reg_file)
                     rand_rd = random.choice(reg_file)
                     rand_inst1 = random.choice(random_list)
                     
                     
                     if rand_rd in [rs1, rs2, rd1, rd2, rand_rs1, rand_rs2]:
                             new_rand_rd = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rs2, rd1, rd2, rand_rs1, rand_rs2]
                                   ])
                             rand_rd = new_rand_rd
                     if rand_rs1 in [rd1, rd2, rs2, rand_rd, rand_rs2, rs1]:
                             new_rand_rs1 = random.choice([
                                   x for x in reg_file
                                   if x not in [rd1, rd2, rs2, rand_rd, rand_rs2, rs1]
                                   ])
                             rand_rs1 = new_rand_rs1
                     if rand_rs2 in [rs1, rd1, rd2, rand_rs1, rand_rd, rs2]:
                             new_rand_rs2 = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rd1, rd2, rand_rs1, rand_rd, rs2]
                                   ])
                             rand_rs2 = new_rand_rs2
                     if rand_inst in [rand_inst1, inst]:
                             new_rand_inst = random.choice([
                                   x for x in random_list
                                   if x not in [rand_inst1, rand_inst]
                                   ])
                             rand_inst = new_rand_inst
                     if rand_inst1 in [rand_inst, inst]:
                             new_rand_inst1 = random.choice([
                                   x for x in random_list
                                   if x not in [rand_inst, rand_inst]
                                   ])
                             rand_inst1 = new_rand_inst1
                     code += f'{rand_inst1} {rand_rd}, {rand_rs1};\n'
                 code += f'{rand_inst} {rd2}, {rd1};\n\n'
            rs1_val = '0xacde785'
            rs2_val = '0x785'
             
            # if signature register needs to be used for operations
            # then first choose a new signature pointer and move the
            # value to it.
            if swreg in [rd1, rs1, rs2]:
                 newswreg = random.choice([
                     x for x in reg_file
                     if x not in [rd1, rs1, rs2]
                     ])
                 asm_code += f'mv {newswreg}, {swreg}\n'
                 swreg = newswreg
                        
            # perform the  required assembly operation           
            asm_code += f'\ninst_{inst_count}:\n'
            asm_code += f'MBOX_DEPENDENCIES_RR_OP({rand_inst}, {inst}, {rs1}, {rs2}, {rd1}, {rd2}, 0, {rs1_val}, {rs2_val}, {swreg}, {offset}, {code})'

                     

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

            inst_count += 1

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
                    'compile_macros': compile_macros,
                    'name_postfix': inst
                })
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv









