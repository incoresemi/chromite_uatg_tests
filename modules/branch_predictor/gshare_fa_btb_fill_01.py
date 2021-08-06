# This module has a function which generates assembly program to fill the
# BTB with entries # there are 33 control insts in the generated program,
# 1 jump from the includes and 32  in the program

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from configparser import ConfigParser


class gshare_fa_btb_fill_01(IPlugin):

    def __init__(self):
        super().__init__()
        self._btb_depth = 32
        self.test_created = False

    def execute(self, _bpu_dict):
        _en_bpu = _bpu_dict['instantiate']
        self._btb_depth = _bpu_dict['btb_depth']
        if _en_bpu and self._btb_depth:
            return True
        else:
            return False

    def generate_asm(self):
        """
          it is assumed that the btb_depth will be a multiple of 4 at all times"
        """

        asm_start = "\taddi t1,x0,0\n\taddi t2,x0,1\n\n"
        branch_count = int(self._btb_depth / 4)
        asm_branch = ""
        asm_jump = "\tadd t1,t1,t2\n\tjal x0,entry_" + str(branch_count +
                                                           1) + "\n\n"
        asm_call = "entry_" + str((2 * branch_count) + 1) + ":\n\n"
        asm_end = "exit:\n\n\taddi x0,x0,0\n\tadd x0,x0,0\n\n"
        for j in range((2 * branch_count) + 2, ((3 * branch_count) + 1)):
            asm_call += "\tcall x1,entry_" + str(j) + "\n"
        asm_call += "\tj exit\n\n"
        for i in range(1, self._btb_depth):
            if i <= branch_count:
                if (i % 2) == 1:
                    asm_branch += "entry_" + str(i) + ":\n"
                    asm_branch += "\tadd t1,t1,t2\n\tbeq t1,t2," \
                                  "entry_" + str(i) + "\n\n"
                else:
                    asm_branch += "entry_" + str(i) + ":\n"
                    asm_branch += "\tsub t1,t1,t2\n\tbeq t1,t2," \
                                  "entry_" + str(i) + "\n\n"
            elif branch_count < i <= 2 * branch_count:
                if (i % 2) == 1:
                    asm_jump += "entry_" + str(i) + ":\n"
                    asm_jump += "\tsub t1,t1,t2\n\tjal x0,entry_" + \
                                str(i + 1) + "\n\taddi x0,x0,0\n\n"
                else:
                    asm_jump += "entry_" + str(i) + ":\n"
                    asm_jump += "\tadd t1,t1,t2\n\tjal x0,entry_" + \
                                str(i + 1) + "\n\taddi x0,x0,0\n\n"

            else:
                if i >= 3 * branch_count:
                    break
                asm_call = asm_call + "entry_" + str(i + 1) + ":\n"
                for j in range(2):
                    asm_call = asm_call + "\taddi x0,x0,0\n"
                asm_call = asm_call + "\tret\n\n"

        asm = asm_start + asm_branch + asm_jump + asm_call + asm_end
        return asm

    def check_log(self, log_file_path, reports_dir):
        """
        check if the rg_allocate register value starts at 0 and traverses
        till 31. This makes sure that the BTB was successfully filled. Also
        check if all the 4 Control instructions are encountered at least once
        This can be checked from the training data -> [      5610] [ 0]BPU :
        Received Training: Training_data........
        """

        f = open(log_file_path, "r")
        log_file = f.read()
        f.close()

        alloc_newind_result = re.findall(rf.alloc_newind_pattern, log_file)
        new_arr = []
        for i in range(len(alloc_newind_result)):
            new_arr.append(alloc_newind_result[i][23:])
        # selecting the pattern "Allocating new index: dd ghr: dddddddd"
        # sorting them and removing duplicates

        new_arr = list(set(new_arr))
        new_arr.sort()
        test_report = {
            "gshare_fa_btb_fill_01_report": {
                'Doc': "ASM should have filled {0} BTB entries. This report "
                       "verifies that.".format(self._btb_depth),
                'BTB_Depth': self._btb_depth,
                'No_filled': None,
                'Execution_Status': None
            }
        }
        ct = 0
        res = None
        
        for i in range(self._btb_depth):
            try:
                if str(i) not in new_arr[i]:
                    pass     
                else:
                    ct += 1
            except IndexError as err:
                pass

        test_report["gshare_fa_btb_fill_01_report"]['No_filled'] = ct

        if ct == self._btb_depth:
            test_report["gshare_fa_btb_fill_01_report"][
                'Execution_Status'] = 'Pass'
            res = True
        else:
            test_report["gshare_fa_btb_fill_01_report"][
                'Execution_Status'] = 'Fail'
            res = False

        f = open(os.path.join(reports_dir, 'gshare_fa_btb_fill_01_report.yaml'),
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
        rg_initialize = config['bpu']['bpu_rg_initialize']
        rg_allocate = config['bpu']['bpu_rg_allocate']
        btb_entry = config['bpu']['bpu_btb_entry']
        sv = (
            "covergroup gshare_fa_btb_fill_cg @(posedge CLK);\n"
            "option.per_instance=1;\n"
            "///Coverpoint : reg rg_allocate should change from 0 to `btb_depth -1\n"
        )
        sv = sv + "{0}_cp : coverpoint rg_{0}[4:0] {{\n".format(rg_allocate)
        sv = sv + "    bins {0}_bin[32] = {{[0:31]}} iff ({1} == 0);\n}}\n".format(
            rg_allocate, rg_initialize)
        sv = sv + "///Coverpoints to check the bits 2 and 3 of the v_reg_btb_entry_XX should contain 01,00,10 and 11 (across the 32 entries)\n"

        for i in range(self._btb_depth):
            sv = sv + str(btb_entry) + "_" + str(i) + "_cp: coverpoint " + str(
                btb_entry) + "_"
            sv = sv + str(i) + "[3:2]{\n    bins " + str(btb_entry) + "_" + str(
                i) + "_bin = {'d0,'d1,'d2,'d3} iff (" + str(
                    rg_initialize) + " == 0);\n}\n"

        sv = sv + "endgroup\n\n"
        return (sv)
