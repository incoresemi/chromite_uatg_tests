# see LICENSE.incore for details

import os
import re
from typing import Dict, Union, Any

from ruamel.yaml import YAML
from yapsy.IPlugin import IPlugin

from uatg.utils import paging_modes

class uatg_pte_read_write_on_execute_only_pf(IPlugin):
    """
        the test is used to setup valid and invalid pages and check the
        behaviour of the core.
    """

    def __init__(self):
        """
            class constructor
        """

        super().__init__()
        self.isa = 'RV32ISU'
        self.modes = []
        self.paging_modes = []

    def execute(self, core_yaml, isa_yaml):
        """
            returns true if the ISA of the core includes either 'S', 'U' 
            or both modes of operation.
        """

        self.isa = isa_yaml['hart0']['ISA']
        
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
                mode = isa_yaml['hart0']['satp'][f'{isa_string}']['mode']['type']['warl']['legal']
                self.satp_mode = mode[0]
        except KeyError:
            pass
        
        self.paging_modes = paging_modes(self.satp_mode, self.isa)

        if ('S' or 'U') in self.isa:
            return True
        else:
            return False

    def generate_asm(self) -> Dict[str, Union[Union[str, list], Any]]:
        """
            this method returns the actual assembly file needed.

            test tries to read and write on a execute only page
        """
        inst_list = ['sw', 'lw']

        for mode in self.modes:
            
            for paging_mode in self.paging_modes:
            
                for inst in inst_list:

                    asm = f"\n\tj exec_here\n"\
                          f"fill:\n"\
                          f".rept 1024\n"\
                          f".word 0x13\n"\
                          f".endr\n\n"\
                          f"faulting_address:\n"\
                          f".rept 1024\n"\
                          f".word 0x13\n"\
                          f".endr\n"\
                          f"exec_here:\n"\
                          f"\tla t0, faulting_address\n"\
                          f"faulting_instruction:\n"\
                          f"\t{inst} t2, 0(t0)\n\n"\
                          f"next_instruction:\n"\
                          f"\taddi t0, x0, 10\n"\
                          f"\taddi t1, x0, 0\n"\
                          f"loop:\n"\
                          f"\taddi t1, t1, 1\n"\
                          f"\tblt t1, t0, loop\n"\
                          f"\tc.nop\n"

                    asm_data = f"\n\n.align 4\n"\
                               f"return_address:\n"\
                               f".dword 0x0\n\n"\
                               f"faulty_page_address:\n"\
                               f".dword 0x0\n"\

                    trap_sigbytes = 24

                    sig_code = 'mtrap_count:\n .fill 1, 8, 0x0\n' \
                               'mtrap_sigptr:\n' \
                               f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'

                    compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test', 
                                      'page_fault_test']

                    privileged_test_dict = {
                        'enable' : True,
                        'mode' : mode,
                        'page_size' : 4096,
                        'paging_mode' : paging_mode,
                        'll_pages' : 64,
                        'fault' : True,
                        'mem_fault':True,
                        'pte_dict' : {'valid': True,
                            'read': False,
                            'write': False,
                            'execute': True,
                            'user': True,
                            'globl': True,
                            'access': True,
                            'dirty': True}
                    }
                
                    yield ({
                        'asm_code': asm,
                        'asm_data': asm_data,
                        'asm_sig': sig_code,
                        'compile_macros': compile_macros,
                        'privileged_test': privileged_test_dict,
                        'docstring': 'This test fills ghr register with ones',
                        'name_postfix': f"{inst}-{mode}-{paging_mode}"
                    })
