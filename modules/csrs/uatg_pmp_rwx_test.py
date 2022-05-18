from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_pmp_rwx_test(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        hart = isa_yaml['hart0']
        if hart['pmpcfg0']['rv32']['accessible'] or \
                hart['pmpcfg0']['rv64']['accessible']:
            return True
        return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        asm_code = 'li x1, 0b10010111e\n' \
                   'csrrw x2, pmpcfg0, x1\n' \
                   'la x3, read_location\n' \
                   'csrrw x4, pmpaddr0, x3\n'
        asm_data = '.align 3\n' \
                   'read_location:\n.dword 0xbabecafe\n'
        sig_code = f'\nmtrap_count:\n .fill 1, 2, 0x0\n' \
                   f'.align 2\nmtrap_sigptr:\n.fill {2}, 4, 0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        privileged_test_enable = True

        privileged_test_dict = {
            'enable': privileged_test_enable,
            'mode': 'machine',
            'page_size': 4096,
            'paging_mode': 'sv39',
            'll_pages': 64,
        }
        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'asm_data': asm_data,
            'compile_macros': compile_macros,
            'privileged_test': privileged_test_dict
        })