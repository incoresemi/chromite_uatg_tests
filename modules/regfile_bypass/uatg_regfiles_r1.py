from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from typing import Dict, List, Union, Any
import random


class uatg_regfiles_r1(IPlugin):

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

        test_dict = []
        reg_file = base_reg_file.copy()
        asm= f"\taddi {reg_file[1]},{reg_file[0]} ,0\n"	#to store zero in another register used later for comparision
        asm+= f"\taddi {reg_file[4]},{reg_file[0]} ,2\n"	#initializing a temporary register (iterative variable)
        asm+= f"\taddi {reg_file[5]},{reg_file[0]} ,20\n"	#initializing a temporary register (to end for loop)
        
        
        asm += f"\tfor:\n\t beq x4,x5, end_for"
        asm += f"\n\tadd {reg_file[0]},{reg_file[0]},{reg_file[4]}"
        asm += f"\n\taddi {reg_file[4]},{reg_file[4]},2\n"
        asm += f"\t j for\n"
        asm += f"\tend_for:\n\t bne {reg_file[0]},{reg_file[1]},flag\n"
        #if the register zero takes a nonzero value then ,register7 takes the value of 10
        #thus giving us the indication of bug!!
        asm += f"\tflag:\n\t addi {reg_file[7]},{reg_file[1]},10\n"

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
