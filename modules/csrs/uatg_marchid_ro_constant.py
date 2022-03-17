from random import randint
from yapsy.IPlugin import IPlugin
from typing import Dict, List, Union, Any
import random
class uatg_marchid_ro_constant(IPlugin):
      """
      """
      
      def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.csr, self.reset_val = None, None

      def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        if 'marchid' in isa_yaml['hart0'].keys():
            self.reset_val = isa_yaml['hart0']['marchid']['reset-val']
            if self.xlen == 32 and isa_yaml['hart0']['marchid']['rv32'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['marchid']['rv32']
       
            elif self.xlen == 64 and isa_yaml['hart0']['marchid']['rv64'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['marchid']['rv64']
                return True 
            else:
                return False
            return True
        else:
            return False

   
      def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
          imm = range(1,10)
          random_value = random.choice(imm)
          # write a random value in mvendorid to check the value is 
          # not updated
          asm_code = f'\n\n #write a random value in marchid ' \
                     f' to check the value is not updated ' \
                     f' \n csrr x1, marchid\n' \
                     f' \n la x4, mtrap_sigptr ' \
                     f' \n li x2 , {random_value} ' \
                     f' \n csrw marchid, x2'\
                     f' \n csrr x3, marchid\n' \
                     f' \n bne x1,x3,failcase'\
                     f' \n sw x0, 0(x4)' \
                     f' \n csrw marchid, x1 '
          asm_code += f' \n j exit'
          asm_code += f' \n failcase: \n li x6, 1 \n sw x6,0(x4)'
          asm_code += f' \n exit: \n nop'
                   
     
          sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                     f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
  
          #compile macros for the test
          compile_macros=['rvtest_mtrap_routine']
              

          test_dict = [{'asm_code': asm_code,
                       'asm_sig': sig_code,
                       'compile_macros': compile_macros,
                      }]
          return test_dict

      def check_log(self, log_file_path, reports_dir) -> bool:
          return False

      def generate_covergroups(self, config_file) -> str:
          sv = " "
          return sv
        




