# See LICENSE.incore for details

import os
import re
from typing import Dict, Union, Any, List

import uatg.regex_formats as rf
from ruamel.yaml import YAML
from yapsy.IPlugin import IPlugin

from uatg.utils import paging_modes


class uatg_gshare_fa_btb_fill_01(IPlugin):
    """
    The test is used to fill the Branch Target Buffer with addresses. 
    It fills the BTB with Conditional Branches and Jumps, Calls and Returns.
    As the replacement algorithm in this implementation of the BTB is round
    robin, hence it also checks if the replacement happens
    properly. 
    """

    def __init__(self):
        """
        The constructor for this class.
        We assume that the default BTB depth is 32
        """
        super().__init__()
        self.modes = []
        self.isa = 'RV32I'
        self._btb_depth = 32

    def execute(self, core_yaml, isa_yaml):
        """
        The method returns true or false.
        In order to make test_generation targeted, we adopt this approach. Based
        on some conditions, we decide if said test should exist.

        This method also acts as the only method which has access to the
        hardware configuration of the DUt in the test_class. 
        """
        _bpu_dict = core_yaml['branch_predictor']
        _en_bpu = _bpu_dict['instantiate']
        # States if the DUT has a branch predictor
        self._btb_depth = _bpu_dict['btb_depth']
        # states the depth of the BTB to customize the test

        self.isa = isa_yaml['hart0']['ISA']
        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')

        if 'U' in self.isa:
            self.modes.append('user')

        if 'RV32' in self.isa:
            isa_string = 'rv32'
        else:
            isa_string = 'rv64'

        try:
            if isa_yaml['hart0']['satp'][f'{isa_string}']['accessible']:
                mode = isa_yaml['hart0']['satp'][f'{isa_string}']['mode'][
                    'type']['warl']['legal']
                self.satp_mode = mode[0]

        except KeyError:
            pass

        self.paging_modes = paging_modes(self.satp_mode, self.isa)

        if _en_bpu and self._btb_depth:
            # check condition, if BPU exists as well as btb_depth is an integer.
            return True
            # return true if this test is to be executed
        else:
            return False
            # return false if this test cannot.

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        This method returns a string of the ASM file to be generated.

        This ASM file is written as the ASM file which will be run on the DUT.
        """

        for mode in self.modes:

            machine_exit_count = 0

            for paging_mode in self.paging_modes:

                if mode == 'machine':
                    if machine_exit_count > 0:
                        continue
                    machine_exit_count = machine_exit_count + 1

                branch_count = int(self._btb_depth / 4)
                # The branch_count is used equally split the instructions
                # between call, jump, branch and returns

                asm_start = "\taddi t1,x0,0\n\taddi t2,x0,1\n\n"
                asm_end = "exit:\n\n\taddi x0,x0,0\n\tadd x0,x0,0\n\n"
                # variables to store some asm boiler plate

                asm_branch = ""
                # empty string which will be populated with branching directives
                asm_jump = f"\tadd t1,t1,t2\n\tjal x0,entry_{branch_count + 1}\n\n"
                # string with jump directives which will be used in a loop
                asm_call = f"entry_{(2 * branch_count) + 1}:\n\n"
                # string with call directives

                for j in range((2 * branch_count) + 2,
                               ((3 * branch_count) + 1)):
                    # for loop to iterate through the branch counts and create a
                    # string with required call directives
                    asm_call += f"\tcall x1,entry_{j}\n"
                asm_call += "\tj exit\n\n"
                # final directive to jump to the exit label

                for i in range(1, self._btb_depth):
                    # for loop to iterate and generate the asm string to be returned
                    if i <= branch_count:
                        # first populate the BTB with branch instructions
                        if (i % 2) == 1:
                            # conditions to return branch and loop directives
                            # we do this to increment/decrement control variable
                            asm_branch += f"entry_{i}:\n" \
                                          f"\tadd t1,t1,t2\n\tbeq t1, t2, " \
                                          f"entry_{i}\n\n"
                            # in the loop/branch.
                        else:
                            asm_branch += f"entry_{i}:\n\tsub t1,t1,t2\n\t" \
                                          f"beq t1, t2, entry_{i}\n\n"
                    elif branch_count < i <= 2 * branch_count:
                        # populate the the next area in the BTB with Jump
                        if (i % 2) == 1:
                            # conditions checks to populate the asm string
                            # accordingly while tracking the control variable
                            asm_jump += f"entry_{i}:\n" \
                                        f"\tsub t1,t1,t2\n\tjal x0,entry_{i + 1}" \
                                        f"\n\taddi x0,x0,0\n\n"
                        else:
                            asm_jump += f"entry_{i}:\n\tadd t1,t1,t2\n\t" \
                                        f"jal x0,entry_{i + 1}\n\taddi x0,x0,0\n\n"

                    else:
                        # finally populate the BTB with call and return instructions
                        if i >= 3 * branch_count:
                            break
                        asm_call = asm_call + "entry_" + str(i + 1) + ":\n"
                        for j in range(2):
                            asm_call = asm_call + "\taddi x0,x0,0\n"
                        asm_call = asm_call + "\tret\n\n"

                # concatenate the strings to form the final ASM sting to be returned
                asm = asm_start + asm_branch + asm_jump + asm_call + asm_end

                # trap signature bytes
                trap_sigbytes = 24

                # initialize the signature region
                sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\nmtrap_sigptr:\n ' \
                           f'.fill {trap_sigbytes // 4},4,0xdeadbeef\n'

                asm_data = f'\n.align 3\n\n'\
                           f'exit_to_s_mode:\n.dword\t0x1\n\n'\
                           f'sample_data:\n.word\t0xbabecafe\n'\
                           f'.word\t0xdeadbeef\n\n'\
                           f'.align 3\n\nsatp_mode_val:\n.dword\t0x0\n\n'

                # compile macros for the test
                if mode != 'machine':
                    compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test']
                else:
                    compile_macros = []

                # user can choose to generate supervisor and/or user tests in
                # addition to machine mode tests here.
                privileged_test_enable = True

                if not privileged_test_enable:
                    self.modes.remove('supervisor')
                    self.modes.remove('user')

                privileged_test_dict = {
                    'enable': privileged_test_enable,
                    'mode': mode,
                    'page_size': 4096,
                    'paging_mode': paging_mode,
                    'll_pages': 64,
                }

                yield ({
                    'asm_code':
                        asm,
                    'asm_sig':
                        sig_code,
                    'asm_data':
                        asm_data,
                    'compile_macros':
                        compile_macros,
                    'privileged_test':
                        privileged_test_dict,
                    'docstring':
                        '',
                    'name_postfix':
                        f"{mode}-" + ('' if mode == 'machine' else paging_mode)
                })

    def check_log(self, log_file_path, reports_dir):
        """
        This method performs a minimal check of the logs genrated from the DUT
        when the ASM test generated from this class is run.

        We use regular expressions to parse and check if the execution is as 
        expected. 
        """

        # check if the rg_allocate register value starts at 0 and traverses
        # till 31. This makes sure that the BTB was successfully filled. Also
        # check if all the 4 Control instructions are encountered at least once
        # This can be checked from the training data -> [      5610] [ 0]BPU :
        # Received Training: Training_data........

        f = open(log_file_path, "r")
        log_file = f.read()  # open the log file for parsing
        f.close()

        alloc_newind_result = re.findall(rf.alloc_newind_pattern, log_file)
        # we choose the pattern among the pre-written patterns which we wrote
        # in the regex formats file selecting the pattern "Allocating new
        # index: dd ghr: dddddddd"

        new_arr = []
        for i in range(len(alloc_newind_result)):
            new_arr.append(alloc_newind_result[i][23:])
            # appending patterns to list based on requirement for this checking

        new_arr = list(set(new_arr))  # sorting them and removing duplicates
        new_arr.sort()
        # creating the template for the YAML report for this check.
        test_report = {
            "gshare_fa_btb_fill_01_report": {
                'Doc': "ASM should have filled {0} BTB entries. This report "
                       "verifies that.".format(self._btb_depth),
                'BTB_Depth': self._btb_depth,
                'No_filled': 0,
                'Execution_Status': ''
            }
        }
        ct = 0  # count variable

        # checking if the required string is present in the log using a loop
        for i in range(self._btb_depth):
            try:
                if str(i) not in new_arr[i]:
                    pass
                else:
                    ct += 1
            except IndexError:
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

        return res  # return the result.

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
        btb_entry = config['branch_predictor']['wire']['bpu_btb_entry']

        # SV syntax to be written into the file.
        # The syntax will check if the BTB filling was as expected.
        sv = "covergroup gshare_fa_btb_fill_cg @(posedge " \
             "CLK);\noption.per_instance=1;\n///Coverpoint : reg rg_allocate " \
             "should change from 0 to `btb_depth -1\n "

        sv += f"{rg_allocate}_cp : coverpoint rg_{rg_allocate}[4:0] {{\n"
        sv += f"\tbins {rg_allocate}_bin[32] = {{[0:31]}} iff (" \
              f"{rg_initialize} == 0);\n}}\n///Coverpoints to check the bits " \
              f"2 and 3 of the v_reg_btb_entry_XX should contain 01,00,10 " \
              f"and 11 (across the 32 entries)\n "

        for i in range(self._btb_depth):
            sv += f"{btb_entry}_{i}_cp: coverpoint {btb_entry}_{i}"
            sv += "[3:2]{\n\tbins " + f"{btb_entry}_{i}_bin = " + \
                  "{'d0,'d1,'d2,'d3} iff(" + f"{rg_initialize} == 0);" + "\n}\n"

        sv += "endgroup\n\n"
        # return the SV string
        return sv
