from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_pmp_fields_check(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.reset_val = None
        self.isa, self.xlen = 'RV32I', 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        hart = isa_yaml['hart0']
        if hart['pmpcfg0']['rv32']['accessible'] or \
                hart['pmpcfg0']['rv64']['accessible']:
            self.reset_val = hart['pmpcfg0']['reset-val']
            return True
        return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:

        asm_code = f'# Checking whether R bits can be set and cleared\n\n'
        imp_csrs = 2
        if self.xlen == 32:
            asm_code += f'li x1, 0x1010101\n'
            for i in range(0, imp_csrs + 1, 1):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'
        else:
            asm_code += f'li x1, 0x101010101010101\n'
            for i in range(0, imp_csrs + 1, 2):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'

        asm_code += f'\n# Checking whether W bits can be set and cleared\n' \
                    f'# W cant be set alone, so setting along with R bits\n\n'
        if self.xlen == 32:
            asm_code += f'li x1, 0x3030303\n'
            for i in range(0, imp_csrs + 1, 1):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'
        else:
            asm_code += f'li x1, 0x303030303030303\n'
            for i in range(0, imp_csrs + 1, 2):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'

        asm_code += f'\n# Checking whether X bits can be set and cleared\n\n'
        if self.xlen == 32:
            asm_code += f'li x1, 0x4040404\n'
            for i in range(0, imp_csrs + 1, 1):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'
        else:
            asm_code += f'li x1, 0x404040404040404\n'
            for i in range(0, imp_csrs + 1, 2):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1\n'

        asm_code += f'\n# Checking whether A bits can be set and cleared\n\n'
        if self.xlen == 32:
            asm_code += f'li x1, 0x08080808\n' \
                        f'li x2, 0x10101010\n' \
                        f'li x3, 0x18181818\n'
            for i in range(0, imp_csrs + 1, 1):
                asm_code += f'csrrs x5, pmpcfg{i}, x1\n' \
                            f'csrrs x5, pmpcfg{i}, x2\n' \
                            f'csrrs x5, pmpcfg{i}, x3\n' \
                            f'csrrc x2, pmpcfg{i}, x3\n'
        else:
            asm_code += f'li x1, 0x0808080808080808\n' \
                        f'li x2, 0x1010101010101010\n' \
                        f'li x3, 0x1818181818181818\n'
            for i in range(0, imp_csrs + 1, 2):
                asm_code += f'csrrs x5, pmpcfg{i}, x1\n' \
                            f'csrrs x5, pmpcfg{i}, x2\n' \
                            f'csrrs x5, pmpcfg{i}, x3\n' \
                            f'csrrc x2, pmpcfg{i}, x3\n'

        asm_code += f'\n# Checking whether L bits can be set\n\n'
        if self.xlen == 32:
            asm_code += f'li x1, 0x80808080\n'
            for i in range(0, imp_csrs + 1, 1):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n'
        else:
            asm_code += f'li x1, 0x8080808080808080\n'
            for i in range(0, imp_csrs + 1, 2):
                asm_code += f'csrrs x2, pmpcfg{i}, x1\n' \
                            f'csrrc x2, pmpcfg{i}, x1  #shouldnt get cleared\n'

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
