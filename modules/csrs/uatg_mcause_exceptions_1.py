from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_mcause_exceptions_1(IPlugin):
    """

    """

    def __init__(self):
        super().__init__()
        self.isa, self.xlen = 'RV32I', 32
        self.mcause, self.mideleg = None, None
        self.reset_val, self.i_reset_val = None, None
        self.int_reg_file = ['x' + str(i) for i in range(11, 32)]

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        self.xlen = 64 if '64' in self.isa else 32
        spec = isa_yaml['hart0']

        if 'mcause' in spec.keys():
            self.reset_val = spec['mcause']['reset-val']
            
            if self.xlen == 32 and spec['mcause']['rv32']['accessible']:
                self.mcause = spec['mcause']['rv32']
            elif self.xlen == 64 and spec['mcause']['rv64']['accessible']:
                self.mcause = spec['mcause']['rv64']
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
        # Cases 12-15 dealt in uatg_mcause_exceptions_2.py
        # 12 Instruction page fault:
        # 13 Load page fault:
        # 15 Store/AMO page fault:

        nt, nn = '\n\t', '\n\n'
        priv_setup = 'li a0, 173\n' \
                     f'#### Privileged Section ####{nn}' \
                     '# setting up root PTEs\n' \
                     f'la t0, l0_pt # load address of root page{nn}' \
                     '# setting up l0 table to point l1 table\n' \
                     'addi t1, x0, 1 # add value 1 to reg\n' \
                     'slli t2, t1, 12 # left shift to create a pagewith ' \
                     'value == page size\nadd t3, t2, t0 # add with the ' \
                     'existing address to get address of level l page\n' \
                     'srli t4, t3, 12 # divide that address with page size\n' \
                     'slli t4, t4, 10 # left shift for PTE format\n' \
                     'add t4, t4, t1 # set valid bit to 1\n' \
                     'mv t2, t0\n\tli t1, 0x1e0\n\tadd t0, t0, t1\n'\
                     '\tSREG t4, (t0)\n\tmv t0, t2\n'\
                     '# store l1 first entry address into the ' \
                     f'first entry of l0{nn}#address updation\n' \
                     'add t0, t3, 0 # move the address of level 1 page to t0' \
                     f'{nn}# setting up l1 table to point l2 table\n' \
                     'addi t1, x0, 1 # add value 1 to reg\n' \
                     'slli t2, t1, 12 # left shift to create a pagewith value' \
                     ' == page size\nadd t3, t2, t0 # add with the existing ' \
                     'address to get address of level l page\n' \
                     'srli t4, t3, 12 # divide that address with page size\n' \
                     'slli t4, t4, 10 # left shift for PTE format\n' \
                     'add t4, t4, t1 # set valid bit to 1\n' \
                     'SREG t4, (t0) # store l2 first entry address into the ' \
                     f'first entry of l1{nn}\n# user page table set up\n' \
                     f'la t0, l0_pt # load address of root page{nn}' \
                     f'la t3, l1_u_pt # load address of l1 user page{nn}' \
                     '# update l0 page entry with address of l1 page\n' \
                     'srli t5, t3, 12\nslli t5, t5, 10\nli t4, 1\n' \
                     f'add t5, t5, t4\nSREG t5, (t0){nn}# address updation\n' \
                     f'add t0, t3, 0 # move address of {nt}\t#l1 page into t0' \
                     '# update l1 page entry with address of l2 page\n' \
                     'addi t2, x0, 1\nslli t2, t2, 12\nadd t3, t0, t2\n' \
                     'srli t5, t3, 12\nslli t5, t5, 10\nli t4, 1\n' \
                     f'add t5, t5, t4\nSREG t5, (t0){nn}'

        inst_misaligned = f'li a0, 173\n# Instruction address misaligned\n' \
                          f'la x1, lab{nn}jr x1 # <- Exception Here\nlab:' \
                          f'{nn}' if 'C' not in self.isa else '# Cant ' \
                          'introduce Instruction Address misaligned ' \
                          f'exception{nn}'

        inst_access_trap = '# Instruction access fault\nli a0, 173\nla x2, ' \
                           'access_fault\nla x3, access_trap_return\nsd x3, ' \
                           f'0(x2){nn}li x1, {0x80000000}\naddi x1, x1, -4\n' \
                           f'jr x1 # <- Exception Here{nn}access_trap_return:' \
                           f'{nt}csrr x5, mcause{nn}'

        illegal_inst_trap = '# Illegal instruction\n.dword 0 # <- Exception' \
                            f' Here\ncsrr x5, mcause\n' \
                            f'{nn}\n'

        breakpt_trap = '# Breakpoint\nebreak # <- Exception Here\n' \
                       f'csrr x5, mcause{nn}'

        load_misaligned_trap = '# Load address misaligned\nla x1, sample_data' \
                               '\nlw x2, 1(x1) # <- Exception Here\n' \
                               f'csrr x5, mcause{nn}'

        load_access_fault = f'# Load access Fault\nli x1, {0x80000000}\n' \
                            f'addi x1, x1, -4\n' \
                            f'lw x0, 0(x1) # <- Exception Here\n' \
                            f'csrr x5, mcause{nn}'

        store_misaligned_trap = '# Store/AMO misaligned\nla x1, ' \
                                'sample_data\nsw x0, 1(x1) # <- Exception ' \
                                f'Here\ncsrr x5, mcause{nn}'

        store_access_trap = '# Store access Fault\nsw x1, 0(x0) # <- ' \
                            'Exception Here\n' \
                            f'csrr x5, mcause{nn}'

        asm_code = f'.option norvc\n.align 2\n{inst_misaligned}li a0, 173\n' \
                   f'{inst_access_trap}{nn}{illegal_inst_trap}{nn}' \
                   f'{breakpt_trap}{nn}{load_misaligned_trap}{nn}' \
                   f'{load_access_fault}{nn}{store_misaligned_trap}{nn}' \
                   f'{store_access_trap}{nn}{priv_setup}{nn}\n' \
                   f'li a0, 173\nRVTEST_SUPERVISOR_ENTRY(12, 8, 60)\n101:{nt}' \
                   f'RVTEST_USER_ENTRY(){nt}\t102:{nt}\t\tnop # now exiting ' \
                   f'from u to m{nt}RVTEST_USER_EXIT() # <- ECALL from U-Mode' \
                   f' Here{nn}test_exit:\ncsrr x6, mcause{nn}' \
                   f'RVTEST_SUPERVISOR_ENTRY(12, 8, 60) # once again entering' \
                   f' s-mode\n101:{nt}nop # now exiting from s to m\n' \
                   f'RVTEST_SUPERVISOR_EXIT() # <- ECALL from S-Mode Here\n' \
                   f'# assuming va!=pa\nsupervisor_exit_label:{nt}' \
                   f'csrr x6, mcause{nt}ECALL # <- ECALL from M-Mode Here{nt}' \
                   f'csrr x6, mcause\n' \
            
        sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                   f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'

        asm_data = '.align 3\nexit_to_s_mode:\n.dword\t0x00\n\n'\
                   'sample_data:\n.word\t0xbabecafe\n'\
                   '.word\t0xdeadbeef\n\n'\
                   '.align 3\nsatp_mode_val:\n.dword\t0x0\n\n.align ' \
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
