from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_mideleg_software_interrupts(IPlugin):
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

        nt = '{nt}'
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
                     'add t0, t3, 0 # move address of{nt}\t#l1 page into t0	' \
                     '# update l1 page entry with address of l2 page\n' \
                     'addi t2, x0, 1\nslli t2, t2, 12\nadd t3, t0, t2\n' \
                     'srli t5, t3, 12\nslli t5, t5, 10\nli t4, 1\n' \
                     'add t5, t5, t4\nsd t5, (t0)\n\n'
        mtime = f'li a0, 173\nla x1, interrupt_address\nla x2, next_inst\nsw ' \
                f'x2, 0(x1)\nld x9, interrupt_address\n\n# enable mie bit in ' \
                f'misa\nli x1, 8\ncsrs mstatus, x1\n\n\nli t1, 0x2004000 # ' \
                f'mtimecmp\nli t2, 0x200BFF8 # mtime\nli x1, 1\nslli x1, x1, ' \
                f'63\nsd x1, 0(t2) # write 1 << 63 to mtime  \nsd x0, 0(t1) #' \
                f' set mtimecmp to 0 mtimecmp < mtime -> interrupt on\nli x1,' \
                f' 128\n# enable msie bit in mie\ncsrw mie, x1\n' \
                f'# enable msip bit in mip\n#csrw mip, x1\n' \
                f'\n\nnext_inst:{nt}nop{nt}nop{nt}{nt}li t1, 0x2004000 # ' \
                f'mtimecmp{nt}li t2, 0x200BFF8 # mtime{nt}li x1, 1{nt}slli ' \
                f'x1, x1, 63{nt}sd x1, 0(t1) # write 1 << 63 to mtimecmp  ' \
                f'{nt}sd x0, 0(t2) # set mtime to 0 mtimecmp > mtime -> ' \
                f'interrupt off{nt}{nt}csrr x1, mstatus{nt}csrr x1, ' \
                f'mip{nt}nop{nt}nop\nnop\n '
        msw = f'li a0, 173\nla x1, interrupt_address\nla x2, ' \
              f'next_inst\nsw x2, 0(x1)\nld x9, interrupt_address' \
              f'\n\n# enable mie bit in misa\nli x1, 8\ncsrs mstatus' \
              f', x1\n\nli x1, 8\n# enable msie bit in mie\n' \
              f'csrw mie, x1\nRVMODEL_SET_MSW_INT\n# enable msip bit' \
              f' in mip\ncsrw mip, x1\n\n\nnext_inst:{nt}nop{nt}nop' \
              f'{nt}RVMODEL_CLEAR_MSW_INT{nt}csrr x1, mstatus{nt}' \
              f'csrr x1, mip{nt}nop{nt}nop\nnop\n'
        for asm_code in [msw, mtime]:

            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                       f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'

            asm_data = '.align 3\nsample_data:\n.dword 0xbabecafe\ninterrupt_' \
                       'address:\n.dword 0xbabacafe\n'
            # compile macros for the test
            compile_macros = ['interrupt_testing', 'rvtest_mtrap_routine']

            privileged_test_enable = False

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
