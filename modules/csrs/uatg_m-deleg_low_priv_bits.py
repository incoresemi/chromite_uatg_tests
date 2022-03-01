from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_m_deleg_low_priv_bits(IPlugin):
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

        mideleg_ro_0 = (1 << 3) + (1 << 7) + (1 << 11)
        medeleg_ro_0 = (1 << 11)

        mideleg_ro_0 += (1 << 12) + (1 << 10) + (1 << 6) + (1 << 2) \
            if 'H' in self.isa else 0

        asm_code = f'li x1, {self.e_reset_val}  # medeleg reset value\n' \
                   f'la x5, mtrap_sigptr\nmedeleg_test:{nt}' \
                   f'csrr x3, medeleg{nt}li x2, {hex(medeleg_ro_0)} ' \
                   f'# bitmask of 1<<11{nt}csrw medeleg, x2{nt}' \
                   f'csrr x3, medeleg{nt}bne x3, x0, medeleg_fail_case{nt}' \
                   f'sw x0, 0(x5){nt}j mideleg_test\n' \
                   f'medeleg_fail_case:{nt}li x4, 1{nt}sw x4, 0(x5)\n\n\n' \
                   f'mideleg_test:{nt}' \
                   f'li x1, {self.i_reset_val}  # mideleg reset value{nt}' \
                   f'csrr x3, medeleg{nt}' \
                   f'li x2, {hex(mideleg_ro_0)} ' \
                   f'# bitmask of {bin(mideleg_ro_0)}{nt}' \
                   f'# Checking if GIELEN is non-zero => bit 12 mideleg RO1' \
                   f'{nt}# csrr x6, hgeip{nt}# beqz x6, continue{nt}' \
                   f'# li x6, {hex(1<<12)}{nt}# add x2, x2, x6\n' \
                   f'# continue:{nt}efcsrw mideleg, x2{nt}csrr x3, mideleg{nt}' \
                   f'bne x3, x0, mideleg_fail_case{nt}sw x0, 4(x5){nt}' \
                   f'j exit\nmideleg_fail_case:{nt}li x4, 1{nt}sw x4, 4(x5)\n' \
                   f'exit:{nt}nop\n\n'
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
