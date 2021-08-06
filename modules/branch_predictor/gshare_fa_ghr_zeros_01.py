# This program generates a assembly code which fills the ghr with zeros
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from configparser import ConfigParser


class gshare_fa_ghr_zeros_01(IPlugin):

    def __init__(self):
        self._history_len = 8

    def execute(self, _bpu_dict):
        self._history_len = _bpu_dict['history_len']
        _en_bpu = _bpu_dict['instantiate']

        if _en_bpu and self._history_len:
            return True
        else:
            return False

    def generate_asm(self):
        """
          the for loop iterates ghr_width + 2 times printing an
          assembly program which contains ghr_width + 2 branches which
          will are *NOT TAKEN*. This fills the ghr with zeros
        """
        loop_count = self._history_len + 2
        asm = "\n\n## test: gshare_fa_ghr_zeros_01 ##\n\n"
        asm += "  addi t0,x0,1\n"

        for i in range(1, loop_count):
            asm = asm + "branch_" + str(i) + ":\n"
            asm = asm + "  beq t0,x0,branch_" + str(i) + "\n"
            asm = asm + "  addi t0,t0,1\n"

        return asm

    def check_log(self, log_file_path, reports_dir):
        """
          check if all the ghr values are zero throughout the test
        """
        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()
        test_report = {
            "gshare_fa_ghr_zeros_01_report": {
                'Doc': "ASM should have generated 00000... pattern in the GHR "
                       "Register. This report show's the "
                       "results",
                'expected_GHR_pattern': None,
                'executed_GHR_pattern': None,
                'Execution_Status': None
            }
        }
        test_report['gshare_fa_ghr_zeros_01_report'][
            'expected_GHR_pattern'] = '0' * self._history_len
        res = None
        alloc_newind_pattern_result = re.findall(rf.alloc_newind_pattern,
                                                 log_file)
        ghr_patterns = [
            i[-self._history_len:] for i in alloc_newind_pattern_result
        ]
        for i in ghr_patterns:
            if self._history_len * '0' in i:
                test_report['gshare_fa_ghr_zeros_01_report'][
                    'executed_GHR_pattern'] = i
                test_report['gshare_fa_ghr_zeros_01_report'][
                    'Execution_Status'] = 'Pass'
                res = True
                break
            else:
                res = False
        if not res:
            test_report['gshare_fa_ghr_zeros_01_report'][
                'executed_GHR_pattern'] = ghr_patterns
            test_report['gshare_fa_ghr_zeros_01_report'][
                'Execution_Status'] = 'Fail: expected pattern not found'

        f = open(
            os.path.join(reports_dir, 'gshare_fa_ghr_zeros_01_report.yaml'),
            'w')
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
        rg_ghr = config['bpu']['bpu_rg_ghr']

        sv = """covergroup bpu_rg_ghr_cg @(posedge CLK); 
option.per_instance=1;
///coverpoint label can be any name that relates the signal
coverpoint_label: coverpoint {0} {{\n""".format(rg_ghr)
        #sv = sv + "    bins cp1 = {" + str(self._history_len) + "{1'b0}};\n"
        #sv = sv + "    bins cp2 = {" + str(self._history_len) + "{1'b1}};\n"
        #sv = sv + "    bins cp3 = {" + str(int(
        #    self._history_len / 2)) + "{2'b01}};\n"
        #sv = sv + "    bins cp4 = {" + str(int(
        #    self._history_len / 2)) + "{2'b10}};\n}\nendgroup\n\n"

        sv = sv + "    bins bin_allzeros = {'b00000000};\n"
        sv = sv + "    bins bin_allones = {'b11111111};\n"
        sv = sv + "    bins bin_altr_10 = {'b10101010};\n"
        sv = sv + "    bins bin_altr_01 = {'b01010101};\n}\nendgroup\n\n"

        return (sv)
