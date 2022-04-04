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

        priv_setup = f'''.option norvc
        # setting up root PTEs
        la t0, l0_pt # load address of root page
        # setting up l0 table to point l1 table
        addi t1, x0, 1 # add value 1 to reg
        slli t2, t1, 12 # left shift to create a page with value == page size
        add t3, t2, t0 # add with the existing address to get address of level l page
        srli t4, t3, 12 # divide that address with page size
        slli t4, t4, 10 # left shift for PTE format
        add t4, t4, t1 # set valid bit to 1
        mv t2, t0
        li t1, 0x1e0
        add t0, t0, t1
        sd t4, (t0)
        mv t0, t2
        # store l1 first entry address into the first entry of l0
        #address updation
        add t0, t3, 0 # move the address of level 1 page to t0
        # setting up l1 table to point l2 table
        addi t1, x0, 1 # add value 1 to reg
        slli t2, t1, 12 # left shift to create a page with value == page size
        add t3, t2, t0 # add with the existing address to get address of level l page
        srli t4, t3, 12 # divide that address with page size
        slli t4, t4, 10 # left shift for PTE format
        add t4, t4, t1 # set valid bit to 1
        sd t4, (t0)
        # store l2 first entry address into the first entry of l1
        # user page table set up
        la t0, l0_pt # load address of root page
        la t3, l1_u_pt # load address of l1 user page
        # update l0 page entry with address of l1 page
        srli t5, t3, 12
        slli t5, t5, 10
        li t4, 1
        add t5, t5, t4
        sd t5, (t0)
        # address updation
        add t0, t3, 0 # move address of l1 page into t0

        # update l1 page entry with address of l2 page
        addi t2, x0, 1
        slli t2, t2, 12
        add t3, t0, t2
        srli t5, t3, 12
        slli t5, t5, 10
        li t4, 1
        add t5, t5, t4
        sd t5, (t0)
        '''
        mtime = f'''
        li a0, 173
        la x1, interrupt_address
        la x2, next_inst
        sw x2, 0(x1)
        ld x9, interrupt_address

        # enable mie bit in mstatus
        li x1, 8
        csrs mstatus, x1

        li t1, 0x2004000 # mtimecmp
        li t2, 0x200BFF8 # mtime
        li x1, 1
        slli x1, x1, 63
        sd x1, 0(t2) # write 1 << 63 to mtime
        sd x0, 0(t1) # set mtimecmp to 0 mtimecmp < mtime -> interrupt on
        # li x1, 128
        # enable msie bit in mie
        #csrw mie, x1
        # enable msip bit in mip
        #csrw mip, x1

        next_inst:
            nop
            nop
            li t1, 0x2004000 # mtimecmp
            li t2, 0x200BFF8 # mtime
            li x1, 1
            slli x1, x1, 63
            sd x1, 0(t1) # write 1 << 63 to mtimecmp
            sd x0, 0(t2) # set mtime to 0 mtimecmp > mtime -> interrupt off
            csrr x1, mstatus
            csrr x1, mip
            nop
        nop
        nop'''
        msw = f'''
            li a0, 173; # to indicate trap handler that this intended
            la x1, interrupt_address
            la x2, next_inst
            sw x2, 0(x1)
            ld x9, interrupt_address

            # enable mie bit in mstatus
            csrsi mstatus, 0x8


            RVMODEL_SET_MSW_INT

            next_inst:
              nop
              nop
              RVMODEL_CLEAR_MSW_INT
              csrr x1, mstatus
              nop
              nop
            nop
        '''

        ssw = f'''{priv_setup}

            li a0, 173; # to indicate trap handler that this intended
            la x1, interrupt_address
            la x2, next_inst
            sw x2, 0(x1)
            ld x9, interrupt_address

            # enable mie bit in mstatus
            csrsi mstatus, 0x8

            # enable ssie bit in mie
            csrwi mie, 0x2

            # enable ssip in mideleg
            csrwi mideleg, 0x2

            RVTEST_SUPERVISOR_ENTRY(12, 8, 60)
            101:	# supervisor entry point
                RVMODEL_SET_MSW_INT
                next_inst:
                    nop
                    nop
                    csrr x1, scause
                    RVMODEL_CLEAR_MSW_INT
                    nop
                    nop
            supervisor_exit_label:
            test_exit:
            nop
            nop
            '''
        stime = f'''{priv_setup}

        li a0, 173; # to indicate trap handler that this intended
        la x1, interrupt_address
        la x2, next_inst
        sw x2, 0(x1)
        ld x9, interrupt_address

        # enable mie bit in mstatus
        csrsi mstatus, 0x8

        # enable ssie bit in mie
        li x1, 32
        csrs mie, x1

        # enable stip in mideleg
        csrs mideleg, x1

        li t1, 0x2004000 # mtimecmp
        li t2, 0x200BFF8 # mtime
        li x1, 1
        slli x1, x1, 63
        sd x1, 0(t2) # write 1 << 63 to mtime
        sd x0, 0(t1) # set mtimecmp to 0 mtimecmp < mtime -> interrupt on

        next_inst:
            nop
            nop
            csrr x1, scause
            li t1, 0x2004000 # mtimecmp
            li t2, 0x200BFF8 # mtime
            li x1, 1
            slli x1, x1, 63
            sd x1, 0(t1) # write 1 << 63 to mtimecmp
            sd x0, 0(t2) # set mtime to 0 mtimecmp > mtime -> interrupt off
            nop
        supervisor_exit_label:
        test_exit:
        nop
        nop
        '''
        data = '.align 3\nexit_to_s_mode:\n.dword 1\n.align 12\n\nl0_pt:\n' \
               '.rept 512\n.dword 0x0\n.endr\nl1_pt:\n.rept 512\n.dword ' \
               '0x0\n.endr\nl2_pt:\n.dword 0x200000ef\n.dword ' \
               '0x200004ef\n.dword 0x200008ef\n.dword 0x20000cef\n.dword ' \
               '0x200010ef\n.dword 0x200014ef\n.dword 0x200018ef\n.dword ' \
               '0x20001cef\n.dword 0x200020ef\n.dword 0x200024ef\n.dword ' \
               '0x200028ef\n.dword 0x20002cef\n.dword 0x200030ef\n.dword ' \
               '0x200034ef\n.dword 0x200038ef\n.dword 0x20003cef\n.dword ' \
               '0x200040ef\n.dword 0x200044ef\n.dword 0x200048ef\n.dword ' \
               '0x20004cef\n.dword 0x200050ef\n.dword 0x200054ef\n.dword ' \
               '0x200058ef\n.dword 0x20005cef\n.dword 0x200060ef\n.dword ' \
               '0x200064ef\n.dword 0x200068ef\n.dword 0x20006cef\n.dword ' \
               '0x200070ef\n.dword 0x200074ef\n.dword 0x200078ef\n.dword ' \
               '0x20007cef\n.dword 0x200080ef\n.dword 0x200084ef\n.dword ' \
               '0x200088ef\n.dword 0x20008cef\n.dword 0x200090ef\n.dword ' \
               '0x200094ef\n.dword 0x200098ef\n.dword 0x20009cef\n.dword ' \
               '0x2000a0ef\n.dword 0x2000a4ef\n.dword 0x2000a8ef\n.dword ' \
               '0x2000acef\n.dword 0x2000b0ef\n.dword 0x2000b4ef\n.dword ' \
               '0x2000b8ef\n.dword 0x2000bcef\n.dword 0x2000c0ef\n.dword ' \
               '0x2000c4ef\n.dword 0x2000c8ef\n.dword 0x2000ccef\n.dword ' \
               '0x2000d0ef\n.dword 0x2000d4ef\n.dword 0x2000d8ef\n.dword ' \
               '0x2000dcef\n.dword 0x2000e0ef\n.dword 0x2000e4ef\n.dword ' \
               '0x2000e8ef\n.dword 0x2000ecef\n.dword 0x2000f0ef\n.dword ' \
               '0x2000f4ef\n.dword 0x2000f8ef\n.dword 0x2000fcef\n.rept ' \
               '448\n.dword 0x0\n.endr\nl1_u_pt:\n.rept 512\n.dword ' \
               '0x0\n.endr\nl2_u_pt:\n.dword 0x200000ff\n.dword ' \
               '0x200004ff\n.dword 0x200008ff\n.dword 0x20000cff\n.dword ' \
               '0x200010ff\n.dword 0x200014ff\n.dword 0x200018ff\n.dword ' \
               '0x20001cff\n.dword 0x200020ff\n.dword 0x200024ff\n.dword ' \
               '0x200028ff\n.dword 0x20002cff\n.dword 0x200030ff\n.dword ' \
               '0x200034ff\n.dword 0x200038ff\n.dword 0x20003cff\n.dword ' \
               '0x200040ff\n.dword 0x200044ff\n.dword 0x200048ff\n.dword ' \
               '0x20004cff\n.dword 0x200050ff\n.dword 0x200054ff\n.dword ' \
               '0x200058ff\n.dword 0x20005cff\n.dword 0x200060ff\n.dword ' \
               '0x200064ff\n.dword 0x200068ff\n.dword 0x20006cff\n.dword ' \
               '0x200070ff\n.dword 0x200074ff\n.dword 0x200078ff\n.dword ' \
               '0x20007cff\n.dword 0x200080ff\n.dword 0x200084ff\n.dword ' \
               '0x200088ff\n.dword 0x20008cff\n.dword 0x200090ff\n.dword ' \
               '0x200094ff\n.dword 0x200098ff\n.dword 0x20009cff\n.dword ' \
               '0x2000a0ff\n.dword 0x2000a4ff\n.dword 0x2000a8ff\n.dword ' \
               '0x2000acff\n.dword 0x2000b0ff\n.dword 0x2000b4ff\n.dword ' \
               '0x2000b8ff\n.dword 0x2000bcff\n.dword 0x2000c0ff\n.dword ' \
               '0x2000c4ff\n.dword 0x2000c8ff\n.dword 0x2000ccff\n.dword ' \
               '0x2000d0ff\n.dword 0x2000d4ff\n.dword 0x2000d8ff\n.dword ' \
               '0x2000dcff\n.dword 0x2000e0ff\n.dword 0x2000e4ff\n.dword ' \
               '0x2000e8ff\n.dword 0x2000ecff\n.dword 0x2000f0ff\n.dword ' \
               '0x2000f4ff\n.dword 0x2000f8ff\n.dword 0x2000fcff\n.rept ' \
               '448\n.dword 0x0\n.endr '
        interrupts = {'msw': msw, 'mtime': mtime, 'ssw': ssw,
                      'stime': stime}
        for int in interrupts:
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
                'asm_code': interrupts[int],
                'asm_sig': sig_code,
                'asm_data': asm_data if int in ('msw', 'mtime')
                else asm_data + data,
                'compile_macros': compile_macros if int in ('msw', 'mtime')
                else compile_macros + ['s_u_mode_test'],
                'privileged_test': privileged_test_dict
            })
