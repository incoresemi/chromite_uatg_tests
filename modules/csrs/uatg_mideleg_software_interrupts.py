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

        priv_setup = f'''
.option norvc
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
SREG t4, (t0)
mv t0, t2
li t1, 0x1f8
li t5, 0x78
add t6, t3, t5
srli t6, t6, 12
slli t6, t6, 10
addi t6, t6, 1 
add t0, t0, t1
SREG t6, (t0)
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
SREG t4, (t0)
li t1, 0x78
add t0, t0, t1
add t6, t3, t1
srli t6, t6, 12
slli t6, t6, 10
addi t6, t6, 1
#ori t0, t0, 1
SREG t6, (t0)
# store l2 first entry address into the first entry of l1

'''
        ssw_delegated = f'''{priv_setup}
# delegate supervisor software interrupt to machine mode
li a0, 173; # to indicate trap handler that this intended
la x1, interrupt_address
la x2, next_inst
sw x2, 0(x1)
ld x9, interrupt_address

# enable mie bit in mstatus
csrsi mstatus, 0xA

# enable ssie bit in mie
csrwi mie, 0x2

# enable ssip in mideleg
csrwi mideleg, 0x2

RVTEST_SUPERVISOR_ENTRY(12, 8, 60)
101:
    csrwi sip, 0x2
    li t1, 1
    wfi
next_inst: 
    nop
    nop
    csrr x1, scause
    nop
    nop
supervisor_exit_label:
test_exit:
nop
nop

'''

        stime_delegated = f'''{priv_setup}
# delegate supervisor software interrupt to machine mode
li a0, 173; # to indicate trap handler that this intended
la x1, interrupt_address
la x2, next_inst
sw x2, 0(x1)
ld x9, interrupt_address
li x3, 32

# enable mie bit in mstatus
csrsi mstatus, 0xA

# enable stie bit in mie
csrw mie, x3

# enable stip in mideleg
csrw mideleg, x3

csrw mip, x3

RVTEST_SUPERVISOR_ENTRY(12, 8, 60)
101:	
    wfi
next_inst:
    nop
    nop
    csrr x1, scause
    nop
    nop
supervisor_exit_label:
test_exit:
nop
nop


'''
        data = '.align 3\n' \
               'sample_data:\n' \
               '.dword 0xbabecafe\n' \
               'interrupt_address:\n' \
               '.dword 0xbabacafe\n' \
               '.align 3\n' \
               'exit_to_s_mode:\n' \
               '.dword 1\n' \
               '.align 12\n' \
               '\n' \
               'l0_pt:\n' \
               '.rept 512\n' \
               '.dword 0x0\n' \
               '.endr\n' \
               'l1_pt:\n' \
               '.rept 512\n' \
               '.dword 0x0\n' \
               '.endr\n' \
               '\n' \
               '\n' \
               'l2_pt:\n' \
               '.dword 0x200000ef # entry_0\n' \
               '.dword 0x200004ef # entry_1\n' \
               '.dword 0x200008ef # entry_2\n' \
               '.dword 0x20000cef # entry_3\n' \
               '.dword 0x200010ef # entry_4\n' \
               '.dword 0x200014ef # entry_5\n' \
               '.dword 0x200018ef # entry_6\n' \
               '.dword 0x20001cef # entry_7\n' \
               '.dword 0x200020ef # entry_8\n' \
               '.dword 0x200024ef # entry_9\n' \
               '.dword 0x200028ef # entry_10\n' \
               '.dword 0x20002cef # entry_11\n' \
               '.dword 0x200030ef # entry_12\n' \
               '.dword 0x200034ef # entry_13\n' \
               '.dword 0x200038ef # entry_14\n' \
               '.dword 0x08000ef # updated entry_15 ' \
               '# 8010EF for 2004000 # 802CEF for 200BFF8\n' \
               '#.dword 0x20003cef # entry_15\n' \
               '.dword 0x200040ef # entry_16\n' \
               '.dword 0x200044ef # entry_17\n' \
               '.dword 0x200048ef # entry_18\n' \
               '.dword 0x20004cef # entry_19\n' \
               '.dword 0x200050ef # entry_20\n' \
               '.dword 0x200054ef # entry_21\n' \
               '.dword 0x200058ef # entry_22\n' \
               '.dword 0x20005cef # entry_23\n' \
               '.dword 0x200060ef # entry_24\n' \
               '.dword 0x200064ef # entry_25\n' \
               '.dword 0x200068ef # entry_26\n' \
               '.dword 0x20006cef # entry_27\n' \
               '.dword 0x200070ef # entry_28\n' \
               '.dword 0x200074ef # entry_29\n' \
               '.dword 0x200078ef # entry_30\n' \
               '.dword 0x20007cef # entry_31\n' \
               '.dword 0x200080ef # entry_32\n' \
               '.dword 0x200084ef # entry_33\n' \
               '.dword 0x200088ef # entry_34\n' \
               '.dword 0x20008cef # entry_35\n' \
               '.dword 0x200090ef # entry_36\n' \
               '.dword 0x200094ef # entry_37\n' \
               '.dword 0x200098ef # entry_38\n' \
               '.dword 0x20009cef # entry_39\n' \
               '.dword 0x2000a0ef # entry_40\n' \
               '.dword 0x2000a4ef # entry_41\n' \
               '.dword 0x2000a8ef # entry_42\n' \
               '.dword 0x2000acef # entry_43\n' \
               '.dword 0x2000b0ef # entry_44\n' \
               '.dword 0x2000b4ef # entry_45\n' \
               '.dword 0x2000b8ef # entry_46\n' \
               '.dword 0x2000bcef # entry_47\n' \
               '.dword 0x2000c0ef # entry_48\n' \
               '.dword 0x2000c4ef # entry_49\n' \
               '.dword 0x2000c8ef # entry_50\n' \
               '.dword 0x2000ccef # entry_51\n' \
               '.dword 0x2000d0ef # entry_52\n' \
               '.dword 0x2000d4ef # entry_53\n' \
               '.dword 0x2000d8ef # entry_54\n' \
               '.dword 0x2000dcef # entry_55\n' \
               '.dword 0x2000e0ef # entry_56\n' \
               '.dword 0x2000e4ef # entry_57\n' \
               '.dword 0x2000e8ef # entry_58\n' \
               '.dword 0x2000ecef # entry_59\n' \
               '.dword 0x2000f0ef # entry_60\n' \
               '.dword 0x2000f4ef # entry_61\n' \
               '.dword 0x2000f8ef # entry_62\n' \
               '.dword 0x2000fcef # entry_63\n' \
               '.rept 448\n' \
               '.dword 0x0\n' \
               '.endr\n\n' \
               'l1_u_pt:\n' \
               '.rept 512\n' \
               '.dword 0x0\n' \
               '.endr\n' \
               'l2_u_pt:\n' \
               '.dword 0x200000ff\n' \
               '.dword 0x200004ff\n' \
               '.dword 0x200008ff\n' \
               '.dword 0x20000cff\n' \
               '.dword 0x200010ff\n' \
               '.dword 0x200014ff\n' \
               '.dword 0x200018ff\n' \
               '.dword 0x20001cff\n' \
               '.dword 0x200020ff\n' \
               '.dword 0x200024ff\n' \
               '.dword 0x200028ff\n' \
               '.dword 0x20002cff\n' \
               '.dword 0x200030ff\n' \
               '.dword 0x200034ff\n' \
               '.dword 0x200038ff\n' \
               '.dword 0x20003cff\n' \
               '.dword 0x200040ff\n' \
               '.dword 0x200044ff\n' \
               '.dword 0x200048ff\n' \
               '.dword 0x20004cff\n' \
               '.dword 0x200050ff\n' \
               '.dword 0x200054ff\n' \
               '.dword 0x200058ff\n' \
               '.dword 0x20005cff\n' \
               '.dword 0x200060ff\n' \
               '.dword 0x200064ff\n' \
               '.dword 0x200068ff\n' \
               '.dword 0x20006cff\n' \
               '.dword 0x200070ff\n' \
               '.dword 0x200074ff\n' \
               '.dword 0x200078ff\n' \
               '.dword 0x20007cff\n' \
               '.dword 0x200080ff\n' \
               '.dword 0x200084ff\n' \
               '.dword 0x200088ff\n' \
               '.dword 0x20008cff\n' \
               '.dword 0x200090ff\n' \
               '.dword 0x200094ff\n' \
               '.dword 0x200098ff\n' \
               '.dword 0x20009cff\n' \
               '.dword 0x2000a0ff\n' \
               '.dword 0x2000a4ff\n' \
               '.dword 0x2000a8ff\n' \
               '.dword 0x2000acff\n' \
               '.dword 0x2000b0ff\n' \
               '.dword 0x2000b4ff\n' \
               '.dword 0x2000b8ff\n' \
               '.dword 0x2000bcff\n' \
               '.dword 0x2000c0ff\n' \
               '.dword 0x2000c4ff\n' \
               '.dword 0x2000c8ff\n' \
               '.dword 0x2000ccff\n' \
               '.dword 0x2000d0ff\n' \
               '.dword 0x2000d4ff\n' \
               '.dword 0x2000d8ff\n' \
               '.dword 0x2000dcff\n' \
               '.dword 0x2000e0ff\n' \
               '.dword 0x2000e4ff\n' \
               '.dword 0x2000e8ff\n' \
               '.dword 0x2000ecff\n' \
               '.dword 0x2000f0ff\n' \
               '.dword 0x2000f4ff\n' \
               '.dword 0x2000f8ff\n' \
               '.dword 0x2000fcff\n' \
               '.rept 448\n' \
               '.dword 0x0\n' \
               '.endr \n'
        interrupts = {
            'ssw_delegated': ssw_delegated,
            'stime_delegated': stime_delegated
        }
        for _int in interrupts:
            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                       f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'
            # compile macros for the test
            compile_macros = [
                'interrupt_testing', 'rvtest_strap_routine',
                'rvtest_mtrap_routine', 's_u_mode_test'
            ]

            privileged_test_enable = True

            privileged_test_dict = {
                'enable': privileged_test_enable,
                'mode': 'machine',
                'page_size': 4096,
                'paging_mode': 'sv39',
                'll_pages': 64,
            }
            yield ({
                'asm_code': interrupts[_int],
                'asm_sig': sig_code,
                'asm_data': data,
                'compile_macros': compile_macros,
                'privileged_test': privileged_test_dict
            })
