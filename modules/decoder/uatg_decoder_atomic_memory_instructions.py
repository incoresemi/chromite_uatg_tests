# Check LICENSE.incore for more licensing details

from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, atomic_mem_ops
from typing import Dict, List, Union, Any


class uatg_decoder_atomic_memory_instructions(IPlugin):
    """
    This class contains methods to generate and validate the tests for
    instructions in the m-extension
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        if 'RV32' in self.isa:
            self.isa_bit = 'rv32'
            self.xlen = 32
            self.offset_inc = 4
        else:
            self.isa_bit = 'rv64'
            self.xlen = 64
            self.offset_inc = 8
        if 'A' in self.isa in self.isa:
            return True
        else:
            return False
    
    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
          Generates the assembly file for Atomic memory instructions
        """

        test_dict = []

        reg_file = base_reg_file.copy()

        reg_file_nz = base_reg_file.copy()
        reg_file_nz.remove('x0')

        instruction_list = atomic_mem_ops[f'{self.isa_bit}-mem-ops']

        for inst in instruction_list:
            asm_code = '#' * 5 + ' amoX rd,rd,rd ' + '#' * 5 + '\n'

            inst_count = 0

            for rd in reg_file:
                for rs2 in reg_file:
                    for rs1 in reg_file_nz:

                        # perform the  required assembly operation
                        asm_code += f'\ninst_{inst_count}:'
                        asm_code += f'\n\tla {rs1}, rvtest_data'
                        asm_code += f'\n#operation: {inst}, rs1={rs1}, rs2=' \
                                    f'{rs2}, rd={rd}\n'
                        asm_code += f'\t{inst} {rd}, {rs2}, ({rs1})\n'

                        inst_count += 1

            compile_macros = []
            
            sig_code = ''

            asm_data = '\nrvtest_data:\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'
            asm_data += '.word 0xbabecafe\n'

            test_dict.append({'asm_code': asm_code,
                              'asm_data': asm_data,
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
