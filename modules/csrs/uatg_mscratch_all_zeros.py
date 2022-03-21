from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_mscratch_all_zeros(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.csr, self.reset_val = None, None

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32

        if 'mscratch' in isa_yaml['hart0'].keys():
            self.reset_val = isa_yaml['hart0']['mscratch']['reset-val']
            if self.xlen == 32 and isa_yaml['hart0']['mscratch']['rv32'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['mscratch']['rv32']
            elif self.xlen == 64 and isa_yaml['hart0']['mscratch']['rv64'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['mscratch']['rv64']
            else:
                return False
        else:
            return False
        # returns true after checks are done
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # check all bits are zero
        all_zeros = '0x0000000000000000'
        nt = '\n\t'
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'

        asm_code += f' la x4, mtrap_sigptr \n ' \
                    f' csrr x5, mscratch \n' \
                    f' li x2, {all_zeros}\n' \
                    f' csrw mscratch, x2 \n' \
                    f' csrr x3, mscratch \n' \
                    f' beq x2, x3 , testpass\n' \
                    f' sw x0, 0(x4)\n' \
                    f' csrw mscratch, x1\n'

        asm_code += f'\n\n\nj exit\ntestpass:{nt}li x7, 5\nexit:{nt}nop'
        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'

        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']

        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
        })
