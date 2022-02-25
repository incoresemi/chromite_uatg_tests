from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import base_reg_file, jump_instructions
from uatg.instruction_constants import bit_walker
import random


class uatg_decoder_jump_jal(IPlugin):
    """
    This class contains the methods to generate and validate tests for
    jump instructions in RISCV-I extension
    """

    def __init__(self) -> None:
        super().__init__()
        self.isa = 'RV64I'
        self.isa_bit = 'rv64'
        self.offset_inc = 4
        self.xlen = 32
        self.num_rand_var = 100

    def execute(self, core_yaml, isa_yaml) -> bool:
        self.isa = isa_yaml['hart0']['ISA']
        if 'rv32' in self.isa:
            self.isa_bit = 'rv32'
            self.xlen = 32
            self.offset_inc = 4
        else:
            self.isa_bit = 'rv64'
            self.xlen = 64
            self.offset_inc = 8
        return True

    def generate_asm(self):
        """
        This method generates Assembly Jump instructions of varied immediate
        values.
        The test will generate the tests for jal and jalr instructions
        """

        # assembly format
        # jal -> jal rd, imm

        # for the jal instruction the rd will be iterated
        # through the 32 possible registers in RISC-V

        reg_file = base_reg_file.copy()

        inst = jump_instructions['jal'][0]

        # to indicate forward or backward jump

        jump_label = ['1b', '3f']

        for label in jump_label:
            for rd in reg_file:

                asm_code = '\n\n' + '#' * 10 + f'{inst} test' + '#' * 10 + '\n'

                # intializing thge signature pointer
                swreg = 'x31'

                # initialize swreg to point to signature_start label
                asm_code += f'RVTEST_SIGBASE({swreg}, signature_start)\n'

                # initilializing temp_register
                temp_reg = 'x1'

                # initial offset
                offset = 0

                # variable to hold the total signature bytes to be used
                sig_bytes = 0

                imm = ['0x0']

                ones = [val for val in range(1, 21)]
                for number in ones:
                    imm += [val for val in bit_walker(20, number, False)]

                trap_sigbytes = 0

                count = 0

                for imm_val in imm:

                    # if signature register needs to be used for operations
                    # then first choose a new signature pointer and move the
                    # value to it.
                    if swreg == rd:
                        newswreg = random.choice(
                            [x for x in reg_file if x not in [rd, 'x0']])
                        asm_code += f'mv {newswreg}, {swreg}\n'
                        swreg = newswreg

                    # if tempreg is used for operation, we switch temp_reg to
                    # some other register.
                    if temp_reg in [rd, swreg]:
                        new_temp_reg = random.choice(
                            [x for x in reg_file if x not in [rd, swreg, 'x0']])
                        temp_reg = new_temp_reg

                    # macro format
                    # TEST_JAL_OP(tempreg, rd, imm, label, swreg, offset, adj)

                    # perform required assembly operation
                    asm_code += f'\ninst_{count}:'
                    asm_code += f'\n#operation: {inst}\n#rd: {rd}'\
                                f', imm: {imm_val}, temp_reg: {temp_reg}'\
                                f', swreg: {swreg}\n'
                    asm_code += f'TEST_JAL_OP({temp_reg}, {rd}, {imm_val},' \
                                f'{label}, {swreg}, {offset}, 0)\n'

                    # adjust the offset. reset to 0 if it crosses 2048 and
                    # increment the current signature pointer with the
                    # current offset value
                    if offset + self.offset_inc >= 2048:
                        asm_code += f'addi {swreg}, {swreg},{offset}\n'
                        offset = 0

                    # Signbytes allocation for trap handler
                    trap_sigbytes = trap_sigbytes + (3 * self.offset_inc)

                    # increment offset by the amount of bytes updated in
                    # signature by each test-macro.
                    offset = offset + self.offset_inc

                    # keep track of the total number of signature bytes used
                    # so far.
                    sig_bytes = sig_bytes + self.offset_inc

                    count = count + 1

                # asm code to populate the signature region
                sig_code = 'signature_start:\n'
                sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                    int(sig_bytes / 4))
                sig_code += 'mtrap_count:\n'
                sig_code += ' .fill 1, 8, 0x0\n'
                sig_code += 'mtrap_sigptr:\n'
                sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                    int(trap_sigbytes / 4))

                # compile macros for the test
                compile_macros = ['rvtest_mtrap_routine']

                asm_data = '\nrvtest_data:\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'
                asm_data += '.word 0xbabecafe\n'

                # for postfix
                postfix_label = ''
                if label == '3f':
                    postfix_label = 'forward'
                elif label == '1b':
                    postfix_label = 'backward'

                # return asm_code and sig_code
                yield ({
                    'asm_code': asm_code,
                    'asm_data': asm_data,
                    'asm_sig': sig_code,
                    'compile_macros': compile_macros,
                    'name_postfix': f'rd_{rd}_{postfix_label}'
                })
