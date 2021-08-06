# python script to automate test 11 in micro-arch test
# ghr repeating pattern 010101010....
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os


class gshare_fa_ghr_alternating_01(IPlugin):

    def __init__(self):
        super().__init__()
        # self.btb_depth = 32
        # self._history_len = 8
        # self.overflow_times = 0
        # self.btb_depth = 32
        self._history_len = 8
        pass

    def execute(self, _bpu_dict):
        _en_bpu = _bpu_dict['instantiate']
        self._history_len = _bpu_dict['history_len']

        if _en_bpu and self._history_len:
            return True
        else:
            return False

    def generate_asm(self):
        """
        This function creates assembly code to populate the Global History
        register with alternating 0's and 1's pattern. eg. 010101010....
        history_len = the size of the Global History Register (ghr) in bits.
                      By default history_len is set to be 8 bits.
        The generated assembly code will use the t0 register to alternatively
        enter and exit branches.
        """

        asm = ".option norvc\n"
        asm = asm + '\taddi t0,x0,1\n'
        asm = asm + '\taddi t1,x0,1\n\taddi t2,x0,2\n\n'
        asm = asm + '\tbeq  t0,x0,lab0\n'

        if self._history_len % 2:
            self._history_len = self._history_len + 1
        # the assembly program is structured in a way that
        # there are odd number of labels.

        for i in range(self._history_len):
            if i % 2:
                asm = asm + 'lab' + str(i) + ':\n'
                asm = asm + '\taddi t0,t0,1\n'
                asm = asm + '\tbeq  t0,x0,lab' + str(i + 1) + '\n'
            else:
                asm = asm + 'lab' + str(i) + ':\n'
                asm = asm + '\taddi t0,t0,-1\n'
                asm = asm + '\tbeq  t0,x0,lab' + str(i + 1) + '\t\n'
        asm = asm + 'lab' + str(self._history_len) + ':\n'
        asm = asm + '\taddi t0,t0,-1\n\n'
        asm = asm + '\taddi t1,t1,-1\n\taddi t2,t2,-1\n'
        asm = asm + '\tbeq  t1,x0,lab0\n\taddi t0,t0,2\n'
        asm = asm + '\tbeq  t2,x0,lab0\n'
        return asm

    def check_log(self, log_file_path, reports_dir):
        """
          check if the ghr value is alternating. 
          it should be 01010101 or 10101010 before being fenced 
        """

        test_report = {
            "gshare_fa_ghr_alternating_01_report": {
                'Doc': "ASM should have generated either 010101... or 101010..."
                       "pattern in the GHR Register. This report show's the "
                       "results",
                'expected_GHR_pattern': None,
                'executed_GHR_pattern': None,
                'Execution_Status': None
            }
        }

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        a = None
        b = None
        if self._history_len % 2:
            a = "01" * (self._history_len // 2) + '0'
            b = "10" * (self._history_len // 2) + '1'
        else:
            a = "01" * (self._history_len // 2)
            b = "10" * (self._history_len // 2)

        train_existing_result = re.findall(rf.train_existing_pattern, log_file)
        test_report['gshare_fa_ghr_alternating_01_report'][
            'expected_GHR_pattern'] = '{0} or {1}'.format(a, b)
        res = None
        ghr_patterns = [i[-self._history_len:] for i in train_existing_result]
        for i in ghr_patterns:
            if a in i or b in i:
                test_report['gshare_fa_ghr_alternating_01_report'][
                    'executed_GHR_pattern'] = i
                test_report['gshare_fa_ghr_alternating_01_report'][
                    'Execution_Status'] = 'Pass'
                res = True
                break
            else:
                res = False

        if not res:
            test_report['gshare_fa_ghr_alternating_01_report'][
                'executed_GHR_pattern'] = ghr_patterns
            test_report['gshare_fa_ghr_alternating_01_report'][
                'Execution_Status'] = 'Fail: expected pattern not found'

        f = open(os.path.join(reports_dir, 'gshare_fa_ghr_alternating_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()

        return res
