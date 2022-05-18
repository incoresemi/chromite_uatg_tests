from yapsy.IPlugin import IPlugin


class uatg_decoder_reserved_arithmetic(IPlugin):
    """
        This class contains methods to generate Reserved instructions of
        RV[32|64] IMAFD for which the core should trap.
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

        reg_file = ['x' + str(i) for i in range(0, 32)]

        # contains the format x0, x0-31, x0-31
        x0_rf_rf_cross = [
            f'x0, {rs1}, {rs2}' for rs1 in reg_file for rs2 in reg_file
        ]
        i_insts = {}

        if '64' in self.isa:
            for inst in ('addw', 'subw', 'sllw', 'srlw', 'sraw'):
                i_insts[inst] = [
                    f'{inst} {x0_rf_imm12}' for x0_rf_imm12 in x0_rf_rf_cross
                ]
            for inst in ('slliw', 'srliw', 'sraiw'):
                # SLLIW, SRLIW, SRAIW encodings with imm[5] ≠ 0 are reserved
                i_insts[inst] = [
                    # 0b0000000_[32-63]_rs1_[1, 5]_rd_0011011
                    f'.word 0b000000{bin(shamt)[2:].zfill(6)}' \
                    f'{bin(rs1)[2:].zfill(5)}{bin(sh)[2:].zfill(5)}' \
                    f'{bin(rd)[2:].zfill(5)}0011011'
                    for shamt in range(32, 64) for rs1 in range(0, 32) for sh in
                    (1, 5) for rd in range(32)
                ]

        del x0_rf_rf_cross

        for op in i_insts:
            offset = 2**14
            ranges = range(0, len(i_insts[op]), offset)
            for begin in ranges:
                asm_code = f'.align 4\n\n\n'
                trap_sigbytes = 0
                trap_count = 0
                end = -1 if begin + offset > len(i_insts[op]) \
                    else begin + offset
                for instruction in i_insts[op][begin:end]:
                    asm_code += f'{instruction}\n'
                    trap_sigbytes = trap_sigbytes + 3 * self.offset_inc
                    trap_count = trap_count + 1
                    # initialize the signature region
                sig_code = 'mtrap_count:\n'
                sig_code += ' .fill 1, 8, 0x0\n'
                sig_code += 'mtrap_sigptr:\n'
                sig_code += f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'
                # compile macros for the test
                compile_macros = ['rvtest_mtrap_routine']
            
                privileged_test_dict = {
                        'enable' : True
                }

                yield ({
                    'asm_code': asm_code,
                    'asm_sig': sig_code,
                    'compile_macros': compile_macros,
                    'privileged_test': privileged_test_dict,
                    'name_postfix': f"{op}"
                })
