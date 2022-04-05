from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_medeleg_exceptions_2(IPlugin):
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
        # 12 Instruction page fault:
        # 13 Load page fault:
        # 15 Store/AMO page fault:

        nt = '\n\t'
        priv_setup = f'\t# setting up root PTEs{nt}la t0, l0_pt # load ' \
                     f'address of root page\n{nt}# setting up l0 table to ' \
                     f'point l1 table{nt}addi t1, x0, 1 # add value 1 to ' \
                     f'reg{nt}slli t2, t1, 12 # left shift to create a ' \
                     f'pagewith value == page size{nt}add t3, t2, t0 # add ' \
                     f'with the existing address to get address of level l ' \
                     f'page{nt}srli t4, t3, 12 # divide that address with ' \
                     f'page size{nt}slli t4, t4, 10 # left shift for PTE ' \
                     f'format{nt}add t4, t4, t1 # set valid bit to 1{nt}' \
                     'mv t2, t0\n\tli t1, 0x1e0\n\tadd t0, t0, t1\n'\
                     '\tSREG t4, (t0)\n\tmv t0, t2\n'\
                     f'# store l1 first entry address into the ' \
                     f'first entry of l0\n{nt}#address updation{nt}add ' \
                     f't0, t3, 0 # move the address of level 1 page to ' \
                     f't0\n{nt}# setting up l1 table to point l2 ' \
                     f'table{nt}addi t1, x0, 1 # add value 1 to ' \
                     f'reg{nt}slli t2, t1, 12 # left shift to create a ' \
                     f'pagewith value == page size{nt}add t3, t2, t0 # add ' \
                     f'with the existing address to get address of level l ' \
                     f'page{nt}srli t4, t3, 12 # divide that address with ' \
                     f'page size{nt}slli t4, t4, 10 # left shift for PTE ' \
                     f'format{nt}add t4, t4, t1 # set valid bit to 1{nt}\n ' \
                     f'SREG t4, 0(t0) # ' \
                     f'store l2 first entry address into the first entry of ' \
                     f'l1\n '

        address_loading = f'address_loading:{nt}li a0, 173{nt}la t5, ' \
                          f'faulting_instruction{nt}la t6, return_address{nt}' \
                          f'sd t5, 0(t6)\n\n'

        for i in ('instruction', 'address'):
            offset = f'offset_adjustment:{nt}li t3, 0xf{nt}li t4, 0xf000{nt}' \
                     f'la t5, faulting_{i}{nt}and t5, t5, t4{nt}srli ' \
                     f't5, t5, 12{nt}and t5, t5, t3{nt}slli t5, t5, 3{nt}la ' \
                     f't6, l2_pt{nt}add t6, t6, t5{nt}li t3, 0x200000ee{nt}sd' \
                     f' t3, 0(t6){nt}la t5, faulty_page_address{nt}' \
                     f'sd t6, 0(t5)\n'

            execution = f'next_instruction:{nt}addi t0, x0, 10{nt}' \
                        f'addi t1, x0, 0\n{nt}loop:{nt}addi t1, t1, 1{nt}' \
                        f'blt t1, t0, loop{nt}c.nop\n'

            if i == 'address':
                execution = f'{nt}j exec_here{nt}fill:{nt}.rept 1024{nt}' \
                            f'.word 0x13{nt}.endr{nt}faulting_address:{nt}' \
                            f'.rept 1024{nt}.word 0x13{nt}.endr{nt}exec_here:' \
                            f'{nt}la t0, faulting_address\n\n' \
                            f'faulting_instruction:{nt}lw t2, 0(t0){nt}' \
                            f'sw t2, 0(t0){nt}' + execution
            else:
                execution = f'faulting_instruction:{nt}add t2, t0, t0{nt}' \
                            + execution

            # execution += f'next_instruction:{nt}{nt}addi t0, x0, 10{nt}' \
            #              f'addi t1, x0, 0\n\nloop:{nt}addi t1, t1, 1{nt}' \
            #              f'blt t1, t0, loop{nt}c.nop\n\n'

            asm_code = f'\n.option norvc\n{priv_setup}\n\n' \
                       f'li a0, 173\n{address_loading}{offset}\n\n' \
                       f'RVTEST_SUPERVISOR_ENTRY(12, 8, 60)\n' \
                       f'supervisor_entry_label:\n\ntest_entry:\n' \
                       f'.option rvc\n{nt}{execution}.option norvc\n' \
                       f'test_exit:\n' \
                       f'RVTEST_SUPERVISOR_EXIT()\n' \
                       f'# assuming va!=pa\nsupervisor_exit_label:\n'

            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                       f'mtrap_sigptr:\n .fill {6},4,0xdeadbeef\n'

            asm_data = '.align 3\nexit_to_s_mode:\n.dword\t0x01\n\n'\
                       'sample_data:\n.word\t0xbabecafe\n'\
                       '.word\t0xdeadbeef\n\n'\
                       '.align 3\nsatp_mode_val:\n.dword\t0x0\n\n'\
                       'faulty_page_address:\n.dword 0x0\n'\
                       'return_address:\n.dword\t0x0\n\n' \
                       '.align 12 \nl0_pt:\n.rept 512\n.dword 0x0\n.endr' \
                       '\nl1_pt:\n .rept 512\n.dword 0x0\n.endr\n' \
                       'l2_pt:\n.dword 0x200000ef ' \
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
                       '0x2000fcef \n.rept 448\n.dword 0x0\n.endr\nl2_u_pt:' \
                       '\n.rept 448\n.dword 0x0\n.endr\naccess_fault:\n' \
                       '.dword 0x0'

            # compile macros for the test
            compile_macros = ['rvtest_mtrap_routine', 's_u_mode_test',
                              'access_fault_test', 'page_fault_test']

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
