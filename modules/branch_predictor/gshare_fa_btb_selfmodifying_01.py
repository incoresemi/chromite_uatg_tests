# Python program to generate the self modifying assembly test program

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os


class gshare_fa_btb_selfmodifying_01(IPlugin):

    def __init__(self):
        super().__init__()
        pass

    def execute(self, _bpu_dict):
        _en_bpu = _bpu_dict['instantiate']
        if _en_bpu:
            return True
        else:
            return False

    def generate_asm(self):
        """
          This method returns the asm file.
        """

        asm = ".option norvc\n\n"
        asm += "  addi t3,x0,0\n\taddi t4,x0,3\n\tjal x0,first\n\n"
        asm += "first:\n\taddi t3,t3,1\n\tbeq t3,t4,end\n\tjal x0,first" \
               + "\n\tjal x0,fin\n\n"
        asm += "end:\n\taddi x0,x0,0\n\taddi t0,x0,1\n\tslli t0,t0,31" \
               + "\n\taddi t0,t0,0x3a4\n"
        asm += "\taddi t1,x0,0x33\n\taddi t3,x0,4\n\tsw t1,0(t0)\n\t" \
               + "fence.i\n\tjal x0,first\n\n"
        asm = asm + "fin:\n"

        return asm

    def check_log(self, log_file_path, reports_dir):
        """
          check if fence is executed properly. 
          The BTBTags should be invalidated and the rg_allocate should return 0
        """
        test_report = {
            "gshare_fa_btb_selfmodifying_01_report": {
                'Doc': "ASM should have executed FENCE instructions at least "
                       "more than once.",
                # TODO: is it to be hardcoded @ Alen?
                'expected_Fence_count': 'presently hard_coded to 2',
                'executed_Fence_count': None,
                'Execution_Status': None
            }
        }

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        fence_executed_result = re.findall(rf.fence_executed_pattern, log_file)
        ct = len(fence_executed_result)
        res = None
        test_report["gshare_fa_btb_selfmodifying_01_report"][
            'executed_Fence_count'] = ct
        if ct <= 1:
            # check for execution of more than one fence inst
            res = False
            test_report["gshare_fa_btb_selfmodifying_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_btb_selfmodifying_01_report"][
                'Execution_Status'] = 'Pass'
        f = open(os.path.join(reports_dir, 'gshare_fa_btb_selfmodifying_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res
