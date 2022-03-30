from typing import Dict, List, Union, Any

from yapsy.IPlugin import IPlugin

from uatg.utils import paging_modes

class uatg_decompressor_reserved_insts(IPlugin):
    """
        This class contains methods to generate compressed reserved instructions
         for which the core should trap.
    """

    def __init__(self) -> None:
        super().__init__()
        self.modes = []
        self.isa = 'RV32I'
        self.isa_bit = 'rv32'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        if 'RV32' in self.isa:
            self.isa_bit = 'rv32'
            self.xlen = 32
            self.offset_inc = 4
        else:
            self.isa_bit = 'rv64'
            self.xlen = 64
            self.offset_inc = 8

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

        return True if 'c' in self.isa.lower() else False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:

        reserved_insts = []

        for mode in self.modes:

            machine_exit_count = 0

            for paging_mode in self.paging_modes:

                if mode == 'machine':
                    if machine_exit_count > 0:
                        continue
                    machine_exit_count = machine_exit_count + 1

                # c.addi14sp: 000 0000 0000 xxx00
                addi14sp = [
                    '0b00000000000' + bin(x)[2:].zfill(3) + '00'
                    for x in range(1, 2 ** 3)
                ]
                # q0 reserved: 100xxxxxxxxxxx00
                q0_reserved = [
                    '0b100' + bin(x)[2:].zfill(11) + '00' for x in range(0, 2 ** 11)
                ]
                reserved_insts += addi14sp + q0_reserved

                if self.isa_bit == 'rv64':
                    # c.addiw: 0001x00000xxxxx01 rd/r1 = 0 -> reserved
                    addiw = [
                        '0b001' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(
                            5) +
                        '01' for y in range(0, 2 ** 5) for x in range(0, 2 ** 1)
                    ]
                    reserved_insts += addiw

                # c.addi16sp: 0110000100000001 nzimm[9:4] = 0 -> reserved
                addi16sp = ['0b0110000100000001']
                # c.lui: 0110xxxxx0000001 rd/={0, 2} & nzimm[17:12] = 0 -> reserved
                lui = [
                    '0b0110' + bin(x)[2:].zfill(5) + '0000001'
                    for x in range(0, 2 ** 5)
                    if x not in (0, 2)
                ]

                if self.isa_bit == 'rv32':
                    # c.subw: 100111xxx00xxx01 RV32 -> reserved
                    subw = [
                        '0b100111' + bin(x)[2:].zfill(3) + '00' + bin(y)[2:].zfill(
                            3) +
                        '01' for x in range(0, 8) for y in range(0, 8)
                    ]
                    # c.addw: 100111xxx01xxx01 RV32 -> reserved
                    addw = [
                        '0b100111' + bin(x)[2:].zfill(3) + '01' + bin(y)[2:].zfill(
                            3) +
                        '01' for x in range(0, 2 ** 3) for y in range(0, 2 ** 3)
                    ]
                    reserved_insts += addw + subw

                # q1_reserved: 100111xxx10xxx01
                #            + 100111xxx11xxx01
                q1_reserved = ['0b100111' + bin(x)[2:].zfill(3) + '10' +
                               bin(y)[2:].zfill(3) + '01' for x in range(0, 2 ** 3)
                               for y in range(0, 2 ** 3)] + \
                              ['0b100111' + bin(x)[2:].zfill(3) + '11' +
                               bin(y)[2:].zfill(3) + '01' for x
                               in range(0, 2 ** 3) for y in range(0, 2 ** 3)]
                reserved_insts += addi16sp + lui + q1_reserved

                # c.lwsp: 010x00000xxxxx10 rd = 0 -> reserved
                lwsp = [
                    '0b001' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(
                        5) + '10'
                    for y in range(0, 2 ** 5)
                    for x in range(0, 2 ** 1)
                ]
                # c.ldsp: 011x00000xxxxx10 rd = 0 -> reserved
                ldsp = [
                    '0b011' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(
                        5) + '10'
                    for y in range(0, 2 ** 5)
                    for x in range(0, 2 ** 1)
                ]
                # c.jr 1000_00000_010 rs1 = 0 -> reserved
                jr = ['0b1000000000000010']
                reserved_insts += lwsp + ldsp + jr

                asm_code = f'.align 4\n\n\n'
                trap_sigbytes = 0
                trap_count = 0

                for res_inst in reserved_insts:
                    # To be replaced with reserved_insts
                    asm_code += f'c.nop\n.hword {res_inst}\n'

                    trap_sigbytes = trap_sigbytes + 3 * self.offset_inc
                    trap_count = trap_count + 1
                # initialize the signature region
                sig_code = 'mtrap_count:\n .fill 1, 8, 0x0\n'
                sig_code += 'mtrap_sigptr:\n'
                sig_code += f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'

                # compile macros for the test
                compile_macros = ['rvtest_mtrap_routine']
                if mode != 'machine':
                    compile_macros.append('s_u_mode_test')

                asm_data = f'\n.align 3\n\n'\
                           f'exit_to_s_mode:\n.dword\t0x1\n'\
                           f'sample_data:\n.word\t0xbabecafe\n\n'

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
                    'asm_code': asm_code,
                    'asm_sig': sig_code,
                    'asm_data': asm_data,
                    'compile_macros': compile_macros,
                    'privileged_test': privileged_test_dict,
                    'docstring': 'This test fills ghr register with ones',
                    'name_postfix': f"compressed_reserved-{mode}-" + ('' if mode == 'machine' else paging_mode)
                })
