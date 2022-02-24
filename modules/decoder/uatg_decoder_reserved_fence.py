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
        # FENCE    : _fm__pred_succ__rs1__000__rd___0001111
        # FENCE.TSO: 1000_0011_0011_00000_000_00000_0001111

        # fm ≠ 0, 8
        fence = [
            f'0b{bin(fm)[2:].zfill(4)}{bin(pred_succ)[2:].zfill(8)}' 
            f'{bin(rs1)[2:].zfill(5)}000{bin(rd)[2:].zfill(8)}0001111'
            for fm in range(1, 8) for pred_succ in range(0, 32)
            for rs1 in range(0, 32) for rd in range(0, 32)]

        # rd=x0, rs1≠x0, fm=0, and either pred=0 or succ=0
        fence += [f'0b0000{bin(pred_succ)[2:].zfill(8)}' 
                  f'{bin(reg)[2:].zfill(5)}000000000001111'
                  for pred_succ in range(0, 32) for reg in range(1, 32) if
                  pred_succ != 0]

        # rd≠x0, rs1=x0, fm=0, and either pred=0 or succ=0
        fence += [
            f'0b0000{bin(pred_succ)[2:].zfill(8)}00000000' 
            f'{bin(reg)[2:].zfill(5)}0001111'
            for pred_succ in range(0, 32) for reg in range(1, 32) if
            pred_succ != 0]

        # rd=rs1=x0, fm=0 pred=0, succ≠0
        fence += [f'0b00000000{bin(succ)[2:].zfill(4)}00000000000000001111'
                  for succ in range(1, 16)]

        # rd=rs1=x0, fm=0 pred≠W (pred[0]=0), succ=0
        fence += [
            f'0b0000{bin(pred)[2:].zfill(4)}000000000000000000001111'
            for pred in range(0, 16) if pred % 2 != 1]

        # !!! Fence currently do not contain the TSO & PAUSE instructions.
        # Need Clarification

        test_dict = []
        offset = 2 ** 14
        ranges = range(0, len(fence), offset)
        for begin in ranges:
            asm_code = f'.align 4\n\n\n'
            trap_sigbytes = 0
            trap_count = 0
            end = -1 if begin + offset > len(fence) \
                else begin + offset
            for instruction in fence[begin:end]:
                asm_code += f'.word {instruction}\n'
                trap_sigbytes = trap_sigbytes + 3 * self.offset_inc
                trap_count = trap_count + 1
                # initialize the signature region
            sig_code = 'mtrap_count:\n'
            sig_code += ' .fill 1, 8, 0x0\n'
            sig_code += 'mtrap_sigptr:\n'
            sig_code += f' .fill {trap_sigbytes // 4},4,0xdeadbeef\n'
            # compile macros for the test
            compile_macros = ['rvtest_mtrap_routine']
            yield ({
                'asm_code': asm_code,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': f"fence"
            })
        #yield test_dict
