from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
import re
import os
from typing import Dict, Union, Any, List


class uatg_gshare_fa_mispredict_loop_01(IPlugin):
    """
    Class with methods to generate an assembly which checks if mis-predictions
    occur. Also, the GHR is also filled with ones (additional test case)
    uses assembly macros

    TODO:
    1. Create another function which prints the includes and other
    assembler directives complying to the test format spec,
    2. Document generate_covergroups
    """

    def __init__(self):
        # initializing variables
        super().__init__()
        self.modes = []
        self.isa = 'RV32I'
        self._history_len = 8
        pass

    def execute(self, core_yaml, isa_yaml) -> bool:
        # Function to check whether to generate/validate this test or not

        # extract needed values from bpu parameters
        _bpu_dict = core_yaml['branch_predictor']
        _history_len = _bpu_dict['history_len']
        _en_bpu = _bpu_dict['instantiate']

        self.isa = isa_yaml['hart0']['ISA']
        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')

        if 'S' in self.isa and 'U' in self.isa:
            self.modes.append('user')

        if _en_bpu and _history_len:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        The function creates a simple loop in assembly which checks if
        mis-predictions occur during the warm-up phase of the BPU
        """

        for mode in self.modes:

            loop_count = 4 * self._history_len
            # the should iterate at least 2
            # times more than the actual ghr width for the BPU to predict
            # correctly at least once. We assume 2x arbitrarily
            asm = f"\n\taddi t0, x0, {loop_count}\n" \
                  f"\taddi t1,x0,0\n\taddi t2,x0,2\n\n" \
                  f"loop:\n\taddi t1,t1,1\n" \
                  f"\taddi t2,t2,10\n\tadd t2,t2,t2\n" \
                  f"\taddi t2,t2,-10\n\taddi t2,t2,20\n" \
                  f"\tadd t2,t2,t2\n\taddi t2,t2,-10\n" \
                  f"\tblt t1,t0,loop\n\n" \
                  f"\tadd t2,t0,t1\n"
            # trap signature bytes
            trap_sigbytes = 24

            # initialize the signature region
            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\nmtrap_sigptr:\n' \
                       f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'

            # compile macros for the test
            if mode != 'machine':
                compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test']
            else:
                compile_macros = []

            # user can choose to generate supervisor and/or user tests in
            # addition to machine mode tests here.
            privileged_test_enable = True

            if not privileged_test_enable:
                self.modes.remove('supervisor')
                self.modes.remove('user')

            asm_data = f'sample_data:\n.word\t0xbabecafe\n\n'\
                       f'exit_to_s_mode:\n.dword\t0x1\n\n'

            privileged_test_dict = {
                'enable': privileged_test_enable,
                'mode': mode,
                'page_size': 4096,
                'paging_mode': 'sv39',
                'll_pages': 64,
            }

            yield ({
                'asm_code': asm,
                'asm_sig': sig_code,
                'asm_data': asm_data,
                'compile_macros': compile_macros,
                'privileged_test': privileged_test_dict,
                'docstring': '',
                'name_postfix': mode
            })

    def check_log(self, log_file_path, reports_dir) -> bool:
        """
          check if there is a mispredict atleast once after a BTBHit.
        """
        test_report = {
            "gshare_fa_mispredict_loop_01_report": {
                'Doc': "Branch Predictor should have mispredicted at least "
                       "more than once.",
                'expected_mispredict_count': '> 1',
                'executed_mispredict_count': 0,
                'Execution_Status': ''
            }
        }

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        # Finding the occurrences of misprediction in the log
        misprediction_result = re.findall(rf.misprediction_pattern, log_file)

        # Counting the number of mispredictions
        test_report["gshare_fa_mispredict_loop_01_report"][
            'executed_mispredict_count'] = len(misprediction_result)

        # Deciding the status of the test based on the no. of occurrences
        if len(misprediction_result) <= 1:
            res = False
            test_report["gshare_fa_mispredict_loop_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_mispredict_loop_01_report"][
                'Execution_Status'] = 'Pass'
        # storing the reports into a corresponding file
        f = open(
            os.path.join(reports_dir,
                         'gshare_fa_mispredict_loop_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res

    def generate_covergroups(self, config_file) -> str:
        """
        returns the covergroups for this test
        """
        config = config_file
        mispredict_flag = config['branch_predictor']['wire'][
            'bpu_mispredict_flag']
        sv = "covergroup gshare_fa_mispredict_loop_cg @(posedge " \
             "CLK);\noption.per_instance=1;\n///Coverpoint : MSB of reg " \
             "ma_mispredict_g should be 1 atleast once. When, the MSB is one," \
             " the MSB-1 bit of the register should be toggled.{0}_cp : " \
             f"coverpoint {mispredict_flag}["
        sv += f"{self._history_len - 1}] {{\n\tbins {mispredict_flag}_" \
              f"{self._history_len - 1}_0to1 = (0=>1) iff ({mispredict_flag}[" \
              f"{self._history_len}] == 1);\n\tbins {mispredict_flag}_" \
              f"{self._history_len - 1}_1to0 = (1=>0) iff (" \
              f"{mispredict_flag}[{self._history_len}] == 1);\n" \
              "}\nendgroup\n\n"
        return sv
