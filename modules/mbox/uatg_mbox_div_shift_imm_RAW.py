from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions, arithmetic_instructions
from uatg.utils import rvtest_data
from typing import Dict, Any
from random import randint
import random

class uatg_mbox_div_shift_imm_RAW(IPlugin):
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
        self.div_stages = 1

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        #self.div_stages = 4
        self.div_stages  = core_yaml['m_extension']['div_stages']
        self.mul_stages_in = core_yaml['m_extension']['mul_stages_in']
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
        reg_file.remove('x3')
        reg_file.remove('x4')
        reg_file.remove('x5')
        reg_file.remove('x6')
        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-div']
        if 'i' in self.isa:
            random_list += arithmetic_instructions[f'{self.isa_bit}-shift-imm']
        for inst in instruction_list:
            asm_code = '#' * 5 + ' mul reg, reg, reg ' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x2'
            #testreg = 'x1'
            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            inst_count = 0

            code = ''
            imm = range(1,10)
            imm_val = random.choice(imm)
            rand_inst = random.choice(random_list)
            #self.mul_stages_in = 4
            for i in range(self.div_stages):
                 #code += f'self.div_stages=={i}\n\n'
                 rs1 = 'x3'
                 rs2 = 'x4'
                 rd1 = 'x5'
                 rd2 = 'x6'
                 '''if rd1 in [rs1, rs2, rd2]:
                      new_rd1 = random.choice([
                          x for x in reg_file
                          if x not in [rs1, rs2, rd2]
                          ])
                      rd1 = new_rd1
                 if rd2 in [rs1, rs2, rd1]:
                      new_rd2 = random.choice([
                          x for x in reg_file
                          if x not in [rs1, rs2, rd1]
                          ])
                      rd2 = new_rd2
                 if rs1 in [rd1, rs2, rd2]:
                      new_rs1 = random.choice([
                          x for x in reg_file
                          if x not in [rd1, rs2, rd2]
                          ])
                      rs1 = new_rs1
                 if rs2 in [rs1, rd1, rd2]:
                      new_rs2 = random.choice([
                          x for x in reg_file
                          if x not in [rs1, rd1, rd2]
                          ])
                      rs2 = new_rs2'''
                 code += f'{inst} {rd1},{rs1},{rs2};\n'
                 for j in range(i):
                     rand_rs1 = random.choice(reg_file)
                     #rand_rs2 = random.choice(reg_file)
                     rand_rd = random.choice(reg_file)
                     rand_inst1 = random.choice(random_list)
                     if rand_rd in [rs1, rs2, rd1, rand_rs1, rd2, swreg]:
                             new_rand_rd = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rs2, rd1, rand_rs1, rd2, swreg]
                                   ])
                             rand_rd = new_rand_rd
                     if rand_rs1 in [rd1, rs2, rd2, rand_rd, rs1, swreg]:
                             new_rand_rs1 = random.choice([
                                   x for x in reg_file
                                   if x not in [rd1, rs2, rd2, rand_rd, rs1, swreg]
                                   ])
                             rand_rs1 = new_rand_rs1
                     '''if rand_rs2 in [rs1, rd1, rd2, rand_rs1, rand_rd, rs2, swreg]:
                             new_rand_rs2 = random.choice([
                                   x for x in reg_file
                                   if x not in [rs1, rd1, rd2, rand_rs1, rand_rd, rs2, swreg]
                                   ])
                             rand_rs2 = new_rand_rs2'''
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
                 code += f'{rand_inst} {rd2}, {rd1}, {imm_val};\n\n'
            rs1_val = '0x48'
            rs2_val = '0x6'
            #rs1_val = '2'
            #rs2_val = '4' 
                        # if signature register needs to be used for operations
                        # then first choose a new signature pointer and move the
                        # value to it.
            if swreg in [rd1, rs1, rs2, rd2, rand_rs1, rand_rd ]:
                 newswreg = random.choice([
                     x for x in reg_file
                     if x not in [rd1, rs1, rs2, rd2, rand_rs1, rand_rd]
                     ])
                 asm_code += f'mv {newswreg}, {swreg}\n'
                 swreg = newswreg
                        
                        # perform the  required assembly operation
                       
            asm_code += f'\ninst_{inst_count}:\n'
                         #asm_code += f'\n#operation: {inst} rs1={rs1}, rs2={rs2}, rd={rd}\n'
                        
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





