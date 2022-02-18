from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_m_deleg_RO1(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.medeleg, self.mideleg = None, None
        self.i_reset_val, self.e_reset_val = None, None
        self.mpp = None

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

            if self.xlen == 32 and spec['medeleg']['rv32']['accessible']\
                    and spec['mideleg']['rv32']['accessible']:
                self.medeleg = spec['medeleg']['rv32']
                self.mideleg = spec['mideleg']['rv32']
            elif self.xlen == 64 and spec['medeleg']['rv64']['accessible']\
                    and spec['medeleg']['rv64']['accessible']:
                self.medeleg = spec['medeleg']['rv64']
                self.mideleg = spec['mideleg']['rv64']
            else:
                return False
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        nt = '\n\t'
        asm_code = f'.option norvc\n\nla x5, mtrap_sigptr\n' \
                   f'li x1, {self.e_reset_val}\n' \
                   f'csrr x3, medeleg\n' \
                   f'csrw medeleg, x0  # writing 0s to medeleg\n' \
                   f'csrr x4, medeleg\nbne x4, x0, fail_case_medeleg\n' \
                   f'csrw medeleg, x1\n' \
                   f'sw x0, 0(x5)\n\n' \
                   f'fail_case_medeleg:\n\tli x6, 1\n\tsw x1, 0(x5)\n\n\n' \
                   f'li x1, {self.i_reset_val}\n' \
                   f'csrr x3, mideleg\n' \
                   f'csrw mideleg, x0  # writing 0s to mideleg\n' \
                   f'csrr x4, mideleg\nbne x4, x0, fail_case_mideleg\n' \
                   f'csrw mideleg, x1\n\n\n\n' \
                   f'fail_case_mideleg:\n\tli x6, 1\n\tsw x1, 4(x5)\n\n\n'
        sig_code = f'\nmtrap_count:\n .fill 1, 2, 0x0\n' \
                   f'.align 2\nmtrap_sigptr:\n.fill {2}, 4, 0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        test_dict = [{
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
            'name_postfix': 'machine'
        }]
        return test_dict
