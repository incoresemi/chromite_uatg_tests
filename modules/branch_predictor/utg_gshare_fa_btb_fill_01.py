# This module has a function which generates assembly program to fill the
# BTB with entries # there are 33 control insts in the generated program,
# 1 jump from the includes and 32  in the program

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import utg.regex_formats as rf
import re
import os


class utg_gshare_fa_btb_fill_01(IPlugin):

    """
    The test is used to fill the Branch Target Buffer with addresses. 
    The test fills the BTB with Conditional Branches and Jumps, Calls and Returns.
    We can find if the functioning of the BTB is as expected, through this test. As the replacement
    algorithm in this implementation of the BTB is round robin, hence it also checks if the replacement happens
    properly. 
    """

    def __init__(self):

        """ The constructor for this class. """
        super().__init__()
        self._btb_depth = 32        ## we assume that the default BTB depth is 32 

    def execute(self, _bpu_dict):

        """
        The method returns true or false.
        In order to make test_generation targeted, we adopt this approach. Based on 
        some conditions, we decide if said test should exist.

        This method also doubles up as the only method which has access to the 
        hardware configuration of the DUt in the test_class. 
        """
        _en_bpu = _bpu_dict['instantiate']        # States if the DUT has a branch predictor
        self._btb_depth = _bpu_dict['btb_depth']  # states the depth of the BTB to customize the test
        if _en_bpu and self._btb_depth:           # check condition, if BPU exits as well as btb_depth is an integer.
            return True                           # return true if this test can exist. 
        else:
            return False                          # return false if this test cannot.

    def generate_asm(self):
        """
        This method returns a string of the ASM file to be generated.

        This ASM file is written as the ASM file which will be run on the DUT.
        """

        asm_start = "\taddi t1,x0,0\n\taddi t2,x0,1\n\n"            # variable to store some initial asm boiler plate
        branch_count = int(self._btb_depth / 4)                     # The branch_count is used equally split the instructions
                                                                    # between call, jump, branch and returns
        asm_branch = ""                                             # empty string which will be populated with branching directives
        asm_jump = "\tadd t1,t1,t2\n\tjal x0,entry_" + str(branch_count +  
                                                           1) + "\n\n" # string with jump directives which will be used in a loop
        asm_call = "entry_" + str((2 * branch_count) + 1) + ":\n\n"    # string with call directives
        asm_end = "exit:\n\n\taddi x0,x0,0\n\tadd x0,x0,0\n\n"         # variable to store the final boiler plate code.
        
        for j in range((2 * branch_count) + 2, ((3 * branch_count) + 1)): # for looop to iterate through the branch counts and 
                                                                          # create a string with required call directives
            asm_call += "\tcall x1,entry_" + str(j) + "\n"
        asm_call += "\tj exit\n\n"                                  # final directve to jump to the exit label
        
        for i in range(1, self._btb_depth):                         # for loop to iterate and generate the final asm string which will be returned
            if i <= branch_count:                                   # first populate the BTB with branch instructions
                if (i % 2) == 1:                                    # conditions to return branch and loop directives
                    asm_branch += "entry_" + str(i) + ":\n"         # we do this in order to increment and decrement the control variable 
                    asm_branch += "\tadd t1,t1,t2\n\tbeq t1,t2," \  # in the loop/branch. 
                                  "entry_" + str(i) + "\n\n"
                else:
                    asm_branch += "entry_" + str(i) + ":\n"
                    asm_branch += "\tsub t1,t1,t2\n\tbeq t1,t2," \
                                  "entry_" + str(i) + "\n\n"
            elif branch_count < i <= 2 * branch_count:               # populate the the next area in the BTB with Jump
                if (i % 2) == 1:                                     # conditions checks to populate the asm string accordingly while tracking the 
                    asm_jump += "entry_" + str(i) + ":\n"            # control variable
                    asm_jump += "\tsub t1,t1,t2\n\tjal x0,entry_" + \
                                str(i + 1) + "\n\taddi x0,x0,0\n\n"
                else:
                    asm_jump += "entry_" + str(i) + ":\n"
                    asm_jump += "\tadd t1,t1,t2\n\tjal x0,entry_" + \
                                str(i + 1) + "\n\taddi x0,x0,0\n\n"

            else:                                                    # finally populate the BTB with call and retu instructions
                if i >= 3 * branch_count:
                    break
                asm_call = asm_call + "entry_" + str(i + 1) + ":\n"
                for j in range(2):
                    asm_call = asm_call + "\taddi x0,x0,0\n"
                asm_call = asm_call + "\tret\n\n"

        asm = asm_start + asm_branch + asm_jump + asm_call + asm_end  # concatenate the strings to form the final ASM sting to be returned
        return asm                                                    # return string

    def check_log(self, log_file_path, reports_dir):
        """
        This method performs a minimal check of the logs genrated from the DUT when
        the ASM test generated from this class is run.

        We use regular expressions to parse and check if the execution is as 
        expected. 
        """

        # check if the rg_allocate register value starts at 0 and traverses
        # till 31. This makes sure that the BTB was successfully filled. Also
        # check if all the 4 Control instructions are encountered at least once
        # This can be checked from the training data -> [      5610] [ 0]BPU :
        # Received Training: Training_data........

        f = open(log_file_path, "r")
        log_file = f.read()          # open the log file for parsing
        f.close()

        alloc_newind_result = re.findall(rf.alloc_newind_pattern, log_file)  # we choose the pattern among the pre-written patterns 
                                                                             # which we wrote in the regex formats file
                                                                             # selecting the pattern "Allocating new index: dd ghr: dddddddd"
        new_arr = []
        for i in range(len(alloc_newind_result)):
            new_arr.append(alloc_newind_result[i][23:])                      # appending patterns into list based on requirement for this checking

        new_arr = list(set(new_arr))     # sorting them and removing duplicates
        new_arr.sort()
        # creating the template for the YAML report for this check.
        test_report = {
            "gshare_fa_btb_fill_01_report": {
                'Doc': "ASM should have filled {0} BTB entries. This report "
                       "verifies that.".format(self._btb_depth),
                'BTB_Depth': self._btb_depth,
                'No_filled': None,
                'Execution_Status': None
            }
        }
        ct = 0        # count variable
        res = None    # the result of the test
        
        # checking if the required string is present in the log using a loop
        for i in range(self._btb_depth):
            try:
                if str(i) not in new_arr[i]:
                    pass
                else:
                    ct += 1
            except IndexError as err:
                pass
        # append count of hits to report
        test_report["gshare_fa_btb_fill_01_report"]['No_filled'] = ct
        # setting pass or fail in the report
        if ct == self._btb_depth:
            test_report["gshare_fa_btb_fill_01_report"][
                'Execution_Status'] = 'Pass'
            res = True
        else:
            test_report["gshare_fa_btb_fill_01_report"][
                'Execution_Status'] = 'Fail'
            res = False
        
        # write the yaml file in
        f = open(os.path.join(reports_dir, 'gshare_fa_btb_fill_01_report.yaml'),
                 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()

        return res   # return the result.

    def generate_covergroups(self, config_file):
        """
           returns the covergroups for this test. This is written as an SV file.

           The covergroups are used to check for coverage.
        """

        config = config_file           # contains the aliasing file as a dict.

        # variables required in the covergroup
        rg_initialize = config['bpu']['register']['bpu_rg_initialize']
        rg_allocate = config['bpu']['register']['bpu_rg_allocate']
        btb_entry = config['bpu']['wire']['bpu_btb_entry']
        
        # SV syntax to be written into the file.
        # The syntax witll check if the BTB filling was as expected.
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
        # return the SV string 
        return (sv)
