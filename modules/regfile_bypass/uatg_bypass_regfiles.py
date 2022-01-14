# See LICENSE.incore for details

# Co-authored-by: Sushanth Mullangi B <sushanthmullangi123@gmail.com>
# Co-authored-by: Nivedita Nadiger <nanivedita@gmail.com>

from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, arithmetic_instructions
from typing import Dict, List, Union, Any
import random


class uatg_bypass_regfiles(IPlugin):

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
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
        asm=f"\tandi {reg_file[3]},{reg_file[0]} ,0\n"	
        #clearing the bits in register x3
        asm +=f"\tandi {reg_file[4]},{reg_file[0]} ,0\n"	
        #clearing the bits in register x4
        asm+=f"\tandi {reg_file[31]} ,{reg_file[0]} ,0\n"	
        #clearing the bits in register x31
        
        # initial register to use as signature pointer
        swreg = 'x31'

        # initialize swreg to point to signature_start label
        asm_code = f"RVTEST_SIGBASE({swreg}, signature_start)\n"
        
        # initial offset to with respect to signature label
        offset = 0

        # variable to hold the total number of signature bytes to be used.
        sig_bytes = 0

        
        for val in range(-10,20,5):
            asm += f"\taddi {reg_file[3]} ,{reg_file[3]} ," + str(val)
            asm += f"\n\taddi {reg_file[4]} ,{reg_file[4]} ,7\n"
            asm += f"\tadd {reg_file[31]} ,{reg_file[3]} ,{reg_file[4]}\n"
            
            # adjust the offset. reset to 0 if it crosses 2048 and
            # increment the current signature pointer with the
            # current offset value
                        
            if offset + self.offset_inc >= 2048:
                   asm_code += f"\taddi {swreg}, {swreg}, {offset}\n"
                   offset = 0

            # increment offset by the amount of bytes updated in
            # signature by each test-macro.
            offset = offset + self.offset_inc

            # keep track of the total number of signature bytes used
            # so far.
            sig_bytes = sig_bytes + self.offset_inc


            # compile macros for the test
            compile_macros = []
            
        # asm code to populate the signature region
        sig_code = "signature_start:\n"
        sig_code += ".fill {0},4,0xdeadbeef\n".format(int(sig_bytes / 4))


        # return asm_code and sig_code
        test_dict.append({
           'asm_code': asm,
           'asm_data': '',
           'asm_sig': sig_code,
           'compile_macros': compile_macros,
           #'name_postfix': inst
            })
        return test_dict
    #after all the manual calculations, signature file should have value of 57
    
    def check_log(self, log_file_path, reports_dir) -> bool:
        return False

    def generate_covergroups(self, config_file) -> str:
        sv = ""
        return sv
