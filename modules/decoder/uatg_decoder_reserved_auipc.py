from yapsy.IPlugin import IPlugin


class uatg_decoder_illegal_instructions(IPlugin):
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
        auipc = [f'auipc x0, {i}' for i in [hex(i) for i in range(0, 2 ** 20)]]
        
        test_dict = []
        offset = 2 ** 14
        ranges = range(0, len(auipc), offset)
        for begin in ranges:
            asm_code = f'.align 4\n\n\n'
            trap_sigbytes = 0
            trap_count = 0
            end = -1 if begin + offset > len(auipc) else begin + offset

            for instruction in auipc[begin:end]:
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
            test_dict.append({
                'asm_code': asm_code,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': f"auipc"
            })
        return test_dict
