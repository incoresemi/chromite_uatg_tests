from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions
from typing import Dict, Any, List, Union
from random import choice


class uatg_mbox_mul_RAW_mul_mul(IPlugin):
    """    """

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
        """    """

        reg_file = [
            register for register in base_reg_file
            if register not in ('x0', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6')
        ]

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-mul']
        if 'i' in self.isa:
            random_list += mext_instructions[f'{self.isa_bit}-mul']
        for inst in instruction_list:
            asm_code = '#' * 5 + ' mul reg, reg, reg ' + '#' * 5 + '\n'

            # initial register to use as signature pointer
            swreg = 'x2'
            # initialize swreg to point to signature_start label
            asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            inst_count = 0

            code = ''
            rand_inst = choice(random_list)

            rs1, rs2, rd1, rd2 = 'x3', 'x4', 'x5', 'x6'

            for i in range(self.mul_stages_in):

                code += f'{inst} {rd1},{rs1},{rs2};\n'
                for j in range(i):
                    rand_rs1 = choice(reg_file)
                    rand_rs2 = choice(reg_file)
                    rand_rd = choice(reg_file)
                    rand_inst1 = choice(random_list)
                    if rand_rd in [rs1, rs2, rd1, rand_rs1, rand_rs2, rd2]:
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
                    if rand_rs2 in [rand_rs1, rand_rd]:
                        new_rand_rs2 = choice([
                            x for x in reg_file if x not in [rand_rs1, rand_rd]
                        ])
                        rand_rs2 = new_rand_rs2
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
                    code += f'{rand_inst1} {rand_rd}, {rand_rs1}, {rand_rs2};\n'
                code += f'{rand_inst} {rd2}, {rd1}, {rs2};\n\n'
            rs1_val = '0x00000005acd7fe48'
            rs2_val = '0x0000000000000001'

            # perform the  required assembly operation

            asm_code += f'\ninst_{inst_count}:\n'

            asm_code += f'MBOX_DEPENDENCIES_RR_OP({rand_inst}, {inst}, {rs1}, '\
                        f'{rs2}, {rd1}, {rd2}, 0, {rs1_val}, {rs2_val}, '\
                        f'{swreg}, {offset}, {code})'

            inst_count += 1

            # asm code to populate the signature region
            sig_code = 'signature_start:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(int(sig_bytes / 4))

            # compile macros for the test
            compile_macros = []

            # return asm_code and sig_code
            yield ({
                'asm_code': asm_code,
                'asm_data': '',
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': inst
            })

    
