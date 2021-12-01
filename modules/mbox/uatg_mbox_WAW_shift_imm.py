from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions, arithmetic_instructions
from uatg.utils import rvtest_data
from typing import Dict, Any
from random import randint
import random

class uatg_mbox_WAW_shift_imm(IPlugin):
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
        """x
            Generates the ASM instructions for multiplier dependencies and stores product in rd(upper 32 bits) and rd1(lower 32 bits) regs.
            It creates asm for the following instructions based upon ISA
               mul[w], mulh, mulhsu, mulhu. 
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for
        # every instruction in m_extension_instructions and arithmetic instructions

        test_dict = []
        
        reg_file = ['x' + str(reg_no) for reg_no in range(32)]  
        reg_file.remove('x0')

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-mul']
        if 'i' in self.isa:
            random_list += arithmetic_instructions[f'{self.isa_bit}-shift-imm']
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
            imm = range(10)
            code = ''
            rand_inst = random.choice(random_list)
            imm_val = random.choice(imm)
            #self.mul_stages_in = 4
            for i in range(self.mul_stages_in):
                 #code += f'mul_stages=={i}\n\n'
                 rs1 = 'x3'
                 rs2 = 'x4'
                 rd1 = 'x5'
                 rs3 = 'x6'
                 rs4 = 'x7'
                 
                 code += f'{inst} {rd1},{rs1},{rs2};\n'
                 for j in range(i):
                     rand_rs1 = random.choice(reg_file)
                     rand_rs2 = random.choice(reg_file)
                     rand_rd = random.choice(reg_file)
                     rand_inst1 = random.choice(random_list)
                     if rand_rd in [rs1, rs2, rs3, rs4, rd1, rand_rs1, rand_rs2]:
                             new_rand_rd = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rs2, rs3, rs4, rd1, rand_rs1, rand_rs2]
                                   ])
                             rand_rd = new_rand_rd
                     if rand_rs1 in [rd1, rs2, rs3, rs4, rand_rd, rand_rs2, rs1]:
                             new_rand_rs1 = random.choice([
                                   x for x in reg_file
                                   if x not in [rd1, rs2, rs3, rs4, rand_rd, rand_rs2, rs1]
                                   ])
                             rand_rs1 = new_rand_rs1
                     if rand_rs2 in [rs1, rs3, rs4, rd1, rand_rs1, rand_rd, rs2]:
                             new_rand_rs2 = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rs3, rs4, rd1, rand_rs1, rand_rd, rs2]
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
                     code += f'{rand_inst1} {rand_rd}, {rand_rs1}, {imm_val};\n'
                 code += f'{rand_inst} {rd1}, {rs4}, {imm_val};\n\n'
            rs1_val = '0x0000000000000012'
            rs2_val = '0x0000000000000021'
            rs3_val = '0x0000000000000045'
            rs4_val = '0x0000000074def5cb'
            #rs1_val = '2'
            #rs2_val = '4' 
                        # if signature register needs to be used for operations
                        # then first choose a new signature pointer and move the
                        # value to it.
            if swreg in [rd1, rs1, rs2, rs3, rs4]:
                 newswreg = random.choice([
                     x for x in reg_file
                     if x not in [rd1, rs1, rs2, rs3, rs4]
                     ])
                 asm_code += f'mv {newswreg}, {swreg}\n'
                 swreg = newswreg
                        
                        # perform the  required assembly operation
                       
            asm_code += f'\ninst_{inst_count}:\n'
                         #asm_code += f'\n#operation: {inst} rs1={rs1}, rs2={rs2}, rd={rd}\n'
                        
            asm_code += f'MBOX_DEPENDENCIES_WAW_RR_OP({rand_inst}, {inst}, {rs1}, {rs2}, {rs3}, {rs4}, {rd1}, 0, {rs1_val}, {rs2_val}, {rs3_val}, {rs4_val},  {swreg}, {offset}, {testreg}, {code})'

                     

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






