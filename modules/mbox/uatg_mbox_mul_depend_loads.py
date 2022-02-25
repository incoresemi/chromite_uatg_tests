from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, mext_instructions, \
    load_store_instructions
from typing import Dict, Any, List, Union
from random import choice, getrandbits


class uatg_mbox_mul_depend_loads(IPlugin):
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

        reg_file = [register for register in base_reg_file if register != 'x0']

        instruction_list = []
        random_list = []

        if 'M' in self.isa or 'Zmmul' in self.isa:
            instruction_list += mext_instructions[f'{self.isa_bit}-mul']
        if 'i' in self.isa:
            random_list += load_store_instructions[f'{self.isa_bit}-loads']
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

            imm = range(1, 100)

            for rd in reg_file:
                for rs1 in reg_file:
                    for rs2 in reg_file:
                        rs2_val = hex(getrandbits(self.xlen))
                        rand_inst = choice(random_list)
                        imm_val = choice(imm)

                        # if signature register needs to be used for operations
                        # then first choose a new signature pointer and move the
                        # value to it.
                        if swreg in [rd, rs1, rs2, testreg]:
                            newswreg = choice([
                                x for x in reg_file
                                if x not in [rd, rs1, rs2, 'x0']
                            ])
                            asm_code += f'mv {newswreg}, {swreg}\n'
                            swreg = newswreg
                        if testreg in [rd, rs1, rs2, swreg]:
                            new_testreg = choice([
                                x for x in reg_file
                                if x not in [rd, rs1, rs2, swreg, 'x0']
                            ])
                            testreg = new_testreg
                        if rd in [swreg, testreg, rs1, rs2]:
                            new_rd = choice([
                                x for x in reg_file
                                if x not in [swreg, testreg, rs1, rs2, 'x0']
                            ])
                            rd = new_rd

                        if rs2 in [swreg, testreg, rs1, rd]:
                            new_rs2 = choice([
                                x for x in reg_file
                                if x not in [swreg, testreg, rs1, rd, 'x0']
                            ])
                            rs2 = new_rs2

                        if rs1 in [swreg, testreg, rs1, rd]:
                            new_rs1 = choice([
                                x for x in reg_file
                                if x not in [swreg, testreg, rs1, rd, 'x0']
                            ])
                            rs1 = new_rs1

                        # perform the  required assembly operation

                        asm_code += f'\ninst_{inst_count}:\n'

                        asm_code += f'MBOX_TEST_LD_OP({rand_inst},{inst}' \
                                    f',{rs1},{rs2},{rd},{testreg},0,' \
                                    f'{rs2_val},{imm_val},{swreg},0,{offset},0)'

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
                asm_data = '\nrvtest_data:\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'

                yield ({
                    'asm_code': asm_code,
                    'asm_data': asm_data,
                    'asm_sig': sig_code,
                    'compile_macros': compile_macros,
                    'name_postfix': inst
                })

    
