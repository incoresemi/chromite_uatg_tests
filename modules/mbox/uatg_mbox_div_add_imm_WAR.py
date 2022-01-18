from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions, \
    arithmetic_instructions
from typing import Dict, List, Union, Any
import random


class uatg_mbox_div_add_imm_WAR(IPlugin):
    """  
     class evaluate the mbox test with write after read dependency with mext
     instructions(div, divu, rem, remu,divuw, remuw, divw,remw) and arithmetic 
     instructions(addi, addw).

    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100
        self.div_stages = 1
        self.mul_stages_in = 1
        self.mul_stages_out = 1

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        # self.div_stages = 4
        self.div_stages = core_yaml['m_extension']['div_stages']
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

    def generate_asm(
            self) -> List[Dict[str, Union[Union[str, List[Any]], Any]]]:
        """
           ASM generates the write after read dependency source 
           register of mext instructions (div, divu, rem, remu, divuw,
           remuw, divw, remw) depends on the destination register of 
           arithmetic instructions(addi, addiw).
           (i.e div x4, x2, x1
                addi x2, x5, imm_val) 
        """

        test_dict = []
        
        doc_string = 'Test evaluates the write after read dependency
                      with mextension instructions(producer) 
                      and arithmetic (consumer) instructions'

        reg_file = [
            register for register in base_reg_file
            if register not in ('x0', 'x3', 'x4', 'x5', 'x6')
        ]

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-div']
        if 'i' in self.isa:
            random_list += arithmetic_instructions[f'{self.isa_bit}-add-imm']
        for inst in instruction_list:
            asm_code = '#' * 5 + ' div reg, reg, reg ' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x2'
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            inst_count = 0

            code = ''
            #assign the imm with range
            imm = range(1, 100)
            # imm_value get the random value from imm
            imm_val = random.choice(imm)
            # rand_inst generates the arithmetic instructions randomly
            rand_inst = random.choice(random_list)
            # initialize the source registers rs1, rs2 
            #destination register rd1
            rs1, rs2, rd1 = 'x3', 'x4', 'x5'
            rand_rs1, rand_rd = 'x0', 'x0'
            #depends on the div_stages the mext and arithmetic 
            #instructions are generated
            for i in range(self.div_stages):

                code += f'{inst} {rd1},{rs1},{rs2};\n'
                for j in range(i):
                    rand_rs1 = random.choice(reg_file)
                    rand_rd = random.choice(reg_file)
                    rand_inst1 = random.choice(random_list)
                    if rand_rd in [rs1, rs2, rd1, rand_rs1, swreg]:
                        new_rand_rd = random.choice([
                            x for x in reg_file
                            if x not in [rs1, rs2, rd1, rand_rs1, swreg]
                        ])
                        rand_rd = new_rand_rd
                    if rand_rs1 in [rd1, rs2, rand_rd, rs1, swreg]:
                        new_rand_rs1 = random.choice([
                            x for x in reg_file
                            if x not in [rd1, rs2, rand_rd, rs1, swreg]
                        ])
                        rand_rs1 = new_rand_rs1

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
                code += f'{rand_inst} {rs1}, {rs2}, {imm_val};\n\n'
            #assign the rs1 and rs2 value
            rs1_val = '0x48'
            rs2_val = '0x6'
            # if signature register needs to be used for operations
            # then first choose a new signature pointer and move the
            # value to it.

            if swreg in [rd1, rs1, rs2, rand_rs1, rand_rd]:
                newswreg = random.choice([
                    x for x in reg_file
                    if x not in [rd1, rs1, rs2, rand_rs1, rand_rd]
                ])
                asm_code += f'mv {newswreg}, {swreg}\n'
                swreg = newswreg

                # perform the  required assembly operation

            asm_code += f'\ninst_{inst_count}:\n'
            asm_code += f'MBOX_DEPENDENCIES_WAR_RI_OP({rand_inst}, {inst}, ' \
                        f'{rs1}, {rs2}, {rd1}, 0, {rs1_val}, {rs2_val}, ' \
                        f'{swreg}, {offset}, {code})'

            # adjust the offset. reset to 0 if it crosses 2048 and
            # increment the current signature pointer with the
            # current offset value
            if offset + self.offset_inc >= 2048:
                asm_code += f'addi {swreg}, {swreg}, {offset}\n'
                # increment offset by the amount of bytes updated in
                # signature by each test-macro.

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
                'name_postfix': inst,
                'doc_string': doc_string
            })
        return test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
