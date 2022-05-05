from yapsy.IPlugin import IPlugin
from uatg.instruction_constants import illegal_generator
from typing import Dict, List


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
        return True

    def generate_asm(self) -> List[Dict[str, str]]:
        """
            The method returns an ASM test containing illegal
            instructions which will make the core trap. 
            This will be a negative test case for the decoder module.
        """
        # right now the illegal generator supports only
        # RVxxIMAFD. Hence, we filter the ISA string to
        # remove the unsupported extensions.
        # right now we remove C,S,U and Z extensions

        # FIX-ME #
        # characters to be deleted
        del_chars = 'NCSU_ZifenceiZicsrSvnapot'
        # translation table
        table = self.isa.maketrans('', '', del_chars)
        # translation
        new_isa_string = self.isa.translate(table)

        illegal_list = illegal_generator(new_isa_string)

        # define test_list

        # split the illegal instruction list using a lambda function
        f = lambda lst, n: [lst[i:i + n] for i in range(0, len(lst), n)]

        no_rvc = ''

        if 'c' not in new_isa_string.lower():
            no_rvc = '.option norvc\n\n'

        for sub_list in f(illegal_list, 100):
            asm_code = '\n\n' + '#' * 5 + \
                       f'illegal instructions for {new_isa_string}' + '#' \
                       * 5 + '\n\n'
            asm_code += f'.align 4\n\n{no_rvc}'
            asm_code += f'la x5, rvtest_data\n'

            # trap signature bytes
            trap_sigbytes = 0
            trap_count = 0

            count = 0
            for inst in sub_list:
                # instruction
                asm_code += f"\ninst_{count}:"
                asm_code += "\n\t.word {0}".format(hex(inst))

                # increment trap count and tarp signature address
                trap_sigbytes = trap_sigbytes + 3 * self.offset_inc
                trap_count = trap_count + 1

                # increment the overrall illegal instruction count
                count = count + 1

            # initialize the signature region
            sig_code = f'mtrap_count:\n .fill 1, 8, 0x0\nmtrap_sigptr:\n ' \
                       f'.fill {trap_sigbytes // 4},4,0xdeadbeef\n'

            # compile macros for the test
            compile_macros = ['rvtest_mtrap_routine']

            asm_code = f'## inst_count: {count}, trap_count: {trap_count}' + \
                       asm_code

            asm_data = '\nrvtest_data:\n.word 0xbabecafe\n.word 0xbabecafe' \
                       '\n.word 0xbabecafe\n.word 0xbabecafe\n'

            yield ({
                'asm_code': asm_code,
                'asm_data': asm_data,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'name_postfix': f"illegals_{new_isa_string}"
            })
