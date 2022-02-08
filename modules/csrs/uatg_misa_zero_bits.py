from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from yapsy.IPlugin import IPlugin


class uatg_misa_disable_zero_bits(IPlugin):
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
        self.modifiers = {
            'xrs1': self.int_reg_file,
            'xrs2': self.int_reg_file,
            'xrd': self.int_reg_file,
        }

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

        # Enabling Zero bits
        _lsb = self.csr['extensions']['msb']
        _bit_width = (self.csr['mxl']['lsb'] - _lsb - 1)
        zero_bits = self.reset_val + (((1 << _bit_width) - 1) << _lsb)
        if ext.islegal(zero_bits):
            asm_code += f'\n\ncsrr x3, misa \n' \
                        f'# Enabling Zero Bits\ntest_zero_bits:{nt}' \
                        f'li x2, {zero_bits}{nt}csrs misa, x2{nt}' \
                        f'csrr x4, misa{nt}bne x4, x3, fail_case\n' \
                        f'csrw misa, x3 # Reset misa to old value\n\n'

        asm_code += f'\n\n\nj exit\nfail_case:{nt}nop{nt}nop\nexit:{nt}nop'
        test_dict = [{
            'asm_code': asm_code,
        }]
        return test_dict
