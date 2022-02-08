from typing import Dict, List, Union, Any

from riscv_config.warl import warl_interpreter as validator
from yapsy.IPlugin import IPlugin


class uatg_misa_misaligned_compressed(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV3  2I', 32
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
        nt = '\n\t'
        ext = validator(self.csr['extensions']['type']['warl'])
        asm_code = f'.option norvc\nli x1, {self.reset_val}\n'

        # Disable C with subsequent Instruction not aligned to 4 Byte boundry
        if 'C' in self.isa and ext.islegal(self.reset_val - (1 << 2)):
            asm_code += '\n# Disable C with subsequent Instruction not ' \
                        f'aligned to 4 Byte boundry\n' \
                        f'la x5, mtrap_sigptr\n' \
                        f'test_c_misalign:.option push{nt}.option rvc{nt}' \
                        f'.align 2 #aligns to 4 byte ' \
                        f'boundary{nt}csrr x1, misa{nt}c.nop{nt}csrc misa, x1' \
                        f' #4 byte instruction to be misaligned{nt}' \
                        f'bne x3, x4, fail_case ' \
                        f'# if x3!=x4 jump to fail_case{nt}' \
                        f'sw x0, 0(x5){nt}.option pop\n'

        asm_code += f'\n\nj exit\nfail_case:{nt}' \
                    f'li x6, 1\nsw x6, 0(x4)\nexit:{nt}nop'

        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']
        test_dict = [{
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros
        }]
        return test_dict

    def check_log(self, log_file_path, reports_dir):
        pass

    def generate_covergroups(self, config_file):
        pass
