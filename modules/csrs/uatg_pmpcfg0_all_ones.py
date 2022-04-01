from typing import Dict, List, Union, Any
from yapsy.IPlugin import IPlugin

class uatg_pmpcfg0_all_ones(IPlugin):
      """

      """
      def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.csr, self.reset_val = None, None

      def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32

        if 'pmpcfg0' in isa_yaml['hart0'].keys(): 
            self.reset_val = isa_yaml['hart0']['pmpcfg0']['reset-val']
            if self.xlen == 32 and isa_yaml['hart0']['pmpcfg0']['rv32'][
               'accessible']:      
               self.csr = isa_yaml['hart0']['pmpcfg0']['rv32']
            elif self.xlen == 64 and isa_yaml['hart0']['pmpcfg0']['rv64'][
               'accessible']:
               self.csr = isa_yaml['hart0']['pmpcfg0']['rv64']
            else:
               return False                 
        else:
            return False
        return True

      def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
         
        # unim  |unim   |uni    |unim    |00000000|00000000|00000000|00000000
        #pmp7cfg|pmp6cfg|pmp5cfg|pmp4cfg |pmp3cfg |pmp2cfg |pmp1cfg |pmp0cfg
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'
        # check if all bits are one
        val = '0xffffffffffffffff'
        asm_code += f' #check if all bits are one and unimplemented \n'\
                    f' # fields get 0 \n'\
                    f' la x4, mtrap_sigptr \n ' \
                    f' li x2, {val}\n'\
                    f' csrw pmpcfg0, x2\n'\
                    f' csrr x3, pmpcfg0\n'\
                    f' bne x2, x3, testpass\n'\
                    f' li x1, 1\n'\
                    f' testpass:\n'\
                    f' nop\n'
        sig_code =  f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                    f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
       
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']

        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
        }) 
