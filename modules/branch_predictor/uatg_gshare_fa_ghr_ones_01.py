# python program to generate an assembly file which fills the ghr with ones
# the ghr will have a zero entry when the loop exits
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from uatg.utils import paging_modes
import re
import os
from typing import Dict, Union, Any, List


class uatg_gshare_fa_ghr_ones_01(IPlugin):
    """
    This class contains methods to
    1. generate asm tests that fills global history register with ones
    2. checks the log file whether the history register has been filled with 1's
       at least once.

    NOTE: The SV covergroup for this test is written in
          utg_gshare_fa_ghr_zeros_01.py
    """

    def __init__(self):
        # initializing variables
        super().__init__()
        self._history_len = 8
        self.modes = []
        self.isa = 'RV32I'
        self.isa = 'RV64I'

    def execute(self, core_yaml, isa_yaml):
        # Function to check whether to generate/validate this test or not

        # extract needed values from bpu's parameters
        _bpu_dict = core_yaml['branch_predictor']
        _en_bpu = _bpu_dict['instantiate']
        self._history_len = _bpu_dict['history_len']
        self.isa = isa_yaml['hart0']['ISA']
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

        if _en_bpu and self._history_len:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
          the for loop iterates ghr_width + 2 times printing an
          assembly program which contains ghr_width + 2 branches which
          will are TAKEN. This fills the ghr with ones
        """

        for mode in self.modes:

            machine_exit_count = 0

            for paging_mode in self.paging_modes:

                if mode == 'machine':
                    if machine_exit_count > 0:
                        continue
                    machine_exit_count = machine_exit_count + 1

                loop_count = self._history_len + 2  # here, 2 is added arbitrarily.
                # it makes sure the loop iterate 2 more times keeping the ghr filled
                # with ones for 2 more predictions

                asm = f"\n\taddi t0, x0, {loop_count}\n\taddi t1, x0, 0 \n\nloop:\n"
                asm += "\taddi t1, t1, 1\n\tblt t1, t0, loop\n\tc.nop\n"

                # trap signature bytes
                trap_sigbytes = 24

                # initialize the signature region
                sig_code = 'mtrap_count:\n .fill 1, 8, 0x0\n' \
                           'mtrap_sigptr:\n' \
                           f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'
                
                # compile macros for the test
                if mode != 'machine':
                    compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test']
                else:
                    compile_macros = []

                asm_data = f'\n.align 3\n\n'\
                           f'exit_to_s_mode:\n.dword\t0x1\n\n'\
                           f'sample_data:\n.word\t0xbabecafe\n'\
                           f'.word\t0xdeadbeef\n\n'\
                           f'.align 3\n\nsatp_mode_val:\n.dword\t0x0\n\n'

                # user can choose to generate supervisor and/or user tests in
                # addition to machine mode tests here.
                privileged_test_enable = True

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
                    'asm_sig': sig_code,
                    'asm_data': asm_data,
                    'compile_macros': compile_macros,
                    'privileged_test': privileged_test_dict,
                    'docstring': 'This test fills ghr register with ones',
                    'name_postfix': f"{mode}-" + ('' if mode == 'machine' else paging_mode)
                })

    def check_log(self, log_file_path, reports_dir):
        """
          check if all the ghr values are fully ones at least once during the
          test
        """

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        test_report = {
            "gshare_fa_ghr_ones_01_report": {
                'Doc': "ASM should have generated 11111... pattern in the GHR "
                       "Register. This report show's the "
                       "results",
                'expected_GHR_pattern': '',
                'executed_GHR_pattern': [],
                'Execution_Status': ''
            }
        }

        # Finding the occurrence of ghr training
        train_existing_result = re.findall(rf.train_existing_pattern, log_file)
        test_report['gshare_fa_ghr_ones_01_report'][
            'expected_GHR_pattern'] = '1' * self._history_len
        res = None
        ghr_patterns = [i[-self._history_len:] for i in train_existing_result]

        # Checking if the required pattern is filled in ghr and deciding status
        for i in ghr_patterns:
            if self._history_len * "1" in i:
                test_report['gshare_fa_ghr_ones_01_report'][
                    'executed_GHR_pattern'] = i
                test_report['gshare_fa_ghr_ones_01_report'][
                    'Execution_Status'] = 'Pass'
                res = True
                break
            else:
                res = False
        if not res:
            test_report['gshare_fa_ghr_ones_01_report'][
                'executed_GHR_pattern'] = ghr_patterns
            test_report['gshare_fa_ghr_ones_01_report'][
                'Execution_Status'] = 'Fail: expected pattern not found'

        # storing test report at corresponding location
        f = open(os.path.join(reports_dir, 'gshare_fa_ghr_ones_01_report.yaml'),
                 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()

        return res
