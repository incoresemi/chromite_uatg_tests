# python program to generate an assembly file which checks if mis-predictions
# occur In addition to this, the GHR is also filled with ones (additional
# test case) uses assembly macros

from typing import Dict, List, Union, Any

# To-Do -> Create another function which prints the includes and other
# assembler directives complying to the test format spec
from yapsy.IPlugin import IPlugin

from uatg.utils import paging_modes

class uatg_decompressor_floating_01(IPlugin):

    def __init__(self):
        super().__init__()
        self.isa = "RV64I"
        self.split_isa = "RV64I"
        self.modes = []

    def execute(self, core_yaml, isa_yaml):
        self.isa = isa_yaml['hart0']['ISA']
        # we split the ISA based on Z because, we are checking for
        # 'C' and 'F' standard extensions. When Zifencei or Zicsr are
        # enabled, the test using 'in' keyword will not return the expected
        # result.
        self.split_isa = self.isa.split('Z')
        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')

        if 'U' in self.isa:
            self.modes.append('user')

        if 'RV32' in self.isa:
            isa_string = 'rv32'
        else:
            isa_string = 'rv64'

        try:
            if isa_yaml['hart0']['satp'][f'{isa_string}']['accessible']:
                mode = isa_yaml['hart0']['satp'][f'{isa_string}']['mode'][
                    'type']['warl']['legal']
                self.satp_mode = mode[0]

        except KeyError:
            pass

        self.paging_modes = paging_modes(self.satp_mode, self.isa)

        if 'C' and 'F' in self.split_isa[0]:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This function will return all the compressed instructions"""

        for mode in self.modes:

            machine_exit_count = 0

            for paging_mode in self.paging_modes:

                if mode == 'machine':
                    if machine_exit_count > 0:
                        continue
                    machine_exit_count = machine_exit_count + 1

                asm = f"#define RVTEST_FP_ENABLE()\n" \
                      f"\tLI x2, MSTATUS_FS;\n" \
                      f"\tcsrrs x3, mstatus,x0;\n" \
                      f"\tor x2, x3, x2;\n" \
                      f"\tcsrrw x0,mstatus,x2;\n" \
                      f"\n\n\t## test: floating ##\n\n" \
                      f"\t###Integer Constant-Generation Instructions###\n" \
                      f"\t###Floating Point and Stack Pointer Based Load and " \
                      f"Store####\n\n\tLA (x2,sample_data)\n" \
                      f"\tc.fsdsp f8,8(x2)\n" \
                      f"\tc.fldsp f12,8(x2)\n" \
                      f"\t###Floating Point Load and Store####\n" \
                      f"\tLA (x10,sample_data)\n" \
                      f"\tc.fsd f11,8(x10)\n" \
                      f"\tLA (x12,sample_data)\n" \
                      f"\tc.fld f9,8(x12)\n" \

                # compile macros for the test
                if mode != 'machine':
                    compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test']
                else:
                    compile_macros = []

                # trap signature bytes
                trap_sigbytes = 24

                # initialize the signature region
                sig_code = 'mtrap_count:\n .fill 1, 8, 0x0\n' \
                           'mtrap_sigptr:\n' \
                           f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'

                asm_data = f'\n.align 3\n\n'\
                           f'exit_to_s_mode:\n.dword\t0x1\n\n'\
                           f'sample_data:\n.word\t0xbabecafe\n'\
                           f'.word\t0xdeadbeef\n\n'\
                           f'.align 3\n\nsatp_mode_val:\n.dword\t0x0\n\n'

                # user can choose to generate supervisor and/or user tests in
                # addition to machine mode tests here.
                privileged_test_enable = False

                if not privileged_test_enable:
                    self.modes.remove('supervisor')
                    self.modes.remove('user')

                privileged_test_dict = {
                    'enable': privileged_test_enable,
                    'mode': mode,
                    'page_size': 4096,
                    'paging_mode': paging_mode,
                    'll_pages': 64,
                }

                yield ({
                    'asm_code': asm,
                    'asm_sig': asm_sig,
                    'compile_macros': compile_macros,
                    'privileged_test': privileged_test_dict,
                    'docstring': 'This test fills ghr register with ones',
                    'name_postfix': f"{mode}-" + ('' if mode == 'machine' else paging_mode)
                })

    def generate_covergroups(self, config_file):
        """
           returns the covergroups for this test
        """
        config = config_file
        fn_decompress_inst = config['decompressor']['input'][
            'decompressor_input']
        sv = f"""covergroup floating_point_cg @(posedge CLK);\n
                option.per_instance=1;
///coverpoint for floating point instructions
floating_point_cp : coverpoint {fn_decompress_inst}"""
        sv += "{\n"
        sv += """  wildcard bins C_FLDSP 	= {16'b001_x_xxxxx_xxxxx_10};\n
  wildcard bins C_FSDSP	= {16'b101_xxxxxx_xxxxx_10};\n
  wildcard bins C_FLD	= {16'b001_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_FSD	= {16'b101_xxx_xxx_xx_xxx_00};\n
  }  
endgroup\n"""

        return sv
