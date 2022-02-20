# python script to automate test 11 in micro-arch test

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
import re
import os
from typing import Dict, Union, Any, List


class uatg_gshare_fa_ras_push_pop_01(IPlugin):
    """
    This class contains methods to
    1. generate asm tests that pushes & pops addresses in return address stack
    2. checks the log file for correct number of push-pops
    TODO 3. generate_sv
    """

    def __init__(self):
        # initializing variables
        super().__init__()
        self.recurse_level = 5

    def execute(self, core_yaml, isa_yaml) -> bool:
        # Function to check whether to generate/validate this test or not

        # extract needed values from bpu's parameters
        _bpu_dict = core_yaml['branch_predictor']
        _en_ras = _bpu_dict['ras_depth']
        _en_bpu = _bpu_dict['instantiate']

        self.isa = isa_yaml['hart0']['ISA']
        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')

        if 'S' in self.isa and 'U' in self.isa:
            self.modes.append('user')

        # conditions to check if this test needs to be implemented or not
        if _en_ras and _en_bpu:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:

        return_list = []

        for mode in self.modes:

            # reg x30 is used as looping variable. reg x31 used as a temp variable

            recurse_level = self.recurse_level
            # number of times call-ret instructions to be implemented in assembly
            no_ops = '\taddi x31, x0, 5\n\taddi x31, x0, -5\n'
            asm = f'\taddi x30, x0, {recurse_level}\n'
            # going into the first call
            asm += '\tcall x1, lab1\n\tbeq x30, x0, end\n'
            # recursively going into calls
            for i in range(1, recurse_level + 1):
                asm += f'lab{i} :\n'
                if i == recurse_level:
                    asm += '\taddi x30, x30, -1\n'
                else:
                    asm += no_ops * 3 + f'\tcall x{i+1}, lab{i+1}\n'
                asm += no_ops * 3 + '\tret\n'
                # getting out recursively using rets
            asm += 'end:\n\tnop\n'

            # trap signature bytes
            trap_sigbytes = 24
            trap_count = 0

            # initialize the signature region
            sig_code = 'mtrap_count:\n'
            sig_code += ' .fill 1, 8, 0x0\n'
            sig_code += 'mtrap_sigptr:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                int(trap_sigbytes / 4))
            # compile macros for the test
            if mode != 'machine':
                compile_macros = ['rvtest_mtrap_routine','s_u_mode_test']
            else:
                compile_macros = []

            # user can choose to generate supervisor and/or user tests in addition
            # to machine mode tests here.
            privileged_test_enable = True

            privileged_test_dict = {
                'enable': privileged_test_enable,
                'mode': mode,
                'page_size': 4096,
                'paging_mode': 'sv39',
                'll_pages': 64,
            }

            return_list.append({
                'asm_code': asm,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'privileged_test': privileged_test_dict,
                'docstring': 'This test fills ghr register with ones',
                'name_postfix': mode
            })

            if not privileged_test_enable:
                return return_list

        return return_list

    def check_log(self, log_file_path, reports_dir) -> bool:
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
                'executed_Push_count': 0,
                'executed_Pop_count': 0,
                'Execution_Status': ''
            }
        }
        # finding the occurrences of pushing events in log
        pushing_to_ras_result = re.findall(rf.pushing_to_ras_pattern, log_file)
        # finding the occurrences of popping events in log
        choosing_top_ras_result = re.findall(rf.choosing_top_ras_pattern,
                                             log_file)
        # getting the number of occurrences
        test_report["gshare_fa_ras_push_pop_01_report"][
            'executed_Push_count'] = len(pushing_to_ras_result)
        test_report["gshare_fa_ras_push_pop_01_report"][
            'executed_Pop_count'] = len(choosing_top_ras_result)

        # Defining the pass/fail status of the test based on no. of push-pops
        if len(pushing_to_ras_result) != 8 or len(choosing_top_ras_result) != 4:
            res = False
            test_report["gshare_fa_ras_push_pop_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_ras_push_pop_01_report"][
                'Execution_Status'] = 'Pass'
        # storing the reports into a corresponding file
        f = open(
            os.path.join(reports_dir, 'gshare_fa_ras_push_pop_01_report.yaml'),
            'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res
