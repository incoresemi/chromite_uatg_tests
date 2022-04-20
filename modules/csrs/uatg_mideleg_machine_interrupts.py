from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin


class uatg_mideleg_machine_interrupts(IPlugin):
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

        mtime = f'''
        li a0, 173
        la x1, interrupt_address
        la x2, next_inst
        sw x2, 0(x1)
        ld x9, interrupt_address

        # enable mstatus.mie
        csrsi mstatus, 0x8

        # set the interrupt
        li t1, 0x2004000 # mtimecmp
        sd x0, 0(t1) # set mtimecmp to 0 mtimecmp < mtime -> interrupt on

        # enable mie.mtip
        li x1, 0x80
        csrw mie, x1
        nop
        wfi

        next_inst:
            nop
        '''
        msw = f'''
            li a0, 173; # to indicate trap handler that this intended
            la x1, interrupt_address
            la x2, next_inst
            sw x2, 0(x1)
            ld x9, interrupt_address

            #enable msip in mie
            csrwi mie, 0x8

            # enable mie bit in mstatus
            csrsi mstatus, 0x8

            RVMODEL_SET_MSW_INT

            # wait for interrupt
            wfi

            next_inst:
            nop
        '''
        interrupts = {
            'msw': msw,
            'mtime': mtime,
        }
        for _int in interrupts:
            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\n' \
                       f'mtrap_sigptr:\n.fill {1},4,0xdeadbeef\n'

            asm_data = '.align 3\nsample_data:\n.dword 0xbabecafe\ninterrupt_' \
                       'address:\n.dword 0xbabacafe\n'
            # compile macros for the test
            compile_macros = [
                'interrupt_testing', 'rvtest_mtrap_routine']

            privileged_test_enable = False

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
                'asm_data': asm_data,
                'compile_macros': compile_macros,
                'privileged_test': privileged_test_dict
            })
