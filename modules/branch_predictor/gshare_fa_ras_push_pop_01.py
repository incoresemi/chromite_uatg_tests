# python script to automate test 11 in micro-arch test

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os


class gshare_fa_ras_push_pop_01(IPlugin):

    def __init__(self):
        super().__init__()
        self.recurse_level = 5

    def execute(self, _bpu_dict):
        _en_ras = _bpu_dict['ras_depth']
        _en_bpu = _bpu_dict['instantiate']

        if _en_ras and _en_bpu:
            return True
        else:
            return False

    def generate_asm(self):
        """
        reg x30 is used as looping variable. reg x31 used as a temp variable
        """

        recurse_level = self.recurse_level
        no_ops = '\taddi x31, x0, 5\n\taddi x31, x0, -5\n'
        asm = '\taddi x30, x0, ' + str(recurse_level) + '\n'
        asm += '\tcall x1, lab1\n\tbeq  x30, x0, end\n'

        for i in range(1, recurse_level + 1):
            asm += 'lab' + str(i) + ':\n'
            if i == recurse_level:
                asm += '\taddi x30, x30, -1\n'
            else:
                asm += no_ops * 3 + '\tcall x' + str(i + 1) + ', lab' + str(
                    i + 1) + '\n'
            asm += no_ops * 3 + '\tret\n'
        asm += 'end:\n\tnop\n'
        return asm

    def check_log(self, log_file_path, reports_dir):
        """
        check for pushes and pops in this file. There should be 8 pushes and
        4 pops
        TODO: (should check why that happens, there should be 8pops)
        """

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        test_report = {
            "gshare_fa_ras_push_pop_01_report": {
                'Doc': "Return Address Stack should have pushed 8 times and "
                       "popped 4 times [presently hardcoded]",
                'expected_Push_count': 8,  # Hardcoded
                'expected_Pop_count': 4,  # Hardcoded
                'executed_Push_count': None,
                'executed_Pop_count': None,
                'Execution_Status': None
            }
        }

        pushing_to_ras_result = re.findall(rf.pushing_to_ras_pattern, log_file)
        choosing_top_ras_result = re.findall(rf.choosing_top_ras_pattern,
                                             log_file)
        res = None
        test_report["gshare_fa_ras_push_pop_01_report"][
            'executed_Push_count'] = len(pushing_to_ras_result)
        test_report["gshare_fa_ras_push_pop_01_report"][
            'executed_Pop_count'] = len(choosing_top_ras_result)

        if len(pushing_to_ras_result) != 8 or len(choosing_top_ras_result) != 4:
            res = False
            test_report["gshare_fa_ras_push_pop_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_ras_push_pop_01_report"][
                'Execution_Status'] = 'Pass'

        f = open(os.path.join(reports_dir, 'gshare_fa_ras_push_pop_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res
