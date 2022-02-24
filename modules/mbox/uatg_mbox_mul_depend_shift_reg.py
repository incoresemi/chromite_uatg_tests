from random import choice, getrandbits
from typing import Dict, Any, List, Union

from uatg.instruction_constants import base_reg_file, mext_instructions, \
    arithmetic_instructions
from yapsy.IPlugin import IPlugin


class uatg_mbox_mul_depend_shift_reg(IPlugin):
    """  
     class evaluates mbox test  read after write dependency with
     multiplication instructions(mul, mulh, mulhsu, mulw) and arithmetic
     instructions(sll, srl, sra, sllw, srlw, sraw).

    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100
        self.mul_stages_in = 0
        self.mul_stages_out = 0

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
            Generates the ASM instructions for multiplier dependencies and
            stores product in rd(upper 32 bits) and rd1(lower 32 bits) regs.
            It creates asm for the following instructions based upon ISA
               mul[w], mulh, mulhsu, mulhu. 
        """
        # rd, rs1, rs2 iterate through all the 32 register combinations for all
        # instruction in m_extension_instructions and arithmetic instructions

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
            random_list += arithmetic_instructions[f'{self.isa_bit}-shift-reg']
        for inst in instruction_list:
            
            # initial register to use as signature pointer
            swreg = 'x2'
            testreg = 'x1'
            # initialize swreg to point to signature_start label
            

            # initial offset to with respect to signature label
            offset = 0

            # variable to hold the total number of signature bytes to be used.
            sig_bytes = 0

            inst_count = 0

            for rd in reg_file:
                asm_code = '#' * 5 + ' mul reg, reg, reg ' + '#' * 5 + '\n'
                asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n' 
                for rs1 in reg_file:
                    for rs2 in reg_file:
                        for rs3 in reg_file:
                            # for i in range(self.mul_stages_in):
                            rs1_val = hex(getrandbits(self.xlen))
                            rs2_val = hex(getrandbits(self.xlen))
                            rs3_val = hex(getrandbits(self.xlen))
                            rand_inst = choice(random_list)

                            # if signature register needs to be used for
                            # operations then first choose a new signature
                            # pointer and move the value to it.
                            if swreg in [rd, rs1, rs2, rs3, testreg]:
                                newswreg = choice([
                                    x for x in reg_file
                                    if x not in [rd, rs1, rs2, rs3, 'x0']
                                ])
                                asm_code += f'mv {newswreg}, {swreg}\n'
                                swreg = newswreg
                            if testreg in [rd, rs1, rs2, rs3, swreg]:
                                new_testreg = choice([
                                    x for x in reg_file if x not in
                                    [rd, rs1, rs2, rs3, swreg, 'x0']
                                ])
                                testreg = new_testreg
                            if rd in [swreg, testreg, rs1, rs2, rs3]:
                                new_rd = choice([
                                    x for x in reg_file if x not in
                                    [swreg, testreg, rs1, rs2, rs3, 'x0']
                                ])
                                rd = new_rd
                            if rs1 in [swreg, testreg, rd, rs2, rs3]:
                                new_rs1 = choice([
                                    x for x in reg_file if x not in
                                    [swreg, testreg, rd, rs2, rs3, 'x0']
                                ])
                                rs1 = new_rs1
                            if rs2 in [swreg, testreg, rs1, rd, rs3]:
                                new_rs2 = choice([
                                    x for x in reg_file if x not in
                                    [swreg, testreg, rs1, rd, rs3, 'x0']
                                ])
                                rs2 = new_rs2
                            if rs3 in [swreg, testreg, rs1, rs2, rd]:
                                new_rs3 = choice([
                                    x for x in reg_file if x not in
                                    [swreg, testreg, rs1, rs2, rd, 'x0']
                                ])
                                rs3 = new_rs3

                            # perform the  required assembly operation

                            asm_code += f'\ninst_{inst_count}:\n'

                            asm_code += f'MBOX_TEST_RR_OP({rand_inst}, ' \
                                        f'{inst}, {rs1}, {rs2}, {rs3}, {rd}' \
                                        f', 0, {rs1_val}, {rs2_val}, ' \
                                        f'{rs3_val}, {swreg}, {offset},' \
                                        f' {testreg})'

                            # adjust the offset. reset to 0 if it crosses 2048
                            # and increment the current signature pointer with
                            # the current offset value
                            if offset + self.offset_inc >= 2048:
                                asm_code += f'addi {swreg}, {swreg}, {offset}\n'
                                offset = 0

                            # increment offset by the amount of bytes updated in
                            # signature by each test-macro.
                            offset = offset + self.offset_inc

                            # keep track of the total number of signature bytes
                            # used so far.
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
        yield test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
