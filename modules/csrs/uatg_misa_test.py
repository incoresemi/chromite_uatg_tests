from random import randint

from yapsy.IPlugin import IPlugin
from typing import Dict, List, Union, Any
from riscv_config.warl import warl_interpreter as validator
from uatg.instruction_generator import instruction_generator


class uatg_misa_test(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.fields = ['extensions', 'mxl']
        self.csr, self.fields, self.reset_val = None, None, None
        self.mpp = None

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
        try:
            self.mpp = isa_yaml['hart0']['mstatus'][f'rv{self.xlen}']['mpp']
        except KeyError:
            raise 'MSTATUS CSR required for this test'
        return True  # returns true after checks are done

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:

        #  10|000000000000000000000000000000000000|00000101000001000100000101
        # MXL|             zeros                  |ZYXWVUTSRQPONMLKJIHGFEDCBA

        # x1  - reset_val
        # x2  - bit mask
        # x3  - csr output
        # x4+ - temp
        ext = validator(self.csr['extensions']['type']['warl'])
        asm_code = f'\nli x1, {self.reset_val}\n'
        ig = instruction_generator(isa=self.isa)
        # Checking if reset_val matches with yaml specification
        asm_code += f'\n\n# 0. Checking whether reset_value matches with ' \
                    f'YAML specification\ncsrr x4, misa\n' \
                    f'bne x4, x1, fail_case\n'

        # Disabling I-extension if E is not implemented
        if ext.islegal(self.reset_val - (1 << 8)) and 'E' not in self.isa:
            # Checks the following conditions:
            # Set I-extension to 0: If set the go-to fail_case
            #                       Else check if I and E are complementary
            asm_code += f'\n\n# 1. Disabling I extension\n' \
                        f'# E extension unavailable -> I shouldnt be updated' \
                        f'\nli x2, {1 << 8}\ncsrc misa, x2\ncsrr x3, misa\n' \
                        f'bne x3, x1, fail_case\n' \
                        '\n# Checking whether I & E are complementary\n' \
                        '# At this point, I = 1 -> E = 0.\n' \
                        '# If E=1 goto fail_case\n' \
                        f'slli x4, x3, {self.xlen - 5}\n' \
                        f'srli x4, x4, {self.xlen - 1}\nbgtz x4, fail_case\n'

        # Disabling & Enabling other extensions individually
        if 'A' in self.isa and ext.islegal(self.reset_val - (1 << 0)):
            asm_code += f'\n# 2a. Disabling & Enabling A extension\n' \
                        f'li x2, {1 << 0}\n' \
                        f'li x5, {randint(80001000, 80002000)}\n' \
                        f'csrc misa, x2 # Clear 0th bit\nlr.w x4, (x5)\n' \
                        f'csrs misa, x2 # Set 0th bit\nlr.w x4, (x5)\n'
        if 'B' in self.isa and ext.islegal(self.reset_val - (1 << 1)):
            asm_code += f'\n# 2b. Disabling & Enabling B extension\n' \
                        f'li x2, {1 << 1} \ncsrc misa, x2 # Clear 1st bit' \
                        f'\nclz x0, x1\ncsrs misa, x2  # Set 1st bit\n' \
                        f'clz x0, x1\n'
        if 'C' in self.isa and ext.islegal(self.reset_val - (1 << 2)):
            asm_code += f'\n# 2.c Disabling & Enabling C extension\n' \
                        f'li x2, {1 << 2}\ncsrc misa, x2 # Clear 2nd bit\n' \
                        f'c.nop\ncsrs misa, x2 # Set 2nd bit\nc.nop\n'
        if 'D' in self.isa and ext.islegal(self.reset_val - (1 << 3)):
            asm_code += f'\n# 2.d Disabling & Enabling D extension\n' \
                        f'li x2, {1 << 3}\ncsrc misa, x2 # Clear 3rd bit\n' \
                        f'fadd.d f0, f0, f0\n' \
                        f'csrs misa, x2 # Set 3rd bit\nfadd.d f0, f0, f0\n'
        # Disabling E is a special case. Dealt later
        if 'F' in self.isa and ext.islegal(self.reset_val - (1 << 5)):
            asm_code += f'\n# 2.f Disabling & Enabling F extension\n' \
                        f'li x2, {1 << 5}\ncsrc misa, x2 # Clear 5th bit\n' \
                        f'fadd.s f0, f0, f0\n' \
                        f'csrs misa, x2 # Set 5th bit\nfadd.s f0, f0, f0\n'
        if 'M' in self.isa and ext.islegal(self.reset_val - (1 << 12)):
            all_m_insts = '\n'.join(ig.generate_all_m_inst())
            asm_code += f'\n# 2m. Disabling & Enabling M extension\n' \
                        f'li x2, {1 << 12}\ncsrc misa, x2 # Clear 12th bit\n' \
                        f'# All M instructions\n{all_m_insts}\n' \
                        f'csrs misa, x2 # Set 12th bit\n{all_m_insts}\n'
        if 'S' in self.isa and ext.islegal(self.reset_val - (1 << 18)):
            asm_code += f'\n# 2s. Disabling & Enabling S extension\n' \
                        f'li x2, {1 << 18}\ncsrc misa, x2 # Clear 18th bit\n' \
                        f'csrr x4, sstatus\n' \
                        f'csrs misa, x2 # Set 18th bit\ncsrr x4, sstatus\n'
        if 'U' in self.isa and ext.islegal(self.reset_val - (1 << 20)):
            # Disable Supervisor mode and access Supervisor CSR's
            _lsb, _msb = self.mpp['lsb'], self.mpp['msb']
            _bit_width = (_msb - _lsb + 1)
            mpp_bits = (((1 << _bit_width) - 1) << _lsb)

            asm_code += f'\n# 2s. Disabling & Enabling U extension\n' \
                        f'li x2, {1 << 20}\ncsrc misa, x2 # Clear 20th bit\n' \
                        f'csrr x3, mstatus # Copying mstatus before making it' \
                        f'dirty\nli x31, {mpp_bits}\ncsrc mstatus, x31 ' \
                        f'# Clear mpp bits of mstatus\nMRET\n' \
                        f'csrr x4, mstatus\nbne x4, x3, fail_case' \
                        f'csrs misa, x2 # Set 20th bit\nMRET\n' \
                        f'csrw mstatus, x3 # Rewriting mstatus to old value\n\n'

        # Enabling unimplemented extensions
        unimplemented_ext = self.reset_val + (self.reset_val % 2**26) ^ (
            (1 << 27) - 1)
        if ext.islegal(unimplemented_ext):
            asm_code += f'\n# 3. Enabling Unimplemented extensions\n'
            asm_code += f'li x2, {unimplemented_ext}\ncsrs misa, x2\n' \
                        f'csrr x3, misa\nbne x3, x1, fail_case\n'

        if 'E' in self.isa:
            asm_code += f'\n# 4. Checking whether I & E are complementary\n'
            if (self.reset_val >> 4) % 1:
                asm_code += '# E is available and enabled -> Check I = 0\n' \
                            '# If I=1 goto fail_case\n' \
                            'add x0, x0, x0\nadd x20, x20, x20\n' \
                            'csrr x3, misa\n' \
                            f'slli x4, x3, {self.xlen - 8}\n' \
                            f'srli x4, x4, {self.xlen - 1}\n' \
                            f'bgtz x4, fail_case\n'
            else:
                asm_code += '# E is available but disabled \n' \
                            '# Set I=0 & Check E = 1\n' \
                            f'\nli x2, {1 << 8}\ncsrc misa, x2\n' \
                            'add x0, x0, x0\nadd x20, x20, x20\n' \
                            f'csrr x3, misa\n' \
                            '# If E=0 goto fail_case\n' \
                            f'slli x4, x3, {self.xlen - 5}\n' \
                            f'srli x4, x4, {self.xlen - 1}\n' \
                            f'beqz x4, fail_case\n#Going back to I mode\n' \
                            f'csrs misa, x2'

        if 'D' in self.isa:
            asm_code += '\n\ncsrr x31, misa \n' \
                        f'# Reading the csr status before manipulation\n' \
                        f'# 5a. Enabling D after disabling F\n' \
                        f'li x2, {1 << 5}\ncsrc misa, x2\nli x2, {1 << 3}\n' \
                        f'csrs misa, x2\nfadd.d f0, f0, f0\n' \
                        f'csrw misa, x31 # reseting misa to previous value\n' \
                        f'# 5b. Enabling D before disabling F\n' \
                        f'li x2, {1 << 3}\ncsrs misa, x2\nli x2, {1 << 3}\n' \
                        f'csrc misa, x2\nfadd.d f0, f0, f0\n' \
                        f'csrw misa, x31 # reseting misa to previous value\n' \

        # Disable C with subsequent Instruction not aligned to 4 Byte boundry
        if 'C' in self.isa:
            asm_code += '\n# 6. Disable C with subsequent Instruction not ' \
                        'aligned to 4 Byte boundry\n.align 2 #aligns to 4 ' \
                        f'byte boundary\nli x2, {1 << 2}\ncsrs misa, x2\n' \
                        'c.nop\ncsrr x3, misa\ncsrc misa, x2 ' \
                        '# clearing C bit\ncsrr x4, misa #4 byte instruction ' \
                        'to be misaligned\nbne x3, x4, fail_case ' \
                        '# if x3!=x4 jump to fail_case\n'

        # Enabling Zero bits
        _lsb = self.csr['extensions']['msb']
        _bit_width = (self.csr['mxl']['lsb'] - _lsb - 1)
        zero_bits = self.reset_val + (((1 << _bit_width) - 1) << _lsb)
        if ext.islegal(zero_bits):
            asm_code += f'\n# 7. Enabling Zero Bits\n'
            asm_code += f'li x2, {zero_bits}\ncsrs misa, x2\ncsrr x3, misa\n' \
                        f'bne x3, x1, fail_case\n'

        # Write illegals in MXL
        mxl = validator(self.csr['mxl']['type']['warl'])
        _lsb, _msb = self.csr['mxl']['lsb'], self.csr['mxl']['msb']
        asm_code += f'\n# 8. Write illegals in MXL\n'
        for value in range(0, 2**(_msb - _lsb + 1)):
            r_val = list(bin(self.reset_val)[2:])[::-1]
            if not mxl.islegal(value):  # if value is illegal
                illegal_value = r_val.copy()

                illegal_value[_lsb:_msb + 1] = list(
                    bin(value)[2:].zfill(_msb - _lsb + 1)[::-1])
                illegal_value = int(''.join(illegal_value[::-1]), 2)

                asm_code += f'\n# MXL = 0b{bin(value)[2:].zfill(2)}\n' \
                            f'add x3, x1, x0 #x3 = reset_val for default\n' \
                            f'li x2, {hex(illegal_value)}\n' \
                            f'csrrw x3, misa, x2\nbne x3, x1, fail_case\n' \

        asm_code += f'\n\n\nj exit\nfail_case:\n\tnop\n\tnop\nexit:\n\tnop'
        test_dict = [{'asm_code': asm_code,
                      # 'asm_sig': sig_code,
                      # 'compile_macros': compile_macros,
                      }]
        return test_dict

    def check_log(self, log_file_path, reports_dir):
        pass

    def generate_covergroups(self, config_file):
        pass
