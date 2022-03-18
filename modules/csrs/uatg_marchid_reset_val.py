from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_marchid_reset_val(IPlugin):
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
        asm_code = f'\nli x1, {self.reset_val}\n'

        # checking the reset value
        asm_code += f'\n\n#  Checking whether reset_value matches with ' \
                    f'YAML specification\n' \
                    f'csrr x4, marchid\n' \
                    f'bne x4, x1, fail_case\n' \
                    f'la x5, mtrap_sigptr\n' \
                    f'sw x0, 0(x5)\n'

        asm_code += f'\nj exit\n' \
                    f'fail_case:\n\tli x6, 1 \n ' \
                    f'sw x6, 0(x5)\n'
        asm_code += f'exit:\n\tnop'

        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
        })
