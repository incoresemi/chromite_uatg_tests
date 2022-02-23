# Check LICENSE.incore for more licensing details

from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, atomic_lr_sc
from uatg.utils import rvtest_data
from typing import Dict, List
from random import randint
import random


class uatg_decoder_atomic_lr_sc_instructions(IPlugin):
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
    
    def generate_asm(self) -> List[Dict[str, str]]:
        """
          Generates the assembly file for Atomic LR-SC instructions
        """

        test_dict = []

        reg_file = base_reg_file.copy()

        reg_file_nz = base_reg_file.copy()
        reg_file_nz.remove('x0')

        instruction_list = atomic_lr_sc[f'{self.isa_bit}-lr-sc']

        for inst in instruction_list: 
            for rd in reg_file:
                asm_code = '#'* 5 + f' {inst[0]} rd,rs1 ' + '#' * 5 + '\n'
                asm_code += '#'* 5 + f' {inst[1]} rd,rs2,rs1 ' + '#' * 5 + '\n'
 
                inst_count = 0
                for rs2 in reg_file:
                    for rs1 in reg_file_nz:

                        rs2_val = hex(random.getrandbits(self.xlen))
                        
                        if rs2 in [rd, rs1]:
                            new_rs2 = random.choice([
                                x for x in reg_file_nz
                                if x not in [rd, rs1]
                            ])
                            rs2 = new_rs2
                        
                        if rd in [rs2, rs1]:
                            new_rd = random.choice([
                                x for x in reg_file_nz
                                if x not in [rs2, rs1]
                            ])
                            rd = new_rd

                        # perform the  required assembly operation
                        asm_code += f'\ninst_{inst_count}:'
                        asm_code += f'\n\tla {rs1}, rvtest_data'
                        asm_code += f'\n\t#operation: {inst[0]}, rs1={rs1}, rd={rs2}\n'
                        asm_code += f'\t{inst[0]} {rs2}, ({rs1})\n' #here rs2 indicates rd
                        asm_code += f'\t#operation: {inst[1]}, rd={rd}, rs2={rs2}, rs1={rs1}\n'
                        asm_code += f'\t{inst[1]} {rd}, {rs2}, ({rs1})\n'

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
                    'name_postfix': inst[0]+'_'+inst[1]
                })

        yield test_dict

    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
