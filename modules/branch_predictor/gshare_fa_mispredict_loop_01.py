# python program to generate an assembly file which checks if mis-predictions
# occur In addition to this, the GHR is also filled with ones (additional
# test case) uses assembly macros

# To-Do -> Create another function which prints the includes and other
# assembler directives complying to the test format spec

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from configparser import ConfigParser


class gshare_fa_mispredict_loop_01(IPlugin):

    def __init__(self):
        super().__init__()
        self._history_len = 8
        pass

    def execute(self, _bpu_dict):
        _history_len = _bpu_dict['history_len']
        _en_bpu = _bpu_dict['instantiate']

        if _en_bpu and _history_len:
            return True
        else:
            return False

    def generate_asm(self):
        """
        The program creates a simple loop in assembly which checks if
        mis-predictions occur during the warm-up phase of the BPU
        """

        loop_count = 4 * self._history_len  # the should iterate at least 2
        # times more than the actual ghr width for the BPU to predict
        # correctly at least once. We assume 2x arbitrarily
        asm = "\n  addi t0,x0," + str(
            loop_count) + "\n  addi t1,x0,0\n  addi t2,x0,2\n\nloop:\n"
        asm += "\taddi t1,t1,1\n" \
            + "\taddi t2,t2,10\n\tadd t2,t2,t2\n" \
            + "\taddi t2,t2,-10\n\taddi t2,t2,20\n"\
            + "\tadd t2,t2,t2\n\taddi t2,t2,-10\n"\
            + "\tblt t1,t0,loop\n\n"
        asm += "\tadd t2,t0,t1\n"

        return asm

    def check_log(self, log_file_path, reports_dir):
        """
          check if there is a mispredict atleast once after a BTBHit. 
        """
        test_report = {
            "gshare_fa_mispredict_loop_01_report": {
                'Doc': "Branch Predictor should have mispredicted at least "
                       "more than once.",
                'expected_mispredict_count': '> 1',
                'executed_mispredict_count': None,
                'Execution_Status': None
            }
        }

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        misprediction_result = re.findall(rf.misprediction_pattern, log_file)

        res = None
        test_report["gshare_fa_mispredict_loop_01_report"][
            'executed_mispredict_count'] = len(misprediction_result)
        if len(misprediction_result) <= 1:
            res = False
            test_report["gshare_fa_mispredict_loop_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_mispredict_loop_01_report"][
                'Execution_Status'] = 'Pass'

        f = open(
            os.path.join(reports_dir,
                         'gshare_fa_mispredict_loop_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res

    def generate_covergroups(self, config_file):
        """
        returns the covergroups for this test
        """
        config = ConfigParser()
        config.read(config_file)
        mispredict_flag = config['bpu']['bpu_mispredict_flag']
        sv = """covergroup gshare_fa_mispredict_loop_cg @(posedge CLK);
option.per_instance=1;
///Coverpoint : MSB of reg ma_mispredict_g should be 1 atleast once. When, the MSB is one, the MSB-1 bit of the register should be toggled.
{0}_cp : coverpoint {0}[""".format(mispredict_flag)
        sv = sv + str(self._history_len -
                      1) + """] {{\n    bins {0}_""".format(mispredict_flag)
        sv = sv + str(self._history_len - 1
                     ) + """_0to1 = (0=>1) iff ({0}[""".format(mispredict_flag)
        sv = sv + str(self._history_len) + """] == 1);\n    bins {0}_""".format(
            mispredict_flag)
        sv = sv + str(self._history_len - 1
                     ) + """_1to0 = (1=>0) iff ({0}[""".format(mispredict_flag)
        sv = sv + str(self._history_len) + """] == 1);\n}\nendgroup\n\n"""

        return (sv)
