import random
from typing import Dict, List, Union, Any
from riscv_config.warl import warl_interpreter as validator
from yapsy.IPlugin import IPlugin

class uatg_pmpcfg0_pmp0cfg_field(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.fields = ['pmp0cfg', 'pmp1cfg','pmp2cfg','pmp3cfg',
                        'pmp4cfg','pmp5cfg','pmp6cfg','pmp7cfg']
        self.csr, self.fields, self.reset_val = None, None, None
        self.dep   =  None
        
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
        self.fields = [i for i in self.csr['fields'] if isinstance(i, str)]
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        
        # 63   55 56   48 47  40 39    32 31    24 23    16 15     8 7      0
        # unim   |unim   |unim   |unim   |00000000|00000000|00000000|00000000
        # pmp7cfg|pmp6cfg|pmp5cfg|pmp4cfg|pmp3cfg |pmp2cfg |pmp1cfg |pmp0cfg
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'
        lsb = self.csr['pmp0cfg']['lsb']
        msb = self.csr['pmp0cfg']['msb']
        value = random.choice(range(0,2 ** (msb-lsb+1)))
        asm_code =  f' li x1, {self.reset_val}\n'
        asm_code += f' #check if the value is legal it\n'\
                    f' #should be written in the csr\n'\
                    f' la x4, mtrap_sigptr\n'\
                    f' li x2, {hex(value)}\n'\
                    f' csrw pmpcfg0,x2\n'\
                    f' csrr x3, pmpcfg0\n'\
                    f' beq x2, x3 , testpass\n'\
                    f' testfail:\n\tli x1, 1\n'\
                    f' testpass:\n\tnop\n'

        sig_code =  f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                    f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n' 

        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']

        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
        }) 
