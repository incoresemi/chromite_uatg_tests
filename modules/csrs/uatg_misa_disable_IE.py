from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from yapsy.IPlugin import IPlugin


class uatg_misa_disable_IE(IPlugin):
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
        ext = validator(self.csr['extensions']['type']['warl'])
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'

        # Disabling I-extension if E is not implemented
        if ext.islegal(self.reset_val - (1 << 8)) and 'E' not in self.isa:
            # Checks the following conditions:
            # Set I-extension to 0: If set the go-to fail_case
            #                       Else check if I and E are complementary
            asm_code += f'\n\ncsrr x3, misa\n' \
                        f'# Disabling I extension\ntest_disable_I:{nt}' \
                        f'# E extension unavailable -> I shouldnt be updated' \
                        f'{nt}li x2, {1 << 8}{nt}csrc misa, x2{nt}' \
                        f'csrr x5, misa{nt}la x6, mtrap_sigptr{nt}' \
                        f'bne x5, x1, fail_case{nt}sw x0, 0(x6){nt}' \
                        f'{nt}# Checking whether I & E are complementary' \
                        f'{nt}# At this point, I = 1 -> E = 0.{nt}' \
                        f'# If E=1 goto fail_case{nt}' \
                        f'slli x4, x5, {self.xlen - 5}{nt}' \
                        f'srli x4, x4, {self.xlen - 1}{nt}bgtz x4, fail_case' \
                        f'{nt}csrw misa, x3\n'

        asm_code += f'\n\nj exit\nfail_case:{nt}' \
                    f'li x7, 1\nsw x7, 0(x6)\nexit:{nt}nop'

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
        yield test_dict
