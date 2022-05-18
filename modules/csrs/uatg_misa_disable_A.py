from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from uatg.instruction_generator import instruction_generator
from yapsy.IPlugin import IPlugin


class uatg_misa_disable_atomic(IPlugin):
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
        ig = instruction_generator(isa=self.isa)

        # Disabling & Enabling Atomic extension
        if 'A' in self.isa and ext.islegal(self.reset_val - (1 << 0)):
            all_a_insts = '\n\t'.join(
                ig.generate_all_a_inst(modifiers=self.modifiers))
            asm_code += f'\ncsrr x3, misa\nla x4, mtrap_sigptr\n' \
                        f'# Disabling & Enabling A extension\n' \
                        f'test_disable_A:{nt}' \
                        f'csrr x5, misa{nt}' \
                        f'li x2, {hex(self.reset_val - (1 << 0))}{nt}' \
                        f'csrw misa, x2 # Clear 0th bit{nt}' \
                        f'beq x2, x5, fail_case ' \
                        f'# If the bit is not written{nt}{all_a_insts}{nt}' \
                        f'sw x0, 0(x4){nt}csrw misa, x3 # Reset misa to ' \
                        f'old value\n'

        asm_code += f'\n\nj exit\nfail_case:{nt}' \
                    f'li x6, 1\nsw x6, 0(x4)\nexit:{nt}nop'

        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']

        privileged_test_dict = {
                    'enable' : True
        }

        yield({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
            'privileged_test': privileged_test_dict,
            'name_postfix': 'machine'
        })
        
