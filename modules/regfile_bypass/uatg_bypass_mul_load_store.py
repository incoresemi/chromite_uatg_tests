# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from typing import Dict, List, Union, Any
import random


class uatg_bypass_mul_load_store(IPlugin):

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
        """
        Branch operation happens if bypass doesn't happen correctly
        Bypassing checked for muldiv ISA alu operation
        Bypassing checked for load/store instructions as well
        """
        test_dict = []
        reg_file = base_reg_file.copy()
        asm = f"\taddi {reg_file[2]} ,{reg_file[0]} ,5\n"
        asm += f"\taddi {reg_file[3]} ,{reg_file[0]} ,7\n"
        asm += f"\taddi {reg_file[4]} ,{reg_file[0]} ,1\n" 

        asm += f"\tmul {reg_file[4]} ,{reg_file[2]} ,{reg_file[3]}\n"
        # a multi-cycle instruction
        asm += f"\tsw {reg_file[4]} ,4({reg_file[0]})\n"   
        #store the product into memory

        asm += f"\tlw {reg_file[5]} ,4({reg_file[0]})\n"    
        # load the stored product from the memory
        asm += f"\taddi {reg_file[6]} ,{reg_file[0]} ,35\n" 
        # store the product(5*7) to verify in the next step

        asm += f"\tbeq {reg_file[5]} ,{reg_file[6]} ,flag\n"
        asm += "\tj end\n"
        asm += f"flag:\n\taddi {reg_file[7]} ,{reg_file[0]} ,10\n"
        asm += "end:\n\tfence.i\n"
        # if this branch is taken then it implies that 
        # bypassing hasn't happened properly
    

    
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
