from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_medeleg_exceptions_1(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.medeleg, self.mideleg = None, None
        self.e_reset_val, self.i_reset_val = None, None
        self.int_reg_file = ['x' + str(i) for i in range(11, 32)]

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        spec = isa_yaml['hart0']

        if 'medeleg' in spec.keys() and 'mideleg' in spec.keys():
            self.e_reset_val = spec['medeleg']['reset-val']
            self.i_reset_val = spec['mideleg']['reset-val']

            if self.xlen == 32 and spec['medeleg']['rv32']['accessible'] \
                    and spec['mideleg']['rv32']['accessible']:
                self.medeleg = spec['medeleg']['rv32']
                self.mideleg = spec['mideleg']['rv32']
            elif self.xlen == 64 and spec['medeleg']['rv64']['accessible'] \
                    and spec['medeleg']['rv64']['accessible']:
                self.medeleg = spec['medeleg']['rv64']
                self.mideleg = spec['mideleg']['rv64']
            else:
                return False
        return True

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # Cases 0-11 dealt in this test
        # 0 Instruction address misaligned: jump to 2 byte boundary above 80M
        # 1 Instruction access fault: jump to address below 80 mil
        # 2 Illegal instruction: .dword 0
        # 3 Breakpoint: ebreak
        # 4 Load address misaligned: lw on an 1byte boundary
        # 5 Load access fault: lw on address below 80 mil
        # 6 Store/AMO address misaligned: sw on an 1byte boundary
        # 7 Store/AMO access fault: sw on address below 80 mil
        # 8 Environment call from U-mode: user pt macro
        # 9 Environment call from S-mode: supervisor pt macro
        # 11 Environment call from M-mode: ecall
        # Cases 12-15 dealt in uatg_medeleg_exceptions_2.py
        # 12 Instruction page fault:
        # 13 Load page fault:
        # 15 Store/AMO page fault:

        nt = '\n\t'
        # TODO: Page faults TBD.
        priv_setup = 'li a0, 173\n' \
                     '#### Privileged Section ####\n\n' \
                     '# setting up root PTEs\n' \
                     'la t0, l0_pt # load address of root page\n\n' \
                     '# setting up l0 table to point l1 table\n' \
                     'addi t1, x0, 1 # add value 1 to reg\n' \
                     'slli t2, t1, 12 # left shift to create a pagewith ' \
                     'value == page size\nadd t3, t2, t0 # add with the ' \
                     'existing address to get address of level l page\n' \
                     'srli t4, t3, 12 # divide that address with page size\n' \
                     'slli t4, t4, 10 # left shift for PTE format\n' \
                     'add t4, t4, t1 # set valid bit to 1\n' \
                     'sd t4, 24(t0) # store l1 first entry address into the ' \
                     'first entry of l0\n\n#address updation\n' \
                     'add t0, t3, 0 # move the address of level 1 page to t0' \
                     '\n\n# setting up l1 table to point l2 table\n' \
                     'addi t1, x0, 1 # add value 1 to reg\n' \
                     'slli t2, t1, 12 # left shift to create a pagewith value' \
                     ' == page size\nadd t3, t2, t0 # add with the existing ' \
                     'address to get address of level l page\n' \
                     'srli t4, t3, 12 # divide that address with page size\n' \
                     'slli t4, t4, 10 # left shift for PTE format\n' \
                     'add t4, t4, t1 # set valid bit to 1\n' \
                     '# calculation for offset\n' \
                     'addi t6, x0, 3\nslli t6, t6, 10\nadd t0, t0, t6\n' \
                     'sd t4, 0(t0) # store l2 first entry address into the ' \
                     'first entry of l1\n\n\n# user page table set up\n' \
                     'la t0, l0_pt # load address of root page\n\n' \
                     'la t3, l1_u_pt # load address of l1 user page\n\n' \
                     '# update l0 page entry with address of l1 page\n' \
                     'srli t5, t3, 12\nslli t5, t5, 10\nli t4, 1\n' \
                     'add t5, t5, t4\nsd t5, (t0)\n\n# address updation\n' \
                     'add t0, t3, 0 # move address of \n\t\t#l1 page into t0	' \
                     '# update l1 page entry with address of l2 page\n' \
                     'addi t2, x0, 1\nslli t2, t2, 12\nadd t3, t0, t2\n' \
                     'srli t5, t3, 12\nslli t5, t5, 10\nli t4, 1\n' \
                     'add t5, t5, t4\nsd t5, (t0)\n\n'

        inst_misaligned = f'li a0, 173\n# Instruction address misaligned\n' \
                          f'la x1, lab\n\njr x1 # <- Exception ' \
                          f'Here\nlab:' \
                          f'\n\n' if 'C' not in self.isa else '# Cant ' \
                          'introduce Instruction Address misaligned exception\n'

        inst_access_trap = '# Instruction access fault\nli a0, 173\nla x2, ' \
                           'access_fault\nla x3, access_trap_return\nsd x3, ' \
                           f'0(x2)\n\nli x1, {0x80000000}\naddi x1, x1, -4\n' \
                           'jr x1 # <- Exception Here\n\naccess_trap_return:\n'

        illegal_inst_trap = '# Illegal instruction\n.dword 0 ' \
                            '# <- Exception Here\n'

        breakpt_trap = '# Breakpoint\nebreak # <- Exception Here\n'

        load_misaligned_trap = '# Load address misaligned\nla x1, sample_data' \
                               '\nlw x2, 1(x1) # <- Exception Here\n'

        load_access_fault = f'# Load access Fault\nli x1, {0x80000000}\n' \
                            f'addi x1, x1, -4\n' \
                            'lw x0, 0(x1) # <- Exception Here\n'

        store_misaligned_trap = '# Store/AMO misaligned\nla x1, ' \
                                'sample_data\nsw x0, 1(x1) # <- Exception ' \
                                'Here\n '

        store_access_trap = '# Store access Fault\nsw x1, 0(x0) # <- ' \
                            'Exception Here\n '

        asm_code = f'.option norvc\n.align 2\n{inst_misaligned}li a0, 173\n' \
                   f'{inst_access_trap}\n\n{illegal_inst_trap}\n\n' \
                   f'{breakpt_trap}\n\n{load_misaligned_trap}\n\n' \
                   f'{load_access_fault}\n\n{store_misaligned_trap}\n\n' \
                   f'{store_access_trap}\n\n{priv_setup}\n\n\n' \
                   f'li a0, 173\n' \
                   f'RVTEST_SUPERVISOR_ENTRY(12, 8, 60)\n' \
                   f'supervisor_entry_label:{nt}' \
                   f'RVTEST_USER_ENTRY(){nt}\ttest_entry:{nt}\t\tnop{nt}' \
                   f'RVTEST_USER_EXIT() # <- ECALL from U-Mode Here{nt}' \
                   f'test_exit:\n' \
                   f'RVTEST_SUPERVISOR_EXIT() # <- ECALL from S-Mode Here\n' \
                   f'#assuming va!=pa\nsupervisor_exit_label:\n' \
                   f'ECALL # <- ECALL from M-Mode Here\n\n' \

        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'

        asm_data = '.align 4\nsample_data:\n.word 0xbabecafe\n.align ' \
                   '12\nl0_pt:\n.rept 512\n.dword 0x0\n.endr\nl1_pt:\n.rept ' \
                   '512\n.dword 0x0\n.endr\nl2_pt:\n.dword 0x200000ef ' \
                   '\n.dword 0x200004ef \n.dword 0x200008ef \n.dword ' \
                   '0x20000cef \n.dword 0x200010ef \n.dword 0x200014ef ' \
                   '\n.dword 0x200018ef \n.dword 0x20001cef \n.dword ' \
                   '0x200020ef \n.dword 0x200024ef \n.dword 0x200028ef ' \
                   '\n.dword 0x20002cef \n.dword 0x200030ef \n.dword ' \
                   '0x200034ef \n.dword 0x200038ef \n.dword 0x20003cef ' \
                   '\n.dword 0x200040ef \n.dword 0x200044ef \n.dword ' \
                   '0x200048ef \n.dword 0x20004cef \n.dword 0x200050ef ' \
                   '\n.dword 0x200054ef \n.dword 0x200058ef \n.dword ' \
                   '0x20005cef \n.dword 0x200060ef \n.dword 0x200064ef ' \
                   '\n.dword 0x200068ef \n.dword 0x20006cef \n.dword ' \
                   '0x200070ef \n.dword 0x200074ef \n.dword 0x200078ef ' \
                   '\n.dword 0x20007cef \n.dword 0x200080ef \n.dword ' \
                   '0x200084ef \n.dword 0x200088ef \n.dword 0x20008cef ' \
                   '\n.dword 0x200090ef \n.dword 0x200094ef \n.dword ' \
                   '0x200098ef \n.dword 0x20009cef \n.dword 0x2000a0ef ' \
                   '\n.dword 0x2000a4ef \n.dword 0x2000a8ef \n.dword ' \
                   '0x2000acef \n.dword 0x2000b0ef \n.dword 0x2000b4ef ' \
                   '\n.dword 0x2000b8ef \n.dword 0x2000bcef \n.dword ' \
                   '0x2000c0ef \n.dword 0x2000c4ef \n.dword 0x2000c8ef ' \
                   '\n.dword 0x2000ccef \n.dword 0x2000d0ef \n.dword ' \
                   '0x2000d4ef \n.dword 0x2000d8ef \n.dword 0x2000dcef ' \
                   '\n.dword 0x2000e0ef \n.dword 0x2000e4ef \n.dword ' \
                   '0x2000e8ef \n.dword 0x2000ecef \n.dword 0x2000f0ef ' \
                   '\n.dword 0x2000f4ef \n.dword 0x2000f8ef \n.dword ' \
                   '0x2000fcef \n.rept 448\n.dword ' \
                   '0x0\n.endr\nl1_u_pt:\n.rept 512\n.dword ' \
                   '0x0\n.endr\nl2_u_pt:\n.dword 0x200000ff \n.dword ' \
                   '0x200004ff \n.dword 0x200008ff \n.dword 0x20000cff ' \
                   '\n.dword 0x200010ff \n.dword 0x200014ff \n.dword ' \
                   '0x200018ff \n.dword 0x20001cff \n.dword 0x200020ff ' \
                   '\n.dword 0x200024ff \n.dword 0x200028ff \n.dword ' \
                   '0x20002cff \n.dword 0x200030ff \n.dword 0x200034ff ' \
                   '\n.dword 0x200038ff \n.dword 0x20003cff \n.dword ' \
                   '0x200040ff \n.dword 0x200044ff \n.dword 0x200048ff ' \
                   '\n.dword 0x20004cff \n.dword 0x200050ff \n.dword ' \
                   '0x200054ff \n.dword 0x200058ff \n.dword 0x20005cff ' \
                   '\n.dword 0x200060ff \n.dword 0x200064ff \n.dword ' \
                   '0x200068ff \n.dword 0x20006cff \n.dword 0x200070ff ' \
                   '\n.dword 0x200074ff \n.dword 0x200078ff \n.dword ' \
                   '0x20007cff \n.dword 0x200080ff \n.dword 0x200084ff ' \
                   '\n.dword 0x200088ff \n.dword 0x20008cff \n.dword ' \
                   '0x200090ff \n.dword 0x200094ff \n.dword 0x200098ff ' \
                   '\n.dword 0x20009cff \n.dword 0x2000a0ff \n.dword ' \
                   '0x2000a4ff \n.dword 0x2000a8ff \n.dword 0x2000acff ' \
                   '\n.dword 0x2000b0ff \n.dword 0x2000b4ff \n.dword ' \
                   '0x2000b8ff \n.dword 0x2000bcff \n.dword 0x2000c0ff ' \
                   '\n.dword 0x2000c4ff \n.dword 0x2000c8ff \n.dword ' \
                   '0x2000ccff \n.dword 0x2000d0ff \n.dword 0x2000d4ff ' \
                   '\n.dword 0x2000d8ff \n.dword 0x2000dcff \n.dword ' \
                   '0x2000e0ff \n.dword 0x2000e4ff \n.dword 0x2000e8ff ' \
                   '\n.dword 0x2000ecff \n.dword 0x2000f0ff \n.dword ' \
                   '0x2000f4ff \n.dword 0x2000f8ff \n.dword 0x2000fcff ' \
                   '\n.rept 448\n.dword 0x0\n.endr\n.align 2\naccess_fault:' \
                   '\n.dword 0x0'

        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test',
                          'access_fault_test']
    
        privileged_test_enable = True

        privileged_test_dict = {
            'enable': privileged_test_enable,
            'mode': 'machine',
            'page_size': 4096,
            'paging_mode': 'sv39',
            'll_pages': 64,
        }
        yield ({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'asm_data': asm_data,
            'compile_macros': compile_macros,
            'privileged_test': privileged_test_dict
        })
