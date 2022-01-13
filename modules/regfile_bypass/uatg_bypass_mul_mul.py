from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from typing import Dict, List, Union, Any
import random


class uatg_bypass_mul_mul(IPlugin):

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
    
        self.xlen = 32

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
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        #bypass of mul and mul operation
        test_dict = []
        reg_file = base_reg_file.copy()
        asm = f"\taddi {reg_file[1]} ,{reg_file[0]} ,3\n"
        asm += f"\taddi {reg_file[2]} ,{reg_file[0]} ,4\n"
        asm += f"\tmul {reg_file[3]} ,{reg_file[1]} ,{reg_file[2]}\n" #1st mul instruction
        #                                                       reg3 should have 12

        asm += f"\tmul {reg_file[4]} ,{reg_file[1]} ,{reg_file[3]}\n" #2nd mul instruction involving a reg which is involved 
        #                                                       in previous instruction
        #                                                       reg4 should have 36 IF THE VALUE OF REG3 IS BYPASSED
       

        asm += f"\taddi {reg_file[5]} ,{reg_file[0]} ,36\n"         #storing the final op to compare with value in reg4

        asm += f"\tbne {reg_file[5]} ,{reg_file[4]} ,flag\n"
        asm += f"\tflag:\n\t addi {reg_file[7]} ,{reg_file[0]} ,10\n" # if this branch is taken then it implies that 
        #                                                           bypassing HASN'T happened properly
    

    
        # compile macros for the test
        compile_macros = []

        # return asm_code and sig_code
        test_dict.append({
            'asm_code': asm,
            #'asm_data': '',
            'asm_sig': '',
            'compile_macros': compile_macros,
            #'name_postfix': inst
        })
        return test_dict
        
    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
