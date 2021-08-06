# This program fences the CPU and checks if the BTB entries are invalidated.

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from configparser import ConfigParser


class gshare_fa_fence_01(IPlugin):
    """
    This program generates an assembly program which fences the CPU and
    checks if the BTB entries are invalidated
    """

    def __init__(self):
        super().__init__()
        self.recurse_level = 5
        self._btb_depth = 32
    def execute(self, _bpu_dict):
        self._btb_depth = _bpu_dict['btb_depth']
        _en_bpu = _bpu_dict['instantiate']
        # TODO why  recursing in the asm test?
        if self._btb_depth and _en_bpu:
            return True
        else:
            return False

    def generate_asm(self):
        """
        This code is derived from the ras_push_pop code. Fence instructions are
        introduced.reg x30 is used as looping variable. reg x31 used as
        a temp variable
        """
        recurse_level = self.recurse_level
        no_ops = "\taddi x31,x0,5\n  addi x31,x0,-5\n"
        asm = "\taddi x30,x0," + str(recurse_level) + "\n"
        asm = asm + "\tcall x1,lab1\n\tbeq x30,x0,end\n\tfence.i\n"

        for i in range(1, recurse_level + 1):
            asm += "lab" + str(i) + ":\n"
            if i == recurse_level:
                asm += "\tfence.i\n\taddi x30,x30,-1\n"
            else:
                asm = asm + no_ops * 3 + "  call x" + str(
                    i + 1) + ", lab" + str(i + 1) + "\n"
            asm = asm + no_ops * 3 + "\tret\n"
        asm = asm + "end:\n\tnop\n"

        return asm

    def check_log(self, log_file_path, reports_dir):
        """
        check if rg_allocate becomes zero after encountering fence.
        also check if the valid bits become zero
        and if the ghr becomes zero
        """
        test_report = {
            "gshare_fa_fence_01_report": {
                'Doc': "ASM should have executed FENCE instructions at least "
                       "more than once.",
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
        test_report["gshare_fa_fence_01_report"]['executed_Fence_count'] = ct
        if ct <= 1:
            # check for execution of more than one fence inst
            res = False
            test_report["gshare_fa_fence_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True
            test_report["gshare_fa_fence_01_report"][
                'Execution_Status'] = 'Pass'
        f = open(os.path.join(reports_dir, 'gshare_fa_fence_01_report.yaml'),
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
        #ini_file = /Projects/incorecpu/jyothi.g/micro-arch-tests/example.ini
        config = ConfigParser()
        config.read(config_file)
        #test = config['test']['test_name']
        rg_initialize = config['bpu']['bpu_rg_initialize']
        rg_allocate = config['bpu']['bpu_rg_allocate']
        btb_tag = config['bpu']['bpu_btb_tag']
        btb_tag_valid = config['bpu']['bpu_btb_tag_valid']
        ras_top_index = config['bpu']['bpu_ras_top_index']
        rg_ghr = config['bpu']['bpu_rg_ghr']

        sv = ("covergroup  gshare_fa_fence_cg @(posedge CLK);\n"
              "option.per_instance=1;\n"
              "///coverpoint -rg_initialize should toggle from 0->1\n")
        sv = sv + str(rg_initialize) + "_cp : coverpoint " + str(
            rg_initialize) + " {\n   bins " + str(
                rg_initialize) + "_0to1 = (0=>1);\n}\n"
        sv = sv + "///Coverpoint to check the LSB of v_reg_btb_tax_00 is valid\n{0}_cp: coverpoint {0} {{\n    bins valid = {{".format(
            btb_tag_valid)
        sv = sv + str(
            self._btb_depth
        ) + "\'b11111111_11111111_11111111_11111111};\n}\n///coverpoint -  rg_initilaize toggles friom 1->0 2. rg_allocate should become zero 3. v_reg_btb_tag_XX should become 0 (the entire 63bit reg) 4. rg_ghr_port1__read should become zeros. 5. ras_stack_top_index_port2__read should become 0\n"
        for i in range(self._btb_depth):
            sv = sv + str(rg_initialize) + "_" + str(i) + ": coverpoint " + str(
                rg_initialize) + "{\n    bins " + str(rg_initialize) + "_"
            sv = sv + str(i) + "1to0 = (1=>0) iff (" + str(
                rg_allocate) + " == 'b0 && " + str(btb_tag) + "_"
            sv = sv + str(i) + " == 'b0 && " + str(
                ras_top_index) + "== 'b0 && " + str(rg_ghr) + "== 'b0);\n}\n"
        sv = sv + "endgroup\n\n"
        sv = sv + """property rg_initialize_prop;

@(negedge CLK) ($fell(rg_initialize)) |=> (rg_allocate == 'b0 && v_reg_btb_tag_0 == 'b0 && v_reg_btb_tag_1 == 'b0 && v_reg_btb_tag_2 == 'b0 && v_reg_btb_tag_3 == 'b0 && v_reg_btb_tag_4 == 'b0 && v_reg_btb_tag_5 == 'b0 && v_reg_btb_tag_6 == 'b0 && v_reg_btb_tag_7 == 'b0 && v_reg_btb_tag_8 == 'b0 && v_reg_btb_tag_9 == 'b0 && v_reg_btb_tag_10 == 'b0 && v_reg_btb_tag_11 == 'b0 && v_reg_btb_tag_12 == 'b0 && v_reg_btb_tag_13 == 'b0 && v_reg_btb_tag_14 == 'b0 && v_reg_btb_tag_15 == 'b0 && v_reg_btb_tag_16 == 'b0 && v_reg_btb_tag_17 == 'b0 && v_reg_btb_tag_18 == 'b0 && v_reg_btb_tag_19 == 'b0 && v_reg_btb_tag_20 == 'b0 && v_reg_btb_tag_21 == 'b0 && v_reg_btb_tag_22 == 'b0 && v_reg_btb_tag_23 == 'b0 && v_reg_btb_tag_24 == 'b0 && v_reg_btb_tag_25 == 'b0 && v_reg_btb_tag_26 == 'b0 && v_reg_btb_tag_27 == 'b0 && v_reg_btb_tag_28 == 'b0 && v_reg_btb_tag_29 == 'b0 && v_reg_btb_tag_30 == 'b0 && v_reg_btb_tag_31 == 'b0 && ras_stack_top_index_port2__read== 'b0 && rg_ghr_port1__read== 'b0);
endproperty

always @(negedge CLK)
rg_initialize_assert: assert property (rg_initialize_prop);"""
        return (sv)
