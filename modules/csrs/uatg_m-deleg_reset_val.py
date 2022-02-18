from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_medeleg_reset_val(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.medeleg, self.mideleg = None, None
        self.e_reset_val, self.i_reset_val = None, None

        # Follow the register usage convention strictly
        # x1  - reset_val
        # x2  - bit mask
        # x3  - csr output
        # x4-x10 - temp
        # x11-31 - random instructions
        self.int_reg_file = ['x' + str(i) for i in range(11, 32)]

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        spec = isa_yaml['hart0']

        if 'medeleg' in spec.keys() and 'mideleg' in spec.keys():
            self.e_reset_val = spec['medeleg']['reset-val']
            self.i_reset_val = spec['mideleg']['reset-val']

            if self.xlen == 32 and spec['medeleg']['rv32']['accessible'] \
                    and spec['mideleg']['rv32']['accessible']:
                self.medeleg = spec['medeleg']['rv32']
                self.mideleg = spec['mideleg']['rv32']
            elif self.xlen == 64 and spec['medeleg']['rv64']['accessible'] \
                    and spec['medeleg']['rv64']['accessible']:
                self.medeleg = spec['medeleg']['rv64']
                self.mideleg = spec['mideleg']['rv64']
            else:
                return False
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        nt = '\n\t'
        asm_code = ''

        # Checking if reset_val matches with yaml specification
        asm_code += f'\n\n# Checking whether reset_value matches with ' \
                    f'YAML specification\nla x5, mtrap_sigptr\n' \
                    f'\nli x1, {self.e_reset_val}\n' \
                    f'medeleg_reset_val:{nt}csrr x4, medeleg{nt}' \
                    f'bne x4, x1, medeleg_fail_case\n' \
                    f'sw x0, 0(x5)\n' \
                    f'\nli x1, {self.i_reset_val}\n' \
                    f'mideleg_reset_val:{nt}csrr x4, mideleg{nt}' \
                    f'bne x4, x1, mideleg_fail_case\n' \
                    f'sw x0, 4(x5)\n'
        asm_code += f'\n\nmedeleg_fail_case:{nt}' \
                    f'li x6, 1\nsw x6, 0(x5)\nj mideleg_reset_val\n' \
                    f'\n\nmideleg_fail_case:{nt}' \
                    f'li x6, 1\nsw x6, 4(x5)\n' \
                    f'exit:{nt}nop'

        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        test_dict = [{
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
            'name_postfix': 'machine'
        }]
        return test_dict
