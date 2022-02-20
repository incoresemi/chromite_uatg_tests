# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
import re
import os
from typing import Dict, Union, Any, List


class uatg_gshare_fa_fence_01(IPlugin):
    """
    This program generates an assembly program which fences the CPU and
    checks if the BTB entries are invalidated
    """

    def __init__(self):
        """ The constructor for this class. """
        super().__init__()
        self.recurse_level = 5
        # used to specify the depth of recursion in calls
        self._btb_depth = 32
        # we assume that the default BTB depth is 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        """
        The method returns true or false.
        In order to make test_generation targeted, we adopt this approach. Based
        on some conditions, we decide if said test should exist.

        This method also doubles up as the only method which has access to the 
        hardware configuration of the DUt in the test_class. 
        """
        _bpu_dict = core_yaml['branch_predictor']
        self._btb_depth = _bpu_dict['btb_depth']
        # states the depth of the BTB
        _en_bpu = _bpu_dict['instantiate']
        # States if the DUT has a branch predictor

        self.isa = isa_yaml['hart0']['ISA']
        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')

        if 'S' in self.isa and 'U' in self.isa:
            self.modes.append('user')

        if self._btb_depth and _en_bpu:
            # check condition, if BPU exists and btb depth is valid
            return True  # return true if this test can exist.
        else:
            # return false if this test cannot.
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        This method returns a string of the ASM file to be generated.

        This ASM file is written as the ASM file which will be run on the DUT.
        """

        # This code is derived from ras_push_pop code. Fence instructions are
        # introduced.reg x30 is used as looping variable. reg x31 used as
        # a temp variable
        # ASM will just fence the Core. We check if the fence happens properly.

        return_list = []

        for mode in self.modes:

            recurse_level = self.recurse_level  # reuse the self variable
            no_ops = "\taddi x31, x0, 5\n\taddi x31, x0, -5\n"  # no templates
            asm = f"\taddi x30, x0, {recurse_level}\n"  # tempate asm directives
            asm += "\tcall x1, lab1\n\tbeq x30, x0, end\n\tfence.i\n"

            for i in range(1, recurse_level + 1):
                # loop to iterate and generate the ASM
                asm += "lab" + str(i) + ":\n"
                if i == recurse_level:
                    asm += "\tfence.i\n\taddi x30,x30,-1\n"
                else:
                    asm += no_ops * 3 + f"\tcall x{i+1}, lab{i+1}\n"
                asm += no_ops * 3 + "\tret\n"
            asm += "end:\n\tnop\n"  # concatenate

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
                'docstring': '',
                'name_postfix': mode
            })

            if not privileged_test_enable:
                return return_list

        return return_list

    def check_log(self, log_file_path, reports_dir):
        """
        This method performs a minimal check of the logs generated from the DUT
        when the ASM test generated from this class is run.

        We use regular expressions to parse and check if the execution is as
        expected.
        """

        # check if rg_allocate becomes zero after encountering fence.
        # also check if the valid bits become zero
        # and if the ghr becomes zero
        # creating the template for the YAML report for this check.
        test_report = {
            "gshare_fa_fence_01_report": {
                'Doc': "ASM should have executed FENCE instructions at least "
                       "more than once.",
                'expected_Fence_count': 'presently hard_coded to 2',
                'executed_Fence_count': 0,
                'Execution_Status': ''
            }
        }

        f = open(log_file_path, "r")
        log_file = f.read()  # open the log file for parsing
        f.close()

        fence_executed_result = re.findall(rf.fence_executed_pattern, log_file)
        # we choose the pattern among the pre-written patterns
        # which we wrote in the regex formats file
        ct = len(fence_executed_result)  # count of hits

        test_report["gshare_fa_fence_01_report"]['executed_Fence_count'] = ct
        # update count
        if ct <= 1:
            # check for execution of more than one fence inst as there is one
            # fence in the boot code so out fence will be the second fence.
            res = False  # test fail
            test_report["gshare_fa_fence_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True  # test pass
            test_report["gshare_fa_fence_01_report"][
                'Execution_Status'] = 'Pass'

        # write YAML file
        f = open(os.path.join(reports_dir, 'gshare_fa_fence_01_report.yaml'),
                 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        # return the result.
        return res

    def generate_covergroups(self, config_file):
        """
           returns the covergroups for this test. This is written as an SV file.

           The covergroups are used to check for coverage.
        """

        config = config_file  # contains the aliasing file as a dict.

        # variables required in the covergroup
        rg_initialize = \
            config['branch_predictor']['register']['bpu_rg_initialize']
        rg_allocate = config['branch_predictor']['register']['bpu_rg_allocate']
        btb_tag = config['branch_predictor']['wire']['bpu_btb_tag']
        btb_tag_valid = config['branch_predictor']['wire']['bpu_btb_tag_valid']
        ras_top_index = config['branch_predictor']['wire']['bpu_ras_top_index']
        rg_ghr = config['branch_predictor']['register']['bpu_rg_ghr']

        # SV syntax as python strings
        sv = "covergroup  gshare_fa_fence_cg @(posedge " \
             "CLK);\noption.per_instance=1;\n///coverpoint -rg_initialize " \
             "should toggle from 0->1\n "
        sv += f"{rg_initialize}_cp : coverpoint {rg_initialize}" + " {\n\tbins"\
              + f" {rg_initialize}_0to1 = (0=>1);" + "\n}\n"
        sv += "///Coverpoint to check the LSB of v_reg_btb_tax_00 is valid\n"\
              f"{btb_tag_valid}_cp: coverpoint {btb_tag_valid}" + \
              "{{\n\tbins valid = {{"
        sv += f"{self._btb_depth}\'" + "b11111111_11111111_11111111_11111111" \
                                       "};\n}\n///coverpoint -  rg_initilaize" \
                                       " toggles from 1->0 2. rg_allocate " \
                                       "should become zero 3. " \
                                       "v_reg_btb_tag_XX should become 0 (the" \
                                       " entire 63bit reg) 4. " \
                                       "rg_ghr_port1__read should become " \
                                       "zeros. 5. " \
                                       "ras_stack_top_index_port2__read " \
                                       "should become 0\n "

        # loops to generate SC strings
        for i in range(self._btb_depth):
            sv += str(rg_initialize) + "_" + str(i) + ": coverpoint " + str(
                rg_initialize) + "{\n    bins " + str(rg_initialize) + "_"
            sv += str(i) + "1to0 = (1=>0) iff (" + str(
                rg_allocate) + " == 'b0 && " + str(btb_tag) + "_"
            sv += str(i) + " == 'b0 && " + str(
                ras_top_index) + "== 'b0 && " + str(rg_ghr) + "== 'b0);\n}\n"
        sv += "endgroup\n\n"
        sv += "property rg_initialize_prop;\n\n@(negedge CLK) ($fell(" \
              "rg_initialize)) |=> (rg_allocate == 'b0 && v_reg_btb_tag_0 == " \
              "'b0 && v_reg_btb_tag_1 == 'b0 && v_reg_btb_tag_2 == 'b0 && " \
              "v_reg_btb_tag_3 == 'b0 && v_reg_btb_tag_4 == 'b0 && " \
              "v_reg_btb_tag_5 == 'b0 && v_reg_btb_tag_6 == 'b0 && " \
              "v_reg_btb_tag_7 == 'b0 && v_reg_btb_tag_8 == 'b0 && " \
              "v_reg_btb_tag_9 == 'b0 && v_reg_btb_tag_10 == 'b0 && " \
              "v_reg_btb_tag_11 == 'b0 && v_reg_btb_tag_12 == 'b0 && " \
              "v_reg_btb_tag_13 == 'b0 && v_reg_btb_tag_14 == 'b0 && " \
              "v_reg_btb_tag_15 == 'b0 && v_reg_btb_tag_16 == 'b0 && " \
              "v_reg_btb_tag_17 == 'b0 && v_reg_btb_tag_18 == 'b0 && " \
              "v_reg_btb_tag_19 == 'b0 && v_reg_btb_tag_20 == 'b0 && " \
              "v_reg_btb_tag_21 == 'b0 && v_reg_btb_tag_22 == 'b0 && " \
              "v_reg_btb_tag_23 == 'b0 && v_reg_btb_tag_24 == 'b0 && " \
              "v_reg_btb_tag_25 == 'b0 && v_reg_btb_tag_26 == 'b0 && " \
              "v_reg_btb_tag_27 == 'b0 && v_reg_btb_tag_28 == 'b0 && " \
              "v_reg_btb_tag_29 == 'b0 && v_reg_btb_tag_30 == 'b0 && " \
              "v_reg_btb_tag_31 == 'b0 && ras_stack_top_index_port2__read== " \
              "'b0 && rg_ghr_port1__read== 'b0);\nendproperty\nalways @(" \
              "negedge CLK)\nrg_initialize_assert: assert property (" \
              "rg_initialize_prop); "

        return sv  # return SV string
