# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import utg.regex_formats as rf
import re
import os


class utg_gshare_fa_btb_selfmodifying_01(IPlugin):

    """
    The test class returns an ASM string which 
    """

    def __init__(self):
        """ The constructor for this class. """
        super().__init__()
        pass # we do not have any variable to declare.

    def execute(self, _bpu_dict):
        """
        The method returns true or false.
        In order to make test_generation targeted, we adopt this approach. Based on 
        some conditions, we decide if said test should exist.

        This method also doubles up as the only method which has access to the 
        hardware configuration of the DUt in the test_class. 
        """
        _en_bpu = _bpu_dict['instantiate'] # States if the DUT has a branch predictor
        if _en_bpu: # check condition, if BPU exists
            return True # return true if this test can exist.
        else:
            return False # return false if this test cannot.

    def generate_asm(self):
        """
        This method returns a string of the ASM file to be generated.

        This ASM file is written as the ASM file which will be run on the DUT.
        """

        # the program generates a simple ASM file
        # the DUT will first execute a jump at one address.
        # the jump at that address will then be changed to become an arithmetic instruction
        # this will be done by storing the arith inst as a data into that address
        # if fence is exceuted, the DUT will not face any error while traversing the same instruction
        # again. 
        # fence will also invalidatethe BTB entries, empty the GHR, empty RAS, make rg allocate 0
 
        # ASM Syntax
        asm = ".option norvc\n\n"
        asm += "  addi t3,x0,0\n\taddi t4,x0,3\n\tjal x0,first\n\n"
        asm += "first:\n\taddi t3,t3,1\n\tbeq t3,t4,end\n\tjal x0,first" \
               + "\n\tjal x0,fin\n\n"
        asm += "end:\n\taddi x0,x0,0\n\taddi t0,x0,1\n\tslli t0,t0,31" \
               + "\n\taddi t0,t0,0x3a4\n"
        asm += "\taddi t1,x0,0x33\n\taddi t3,x0,4\n\tsw t1,0(t0)\n\t" \
               + "fence.i\n\tjal x0,first\n\n"
        asm = asm + "fin:\n"

        return asm # return string

    def check_log(self, log_file_path, reports_dir):
        """
        This method performs a minimal check of the logs genrated from the DUT when
        the ASM test generated from this class is run.

        We use regular expressions to parse and check if the execution is as 
        expected. 
        """
        
        # check if fence is executed properly. 
        # The BTBTags should be invalidated and the rg_allocate should return 0
        # creating the template for the YAML report for this check.
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
        log_file = f.read() # open the log file for parsing
        f.close()

        fence_executed_result = re.findall(rf.fence_executed_pattern, log_file) # we choose the pattern among the pre-written patterns 
                                                                                # which we wrote in the regex formats file
        ct = len(fence_executed_result) # count
        res = None # result
        test_report["gshare_fa_btb_selfmodifying_01_report"][
            'executed_Fence_count'] = ct  # update count
        if ct <= 1:
            # check for execution of more than one fence inst
            res = False  # failed test
            test_report["gshare_fa_btb_selfmodifying_01_report"][
                'Execution_Status'] = 'Fail'
        else:
            res = True  # test passed
            test_report["gshare_fa_btb_selfmodifying_01_report"][
                'Execution_Status'] = 'Pass'

        # write into YAML file
        f = open(os.path.join(reports_dir, 'gshare_fa_btb_selfmodifying_01_report.yaml'), 'w')
        yaml = YAML()
        yaml.default_flow_style = False
        yaml.dump(test_report, f)
        f.close()
        return res # return the result.
