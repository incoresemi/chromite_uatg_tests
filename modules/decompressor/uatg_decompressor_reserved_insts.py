from yapsy.IPlugin import IPlugin


class uatg_decoder_illegal_instructions(IPlugin):
    """
        This class contains methods to generate illegal instructrions for
        which the core should trap.
    """

    def __init__(self) -> None:
        super().__init__()
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
        return True if 'c' in self.isa.lower() else False

    def generate_asm(self):
        reserved_insts = []
        test_dict = []

        # c.addi14sp: 000 0000 0000 xxx00
        addi14sp = ['0b00000000000' + bin(x)[2:].zfill(3) + '00' for x in
                    range(1, 2 ** 3)]
        # q0 reserved: 100xxxxxxxxxxx00
        q0_reserved = ['0b100' + bin(x)[2:].zfill(11) + '00' for x in
                       range(0, 2 ** 11)]
        reserved_insts += addi14sp + q0_reserved

        if self.isa_bit == 'rv64':
            # c.addiw: 0001x00000xxxxx01 rd/r1 = 0 -> reserved
            addiw = ['0b001' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(
                5) + '01'
                     for y in range(0, 2 ** 5) for x in range(0, 2 ** 1)]
            reserved_insts += addiw

        # c.addi16sp: 0110000100000001 nzimm[9:4] = 0 -> reserved
        addi16sp = ['0b0110000100000001']
        # c.lui: 0110xxxxx0000001 rd/={0, 2} & nzimm[17:12] = 0 -> reserved
        lui = ['0b0110' + bin(x)[2:].zfill(5) + '0000001' for x in
               range(0, 2 ** 5) if
               x not in (0, 2)]

        if self.isa_bit == 'rv32':
            # c.subw: 100111xxx00xxx01 RV32 -> reserved
            subw = ['0b100111' + bin(x)[2:].zfill(3) + '00' + bin(y)[2:].zfill(
                3) + '01' for x in
                    range(0, 8) for y in range(0, 8)]
            # c.addw: 100111xxx01xxx01 RV32 -> reserved
            addw = ['0b100111' + bin(x)[2:].zfill(3) + '01' + bin(y)[2:].zfill(
                3) + '01' for x in
                    range(0, 2 ** 3) for y in range(0, 2 ** 3)]
            reserved_insts += addw + subw

        # q1_reserved: 100111xxx10xxx01
        #            + 100111xxx11xxx01
        q1_reserved = ['0b100111' + bin(x)[2:].zfill(3) + '10' + bin(y)[
                                                                 2:].zfill(
            3) + '01' for x
               in range(0, 2 ** 3) for y in range(0, 2 ** 3)] + \
               ['0b100111' + bin(x)[2:].zfill(3) + '11' + bin(y)[2:].zfill(
                          3) + '01' for x
                       in range(0, 2 ** 3) for y in range(0, 2 ** 3)]
        reserved_insts += addi16sp + lui + q1_reserved

        # c.lwsp: 010x00000xxxxx10 rd = 0 -> reserved
        lwsp = [
            '0b001' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(5) + '10'
            for y in
            range(0, 2 ** 5) for x in range(0, 2 ** 1)]
        # c.ldsp: 011x00000xxxxx10 rd = 0 -> reserved
        ldsp = [
            '0b011' + bin(x)[2:].zfill(1) + '00000' + bin(y)[2:].zfill(5) + '10'
            for y in
            range(0, 2 ** 5) for x in range(0, 2 ** 1)]
        # c.jr 1000_00000_010 rs1 = 0 -> reserved
        jr = ['0b1000000000000010']
        reserved_insts += lwsp + ldsp + jr

        asm_code = f'.align 4\n\n\n'
        trap_sigbytes = 0
        trap_count = 0

        for res_inst in addi16sp+jr:  # To be replaced with reserved_insts
            asm_code += f'c.nop\n.hword {res_inst}\n'

            trap_sigbytes = trap_sigbytes + 3 * self.offset_inc
            trap_count = trap_count + 1
        # initialize the signature region
        sig_code = 'mtrap_count:\n'
        sig_code += ' .fill 1, 8, 0x0\n'
        sig_code += 'mtrap_sigptr:\n'
        sig_code += f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'

        # compile macros for the test
        compile_macros = ['rvtest_mtrap_routine']

        test_dict.append({
            'asm_code': asm_code,
            'asm_sig': sig_code,
            'compile_macros': compile_macros,
            'name_postfix': f"compressed_reserved"
        })
        return test_dict
