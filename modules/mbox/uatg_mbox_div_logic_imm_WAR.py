from random import choice
from typing import Dict, List, Union, Any

from uatg.instruction_constants import base_reg_file, mext_instructions, \
    logic_instructions
from yapsy.IPlugin import IPlugin


class uatg_mbox_div_logic_imm_WAR(IPlugin):
    """ 
     class evaluate the mbox test with write after read dependency with mext
     instructions(div, divu, rem, remu,divuw, remuw, divw,remw) 
     and logic instructions(andi, ori, slli, slti, sltui, xori).

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
           logic instructions(andi, ori, slli, sltui, xori).
           (i.e div x4, x2, x1
                andi x2, x5, imm_val) 
        """

        doc_string = 'Test evaluates the write after read dependency with ' \
                     'mextension instructions(producer) and logical (' \
                     'consumer) instructions '

        reg_file = [
            register for register in base_reg_file
            if register not in ('x0', 'x3', 'x4', 'x5', 'x6')
        ]

        instruction_list = []
        random_list = []

        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-div']
        if 'i' in self.isa:
            random_list += logic_instructions[f'logic-imm']
        for inst in instruction_list:
            asm_code = '#' * 5 + ' div reg, reg, reg ' + '#' * 5 + '\n'

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
            # assign the imm with range
            imm = range(1, 10)
            # imm_value get the random value from imm
            imm_val = choice(imm)
            # rand_inst generates the arithmetic instructions randomly
            rand_inst = choice(random_list)
            # initialize the source registers rs1, rs2
            # destination register rd1
            rs1, rs2, rd1 = 'x3', 'x4', 'x5'
            rand_rs1, rand_rd = 'x0', 'x0'
            # depends on the div_stages the mext and arithmetic
            # instructions are generated
            for i in range(self.div_stages):
                rs1 = 'x3'
                rs2 = 'x4'
                rd1 = 'x5'

                code += f'{inst} {rd1},{rs1},{rs2};\n'
                for j in range(i):
                    rand_rs1 = choice(reg_file)
                    rand_rd = choice(reg_file)
                    rand_inst1 = choice(random_list)
                    if rand_rd in [rs1, rs2, rd1, rand_rs1, swreg]:
                        new_rand_rd = choice([
                            x for x in reg_file
                            if x not in [rs1, rs2, rd1, rand_rs1, swreg]
                        ])
                        rand_rd = new_rand_rd
                    if rand_rs1 in [rd1, rs2, rand_rd, rs1, swreg]:
                        new_rand_rs1 = choice([
                            x for x in reg_file
                            if x not in [rd1, rs2, rand_rd, rs1, swreg]
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
                code += f'{rand_inst} {rs1}, {rs2}, {imm_val};\n\n'
            # assign the rs1 and rs2 value
            rs1_val = '0x48'
            rs2_val = '0x6'

            # if signature register needs to be used for operations
            # then first choose a new signature pointer and move the
            # value to it.
            if swreg in [rd1, rs1, rs2, rand_rs1, rand_rd]:
                newswreg = choice([
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
            yield ({
                'asm_code': asm_code,
                'asm_data': '',
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': inst,
                'doc_string': doc_string
            })

    
