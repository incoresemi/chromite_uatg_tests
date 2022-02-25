from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from uatg.instruction_generator import instruction_generator
from yapsy.IPlugin import IPlugin


class uatg_misa_disable_compressed(IPlugin):
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
        self.modifiers = {
            'xrs1': self.int_reg_file,
            'xrs2': self.int_reg_file,
            'xrd': self.int_reg_file,
            'frs1': self.float_reg_file,
            'frs2': self.float_reg_file,
            'frd': self.int_reg_file,
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
        ig = instruction_generator(isa=self.isa)

        nt = '\n\t'
        ext = validator(self.csr['extensions']['type']['warl'])
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'

        # Disabling & Enabling other extensions individually
        if 'C' in self.isa and ext.islegal(self.reset_val - (1 << 2)):
            # all_c_insts = 'c.nop\n' * 2
            all_c_insts = '\n\t'.join(
                ig.generate_all_c_inst(modifiers=self.modifiers))
            asm_code += f'\ncsrr x3, misa\nla x4, mtrap_sigptr\n' \
                        f'# Disabling & Enabling C extension\n' \
                        f'test_disable_C:{nt}.option push{nt}.option rvc{nt}' \
                        f'li x2, {hex(self.reset_val - (1 << 2))}{nt}' \
                        f'csrw misa, x2 # Clear 2nd bit{nt}' \
                        f'csrr x5, misa{nt}bne x2, x5, fail_case ' \
                        f'# If the bit is not written{nt}sw x0, 0(x4){nt}' \
                        f'.align 2\n{all_c_insts}{nt}.option pop{nt}' \
                        f'csrw misa, x3 # Reset misa to ' \
                        f'old value\n'

        asm_code += f'\n\nj exit\nfail_case:{nt}' \
                    f'li x6, 1\nsw x6, 0(x4)\nexit:{nt}nop'

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
