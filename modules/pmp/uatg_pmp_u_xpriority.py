#    Copyright (c) 2022 Incore Semiconductors Pvt. Ltd. All Rights Reserved. See LICENSE.incore for more details.
#    Created On:  Wed Aug 24, 2022 12:50:58
#    Author(s):
#    - S Pawan Kumar <pawan.kumar@incoresemi.com> gitlab: @pawks github: @pawks

import random,sys,math
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin
import pathlib
import importlib
thisdir = pathlib.Path(__file__).parent.resolve()
sys.path.append(str(thisdir))
helpers = importlib.import_module("pmp_helpers")

from uatg.log import logger as log

class uatg_pmp_u_xpriority(IPlugin):

    def __init__(self):
        super().__init__()

    def execute(self,core_yaml,isa_yaml) -> bool:
        log.debug("Checking PMP configuration.")
        self.rsize = max(2 ** (isa_yaml['hart0']['pmp_granularity']+2), 8)
        self.isa_yaml = isa_yaml
        return helpers.is_pmp_present(isa_yaml)

    def generate_asm(self) -> Dict[str, Union[Union[str, list], Any]]:

        align = int(math.log(self.rsize, 2))

        asm_data = f"\n\n.align 3\n"\
                f"return_address:\n"\
                f".dword 0x0\n\n"\
                f"access_fault:\n.dword 0\n"
                f"faulty_page_address:\n"\
                f".dword 0x0\n"\
                f'\n.align 3\n\n'\
                f'exit_to_s_mode:\n.dword\t0x1\n\n'\
                f'sample_data:\n.word\t0xbabecafe\n'\
                f'.word\t0xdeadbeef\n\n'\
                f'.align 3\n\nsatp_mode_val:\n.dword\t0x0\n\n'\
                f"\n.align {align}\nrvtest_data:\n"+(''.join([".word 0xbabecafe\n"]*int(self.rsize/4)))
        log.debug("Generating Test")
        xlen = helpers.get_xlen(self.isa_yaml)
        pmps = helpers.get_valid_pmp_entries(self.isa_yaml)
        asm = "li t0, 0;\n csrw satp, t0;\n"
        for i in pmps[:-1]:
            asm += helpers.reset_pmp(i,'t0',xlen)
        asm += helpers.config_pmp(max(pmps),'t0', 's0','li t0,0x2FFFFFFF',
                    helpers.cfg(True, True,True, False, helpers.mode_napot),xlen,False)
        compile_macros = ['rvtest_mtrap_routine','s_u_mode_test','access_fault_test']
        exemode='m' + ('s' if 'S' in self.isa_yaml['hart0']['ISA'] else '')
        sinst = 'sw' if xlen == 32 else 'sd'
        inc = int(xlen/8)
        for entry in pmps[:-1]:
            modes = helpers.get_legal_modes(self.isa_yaml, entry)
            for mode in filter(lambda x: x!= 0, modes):
                label = 'pmp_target'
                test_asm = f'j start_test;\n.align {align}\npmp_target: \nj 1f;\n.align {align}\n'\
                        f'{sinst} t2, 0(t1);\njalr x0, ra;\nstart_test:\n'
                test_asm += f'la t1, exit_to_s_mode;\n sw x0, 0(t1);'
                test_asm += f'la t1, sig;\n li t2, 0;\n la t3, access_fault;\n'
                test_asm += helpers.config_pmp(entry, 't0', 's0',
                        helpers.get_addr_seq(mode,self.rsize,'t0','s0',
                            label),
                        helpers.cfg(False, False, False, False, mode), xlen , True)
                if mode == 1 and entry != 0:
                    test_asm += helpers.config_pmp(entry-1, 't0', 's0',
                        helpers.get_addr_seq(0,0,'t0','s0',
                        label),
                        0, xlen, True)
                test_asm += 'li t3, 0;\naddi t6, x0, 0;\nslli t6, t6, 11;\n'\
                        'csrs CSR_MSTATUS, t6;\n la t5, user_entry;\n'\
                        'csrw CSR_MEPC, t5;\n mret;\n user_entry:\n'\
                        f'la t4, recovery_u;\n{sinst} t4, 0(t3);\n'\
                        f'li a0, 173;\nla t4, pmp_target;\n{sinst} t4, 0(t3);\n jalr ra, t4;\n'\
                        f'recovery_u:\naddi t1, t1,{inc};\necall;\ntest_exit:\n'
                trap_sigbytes = 24
                sig_code = f'sig:\n .fill 3*{xlen//32},4,0xdeadbeef\n'+\
                        ' mtrap_count:\n .fill 1, 8, 0x0\n' \
                       'mtrap_sigptr:\n' \
                       f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'
                yield ({
                    'asm_code': asm+test_asm+'\ntest_exit:\n',
                    'asm_data': asm_data,
                    'asm_sig': sig_code,
                    'compile_macros': compile_macros,
                    'name_postfix': f"{exemode}-{entry}-{mode}-{inst}"
                })

    def check_log(self, log_file_path, reports_dir):
        """

        """

    def generate_covergroups(self, config_file):
        """

        """