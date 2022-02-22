# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
from uatg.instruction_constants import atomic_mem_ops as inst_dict
import random
import math


class uatg_icache_line_boundary(IPlugin):

    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4

    def execute(self, core_yaml, isa_yaml):
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._ways = _icache_dict['ways']
        self._ISA = isa_yaml['hart0']['ISA']
        if 'C' not in self._ISA.upper():
            return False
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Used to generate asm files with random atomic operations
        Boundaries are random but compliant to instruction
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"
        
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"init_regfile:\n\tmv x{_}, x0\n" if _ == 1 else
        f"\tmv x{_}, x0\n" for _ in range(1,32)]

        asm = "".join(asm_init)

        # load junk data into t1 and t2
        asm += f'load_data:\n\tli t1, 0x55\n\tli t2, 0x66\n' \
        f'\tli t3, {self._sets * self._ways}\n'

        for line_iter in range(self._sets * self._ways):
            # generate 4 bytes less than 1 line worth of compressed instructions
            list_inst = ['\tc.add t5, t6\n'
            for list_iter in range(int(self._word_size / 2) * self._block_size - 2)]

            # replace the last instruction with a 4-byte instruction such that
            # the first half stays on this line and the other half is elsewhere

            list_inst[-1] = f'target_{line_iter}:\n\taddi t4, t4, 1\n'

            # replace the first <> instructions with branching mechanism

            # 2 extra bytes while replacing compressed instr
            list_inst[0] = f'\tblt t4, t3, target_{line_iter}\n'

            # 2 extra bytes while replacing compressed instr
            list_inst[1] = '\tj end\n'

            asm += f'iter_{line_iter}:\n\t.align ' \
                f'{int(math.log2(self._word_size * self._block_size))}\n' + \
                f''.join(list_inst)
        
        # end
        asm += f'end:\n\tnop\n'

        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
    def check_log(self, log_file_path, reports_dir):
        ''
    def generate_covergroups(self, config_file):
        ''
