# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin

from typing import Dict, Union, Any, List
import random


class uatg_dcache_fill_06(IPlugin):

    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4

    def execute(self, core_yaml, isa_yaml) -> bool:
        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        filling up cache with diffent load/store variations
        lb, lbu, lh, lhu, lw, lwu, ld, sb, sh, sw, sd
        sequentially in the exact same order
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size * self._sets *
                       self._ways * 2):
            # We generate random 8 byte numbers.
            asm_data += f"\t.dword 0x{random.randrange(16 ** 16):8x}\n"

        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1"
        asm_main += f"\n\tli t3, {self._sets * self._ways}"
        asm_main += "\n\tla t2, rvtest_data\n"

        labs = ['lab1', 'lab2', 'lab3', 'lab4', 'lab5']
        labs.extend(['lab6', 'lab7', 'lab8', 'lab9', 'lab10', 'lab11', 'end'])
        tests = [
            'lb', 'lbu', 'lh', 'lhu', 'lw', 'lwu', 'ld', 'sb', 'sh', 'sw', 'sd'
        ]
        asm_lab1 = ''
        for i in range(len(labs) - 1):
            asm_lab1 += str(labs[i]) + ":\n\t" + str(
                tests[i]) + " t0, 0(t2)\n\t"
            asm_lab1 += f"addi t2, t2, {self._word_size * self._block_size}\n\t"
            asm_lab1 += "beq t4, t3, " + str(
                labs[i + 1]) + "\n\taddi t4, t4, 1\n\tj " + str(labs[i]) + "\n"

        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of ASM.
        asm = asm_main + asm_lab1 + asm_end
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
