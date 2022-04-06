import random
from typing import Dict, List, Any, Union

from uatg.instruction_constants import arithmetic_instructions, \
    mext_instructions, base_reg_file
from yapsy.IPlugin import IPlugin


class uatg_mbox_mul_depend_shift_imm(IPlugin):
    """ 
     class evaluates mbox test  read after write dependency with
     multiplication instructions(mul, mulh, mulhsu, mulw) and arithmetic
     instructions(slli, srli, srai, slliw, srliw, sraiw).
 
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

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
          ASM generates the read after write dependency with multiplication 
          instructions and arithmetic instructions.  destination register of
         mext instructions depends on the source register of arithmetic 
         instructions.
          (i.e mulh x4, x3, x1
               slli x1, x4, x6)
        """
        test_dict = []

        doc_string = 'Test evaluates the read after write dependency with ' \
                     'mextension(producer) instructions and arithmetic(' \
                     'consumer) instructions '

        reg_file = [register for register in base_reg_file if register != 'x0']

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
            # assign the imm with range
            imm = range(1, 4)

            for _ in range(10):
                [rs1, rs2, rd] = random.choices(reg_file, k=3)
                rs1_val = hex(random.getrandbits(self.xlen))
                rs2_val = hex(random.getrandbits(self.xlen))
                rand_inst = random.choice(random_list)
                imm_val = random.choice(imm)

                # if signature register needs to be used for operations
                # then first choose a new signature pointer and move the
                # value to it.
                if swreg in [rd, rs1, rs2, testreg]:
                    newswreg = random.choice([
                        x for x in reg_file
                        if x not in [rd, rs1, rs2, 'x0']
                    ])
                    asm_code += f'mv {newswreg}, {swreg}\n'
                    swreg = newswreg
                if testreg in [rd, rs1, rs2, swreg]:
                    new_testreg = random.choice([
                        x for x in reg_file
                        if x not in [rd, rs1, rs2, swreg, 'x0']
                    ])
                    testreg = new_testreg
                if rd in [swreg, testreg, rs1, rs2]:
                    new_rd = random.choice([
                        x for x in reg_file
                        if x not in [swreg, testreg, rs1, rs2, 'x0']
                    ])
                    rd = new_rd
                if rs1 in [swreg, testreg, rd, rs2]:
                    new_rs1 = random.choice([
                        x for x in reg_file
                        if x not in [swreg, testreg, rd, rs2, 'x0']
                    ])
                    rs1 = new_rs1
                if rs2 in [swreg, testreg, rs1, rd]:
                    new_rs2 = random.choice([
                        x for x in reg_file
                        if x not in [swreg, testreg, rs1, rd, 'x0']
                    ])
                    rs2 = new_rs2

                # perform the  required assembly operation

                asm_code += f'\ninst_{inst_count}:\n'
                asm_code += f'MBOX_TEST_RI_OP({rand_inst}, {inst}, ' \
                            f'{rs1}, {rs2}, {rd}, 0,  {rs1_val}, ' \
                            f'{rs2_val}, {imm_val}, {swreg}, ' \
                            f'{offset}, {testreg})'

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
                sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                    int(sig_bytes / 4))

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
