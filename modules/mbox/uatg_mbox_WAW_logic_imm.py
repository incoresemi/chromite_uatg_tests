from random import choice
from typing import Dict, Any, List, Union

from uatg.instruction_constants import base_reg_file, mext_instructions, \
    logic_instructions
from yapsy.IPlugin import IPlugin


class uatg_mbox_WAW_logic_imm(IPlugin):
    """  
     class evaluates mbox test write after write dependency
     with  multiplication instructions(mul,mulh, mulhsu, mulw) 
     and logic instructions (andi, ori, slti, sltui, xori).
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100
        self.mul_stages_in = 1
        self.mul_stages_out = 1

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
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
          ASM generates the write after write dependency with multiplication 
          instructions and logical instructions. destination register
          is same for logic instructions and mext instructions.
          (i.e mulh x6, x5, x4
               andi x6, x3, imm_val)
        """

        test_dict = []

        doc_string = 'Test evaluates the write after write dependency with ' \
                     'mextension(producer) instructions and logic(consumer) ' \
                     'instructions '

        reg_file = [
            register for register in base_reg_file
            if register not in ('x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7')
        ]

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-mul']
        if 'i' in self.isa:
            random_list += logic_instructions[f'logic-imm']
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
            # assign the imm with range
            imm = range(10)

            code = ''
            rand_inst = choice(random_list)
            # imm_value get the random value from imm
            imm_val = choice(imm)
            # initialize the source registers rs1, rs2, rs3 and rs4 
            # destination register rd1
            rs1, rs2, rs3, rs4, rd1 = 'x3', 'x4', 'x6', 'x7', 'x5'
            # depends on the mul_stages_in the mext and logic 
            # instructions generated
            for i in range(self.mul_stages_in):

                code += f'{inst} {rd1},{rs1},{rs2};\n'
                for j in range(i):
                    rand_rs1 = choice(reg_file)
                    rand_rs2 = choice(reg_file)
                    rand_rd = choice(reg_file)
                    rand_inst1 = choice(random_list)
                    if rand_rd in [rand_rs1, rand_rs2]:
                        new_rand_rd = choice([
                            x for x in reg_file
                            if x not in [rand_rs1, rand_rs2]
                        ])
                        rand_rd = new_rand_rd
                    if rand_rs1 in [rand_rd, rand_rs2]:
                        new_rand_rs1 = choice([
                            x for x in reg_file if x not in [rand_rd, rand_rs2]
                        ])
                        rand_rs1 = new_rand_rs1
                    if rand_inst in [rand_inst1, inst]:
                        new_rand_inst = choice([
                            x for x in random_list
                            if x not in [rand_inst1, rand_inst]
                        ])
                        rand_inst = new_rand_inst
                    if rand_inst1 in [rand_inst, inst]:
                        new_rand_inst1 = choice([
                            x for x in random_list
                            if x not in [rand_inst, rand_inst]
                        ])
                        rand_inst1 = new_rand_inst1
                    code += f'{rand_inst1} {rand_rd}, {rand_rs1}, {imm_val};\n'
                code += f'{rand_inst} {rd1}, {rs4}, {imm_val};\n\n'
            # assign the rs1_val, rs2_val, rs3_val and rs4_val
            rs1_val = '0x0000000000000012'
            rs2_val = '0x0000000000000021'
            rs3_val = '0x0000000000000045'
            rs4_val = '0x0000000000000011'

            # perform the  required assembly operation

            asm_code += f'\ninst_{inst_count}:\n'
            asm_code += f'MBOX_DEPENDENCIES_WAW_RR_OP({rand_inst}, {inst},' \
                        f'{rs1}, {rs2}, {rs3}, {rs4}, {rd1}, 0, {rs1_val},' \
                        f'{rs2_val}, {rs3_val}, {rs4_val},  {swreg}, {offset}' \
                        f', {testreg}, {code})'

            inst_count += 1

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
        yield test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
