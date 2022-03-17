from yapsy.IPlugin import IPlugin
from typing import Dict, List, Union, Any

class uatg_mvendorid_reset_val(IPlugin):
      """
      """
      
      def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.csr, self.reset_val = None, None



        # Follow the register usage convention strictly
        # x1  - reset_val
        # x2  - bit mask
        # x3  - csr output
        # x4-x10 - temp
        # x11-31 - random instructions
        self.int_reg_file = ['x' + str(i) for i in range(11, 32)]
        self.float_reg_file = ['f' + str(i) for i in range(0, 32)]

      def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32

        if 'mvendorid' in isa_yaml['hart0'].keys():
            self.reset_val = isa_yaml['hart0']['mvendorid']['reset-val']
            if self.xlen == 32 and isa_yaml['hart0']['mvendorid']['rv32'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['mvendorid']['rv32']
       
            elif self.xlen == 64 and isa_yaml['hart0']['mvendorid']['rv64'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['mvendorid']['rv64']
                return True 
            else:
                return False
            return True
        else:
            return False

   
      def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
          
          asm_code = f'\nli x1, {self.reset_val}\n'

          # checking the reset value
          asm_code += f'\n\n#  Checking whether reset_value matches with ' \
                      f'YAML specification\n'\
                      f'csrr x4, mvendorid\n' \
                      f'bne x4, x1, fail_case\n'\
                      f'la x5, reset_val_sigptr\n' \
                      f'sw x0, 0(x5)\n'
          
          asm_code += f'\nj exit\n'\
                      f'fail_case:\n\tli x6, 1'\
                      f' \nsw x6, 0(x5)'
          asm_code += f'\nexit:\n\tnop'
            
          sig_code =  f'reset_val_sigptr:\n.fill {1}, 4,0xdeadbeef\n'
          
          #compile macros for the test
          compile_macros=['rvtest_mtrap_routine']
          test_dict = [{'asm_code': asm_code,
                        'asm_sig': sig_code,
                        #'compile_macros': compile_macros,
                      }]
          return test_dict

      def check_log(self, log_file_path, reports_dir) -> bool:
          return False

      def generate_covergroups(self, config_file) -> str:
          sv = " "
          return sv
        

