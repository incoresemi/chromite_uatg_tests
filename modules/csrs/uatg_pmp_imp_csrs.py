from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_pmp_imp_csrs(IPlugin):
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
        asm_code = ''
        if self.isa == 32:
            asm_code = 'csrr x1, pmpcfg1\ncsrr x1, pmpcfg2\ncsrr x1, ' \
                       'pmpcfg3\ncsrr x1, pmpcfg4\ncsrr x1, pmpcfg5\ncsrr x1, ' \
                       'pmpcfg6\ncsrr x1, pmpcfg7\ncsrr x1, pmpcfg8\ncsrr x1, ' \
                       'pmpcfg9\ncsrr x1, pmpcfg10\ncsrr x1, pmpcfg11\ncsrr ' \
                       'x1, pmpcfg12\ncsrr x1, pmpcfg13\ncsrr x1, ' \
                       'pmpcfg14\ncsrr x1, pmpcfg15\n '
        elif self.isa == 64:
            asm_code = '# Valid CSR accesses\n\ncsrr x1, pmpcfg0\ncsrr x1, ' \
                       'pmpcfg2\ncsrr x1, pmpcfg4\ncsrr x1, pmpcfg6\ncsrr x1, ' \
                       'pmpcfg8\ncsrr x1, pmpcfg10\ncsrr x1, pmpcfg12\ncsrr ' \
                       'x1, pmpcfg14\ncsrr x1, pmpcfg16\ncsrr x1, ' \
                       'pmpcfg18\ncsrr x1, pmpcfg20\ncsrr x1, pmpcfg22\ncsrr ' \
                       'x1, pmpcfg24\ncsrr x1, pmpcfg26\ncsrr x1, ' \
                       'pmpcfg28\ncsrr x1, pmpcfg30\ncsrr x1, pmpcfg32\ncsrr ' \
                       'x1, pmpcfg34\ncsrr x1, pmpcfg36\ncsrr x1, ' \
                       'pmpcfg38\ncsrr x1, pmpcfg40\ncsrr x1, pmpcfg42\ncsrr ' \
                       'x1, pmpcfg44\ncsrr x1, pmpcfg46\ncsrr x1, ' \
                       'pmpcfg48\ncsrr x1, pmpcfg50\ncsrr x1, pmpcfg52\ncsrr ' \
                       'x1, pmpcfg54\ncsrr x1, pmpcfg56\ncsrr x1, ' \
                       'pmpcfg58\ncsrr x1, pmpcfg60\ncsrr x1, pmpcfg62\n\n\n' \
                       '# Invalid CSR accesses\n\ncsrr x1, pmpcfg1\ncsrr x1, ' \
                       'pmpcfg3\ncsrr x1, pmpcfg5\ncsrr x1, pmpcfg7\ncsrr x1, ' \
                       'pmpcfg9\ncsrr x1, pmpcfg11\ncsrr x1, pmpcfg13\ncsrr ' \
                       'x1, pmpcfg15\ncsrr x1, pmpcfg17\ncsrr x1, ' \
                       'pmpcfg19\ncsrr x1, pmpcfg21\ncsrr x1, pmpcfg23\ncsrr ' \
                       'x1, pmpcfg25\ncsrr x1, pmpcfg27\ncsrr x1, ' \
                       'pmpcfg29\ncsrr x1, pmpcfg31\ncsrr x1, pmpcfg33\ncsrr ' \
                       'x1, pmpcfg35\ncsrr x1, pmpcfg37\ncsrr x1, ' \
                       'pmpcfg39\ncsrr x1, pmpcfg41\ncsrr x1, pmpcfg43\ncsrr ' \
                       'x1, pmpcfg45\ncsrr x1, pmpcfg47\ncsrr x1, ' \
                       'pmpcfg49\ncsrr x1, pmpcfg51\ncsrr x1, pmpcfg53\ncsrr ' \
                       'x1, pmpcfg55\ncsrr x1, pmpcfg57\ncsrr x1, ' \
                       'pmpcfg59\ncsrr x1, pmpcfg61\ncsrr x1, pmpcfg63\n '
        asm_data = '.align 3\n' \
                   'sample:\n.dword 0xbabecafe\n'
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