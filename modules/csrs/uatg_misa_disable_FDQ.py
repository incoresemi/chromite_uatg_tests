from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from uatg.instruction_generator import instruction_generator
from yapsy.IPlugin import IPlugin


class uatg_misa_disable_FDQ(IPlugin):
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

        nt = '\n\t'
        ext = validator(self.csr['extensions']['type']['warl'])
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'
        ig = instruction_generator(isa=self.isa)

        # Disabling & Enabling F extension
        if 'F' in self.isa and ext.islegal(self.reset_val - (1 << 5)):
            all_f_insts = 'fadd.s f0, f0, f0'
            # all_f_insts = '\n\t'.join(
            #     ig.generate_all_f_inst(modifiers=self.modifiers))
            asm_code += f'\ncsrr x3, misa\nla x4, mtrap_sigptr\n' \
                        f'# Disabling & Enabling F extension\n' \
                        f'test_disable_F:{nt}' \
                        f'li x2, {hex(self.reset_val - (1 << 5))}{nt}' \
                        f'csrw misa, x2 # Clear 5rd bit{nt}' \
                        f'csrr x5, misa{nt}beq x2, x5, fail_case ' \
                        f'# If the bit is not written{nt}sw x0, 0(x4){nt}' \
                        f'addi x4, x4, 4 # incrementing mtrap_sigptr{nt}' \
                        f'{all_f_insts}{nt}csrw misa, x3 # Reset misa to ' \
                        f'old value\n'

        # Disabling & Enabling D extension
        if 'D' in self.isa and ext.islegal(self.reset_val - (1 << 3)):
            all_d_insts = 'fadd.d f0, f0, f0'
            # all_d_insts = '\n\t'.join(
            #     ig.generate_all_d_inst(modifiers=self.modifiers))
            asm_code += f'\ncsrr x3, misa\nla x4, mtrap_sigptr\n' \
                        f'# Disabling & Enabling D extension individually\n' \
                        f'test_disable_D:{nt}' \
                        f'li x2, {hex(self.reset_val - (1 << 3))}{nt}' \
                        f'csrw misa, x2 # Clear 3rd bit{nt}' \
                        f'csrr x5, misa{nt}beq x2, x5, fail_case ' \
                        f'# If the bit is not written{nt}sw x0, 0(x4){nt}' \
                        f'addi x4, x4, 4 # incrementing mtrap_sigptr{nt}' \
                        f'{all_d_insts}{nt}csrw misa, x3 # Reset misa to ' \
                        f'old value\n'

            asm_code += '\n\ncsrr x3, misa \n' \
                        f'# Enabling D after disabling F\n' \
                        f'test_DF:{nt}' \
                        f'li x2, {1 << 5}{nt}csrc misa, x2{nt}li x2, {1 << 3}' \
                        f'{nt}csrs misa, x2{nt}fadd.d f0, f0, f0{nt}' \
                        f'csrw misa, x3 # Reset misa to old value\n\n' \
                        f'# Enabling D before disabling F\n' \
                        f'test_FD:{nt}li x2, {1 << 3}{nt}csrs misa, x2{nt}' \
                        f'li x2, {1 << 3}{nt}csrc misa, x2{nt}' \
                        f'fadd.d f0, f0, f0{nt}csrw misa, x3 ' \
                        f'# Reset misa to old value\n'

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
        return test_dict
