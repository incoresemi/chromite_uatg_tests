from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_misa_reset_val(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.fields = ['extensions', 'mxl']
        self.csr, self.fields, self.reset_val = None, None, None
        self.mpp = None

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

        if 'misa' in isa_yaml['hart0'].keys():
            self.reset_val = isa_yaml['hart0']['misa']['reset-val']
            if self.xlen == 32 and isa_yaml['hart0']['misa']['rv32'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['misa']['rv32']
            elif self.xlen == 64 and isa_yaml['hart0']['misa']['rv64'][
                    'accessible']:
                self.csr = isa_yaml['hart0']['misa']['rv64']
            else:
                return False
        else:
            return False
        self.fields = [i for i in self.csr['fields'] if isinstance(i, str)]
        return True  # returns true after checks are done

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:

        #  10|000000000000000000000000000000000000|00000101000001000100000101
        # MXL|             zeros                  |ZYXWVUTSRQPONMLKJIHGFEDCBA

        nt = '\n\t'
        asm_code = f'\nli x1, {self.reset_val}\n'

        # Checking if reset_val matches with yaml specification
        asm_code += f'\n\n# Checking whether reset_value matches with ' \
                    f'YAML specification\ntest_reset_val:{nt}csrr x4, misa' \
                    f'{nt}bne x4, x1, fail_case\nla x5, reset_val_sigptr\n' \
                    f'sw x0, 0(x5)\n'
        asm_code += f'\n\nj exit\nfail_case:{nt}' \
                    f'li x6, 1\nsw x6, 0(x5)\nexit:{nt}nop'

        sig_code = f'reset_val_sigptr:\n.fill {1},4,0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        test_dict = [{
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'name_postfix': 'machine'
        }]
        yield test_dict
