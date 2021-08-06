# python program to generate an assembly file which fills the ghr with ones
# the ghr will have a zero entry when the loop exits
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os

class gshare_fa_ghr_ones_01(IPlugin):

    def __init__(self):
        self._history_len = 8

    def execute(self, _bpu_dict):
        _en_bpu = _bpu_dict['instantiate']
        self._history_len = _bpu_dict['history_len']

        if _en_bpu and self._history_len:
            return True
        else:
            return False

    def generate_asm(self):
        """
        The generated assembly file fills the ghr with ones
        """

        loop_count = self._history_len + 2  # here, 2 is added arbitrarily.
        # it makes sure the loop iterate 2 more times keeping the ghr filled
        # with ones for 2 more predictions

        asm = "\n  addi t0,x0," + str(
            loop_count) + "\n  addi t1,x0,0\n\nloop:\n"
        asm = asm + "  addi t1,t1,1\n  blt t1,t0,loop\n"

        return asm

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
                'expected_GHR_pattern': None,
                'executed_GHR_pattern': None,
                'Execution_Status': None
            }
        }

        train_existing_result = re.findall(rf.train_existing_pattern, log_file)
        test_report['gshare_fa_ghr_ones_01_report'][
            'expected_GHR_pattern'] = '1' * self._history_len
        res = None

        ghr_patterns = [i[-self._history_len:] for i in train_existing_result]
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

        f = open(os.path.join(reports_dir, 'gshare_fa_ghr_ones_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()

        return res
