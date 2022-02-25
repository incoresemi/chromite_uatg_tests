from random import choice
from typing import Dict, Any, List, Union

from uatg.instruction_constants import mext_instructions, \
    compressed_instructions
from yapsy.IPlugin import IPlugin


class uatg_mbox_comp_WAR_reg_imm(IPlugin):
    """
     This class contains the write after read dependency and 
     validate the tests for mbox module with compressed instruction
     and multiplication instructions
    """

    def __init__(self) -> None:
        super().__init__()
        self.mul_stages_out = 0
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100
        self.mul_stages_in = 1

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
         Generates the ASM instructions for multiplier dependencies
         with compressed instructions.It creates asm for the following 
         instructions based upon ISA mul[w], mulh, mulhsu, mulhu 
         with compressed instructions(reg-imm). 
         (i.e mul x3, x5, x1
              addi x5, imm_val)
 
        """
        # compressed instructions for CI format has no limit to use
        # the registers it will support x0 to x31 registers.
        # Test to validate the mextension instructions with compressed
        # (reg-imm) instructions.

        doc_string = 'Test evaluates write after read dependency with ' \
                     'compressed(consumer) instruction and multiplication ' \
                     '(producer) instruction'

        reg_file = ['x' + str(reg_no) for reg_no in range(32)]
        reg_file.remove('x0')

        instruction_list = []
        random_list = []
        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-mul']
        if 'i' in self.isa:
            random_list += compressed_instructions[f'reg-imm']
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
            # rand_inst generates the compressed instructions randomly
            rand_inst = choice(random_list)
            # assign the imm with range
            imm = range(1, 10)
            # imm_value get the random value from imm
            imm_val = choice(imm)
            # depends on the mul_stages_in the mext and logic
            # instructions generated
            # initialize the source and destination register
            rs1 = 'x9'
            rs2 = 'x10'
            rd1 = 'x11'
            rs3 = 'x12'
            for i in range(self.mul_stages_in):
                code += f'{inst} {rd1},{rs1},{rs2};\n'
                for j in range(i):
                    rand_rs1 = choice(reg_file)
                    rand_rs2 = choice(reg_file)
                    rand_rd = choice(reg_file)
                    rand_inst1 = choice(random_list)

                    if rand_rd in [rs1, rs2, rd1, rand_rs1, rand_rs2, rs3]:
                        new_rand_rd = choice([
                            x for x in reg_file if x not in [rs1, rs2, rd1, 
                                                             rand_rs1,
                                                             rand_rs2, rs3]
                        ])
                        rand_rd = new_rand_rd
                    if rand_rs1 in [rd1, rs2, rs3, rand_rd, rand_rs2, rs1]:
                        new_rand_rs1 = choice([
                            x for x in reg_file
                            if x not in [rd1, rs2, rs3, rand_rd, rand_rs2, rs1]
                        ])
                        rand_rs1 = new_rand_rs1
                    if rand_rs2 in [rs1, rd1, rs3, rand_rs1, rand_rd, rs2]:
                        new_rand_rs2 = choice([
                            x for x in reg_file
                            if x not in [rs1, rd1, rs3, rand_rs1, rand_rd, rs2]
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
                code += f'{rand_inst} {rd1}, {imm_val};\n\n'
            # assign the rs1, rs2 and rs3 values
            rs1_val = '0xacde785'
            rs2_val = '0x21'
            rs3_val = '0x21'

            # if signature register needs to be used for operations
            # then first choose a new signature pointer and move the
            # value to it.
            if swreg in [rd1, rs1, rs2, rs3]:
                newswreg = choice(
                    [x for x in reg_file if x not in [rd1, rs1, rs2, rs3]])
                asm_code += f'mv {newswreg}, {swreg}\n'
                swreg = newswreg

            # perform the  required assembly operation
            asm_code += f'\ninst_{inst_count}:\n'
            asm_code += f'MBOX_COMPRESSED_RR_OP({rand_inst}, {inst}, {rs1}, ' \
                        f'{rs2}, {rs3}, {rd1}, 0, {rs1_val}, {rs2_val}, ' \
                        f'{rs3_val}, {swreg}, {offset}, {code})'

            # adjust the offset. reset to 0 if it crosses 2048 and
            # increment the current signature pointer with the
            # current offset value
            if offset + self.offset_inc >= 2048:
                asm_code += f'addi {swreg}, {swreg}, {offset}\n'

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
