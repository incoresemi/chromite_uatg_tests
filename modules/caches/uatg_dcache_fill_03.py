# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
import random


class uatg_dcache_fill_03(IPlugin):

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
        Perform a fence operation to clear out the data cache subsystem and the
        fill buffer.
        Perform numerous load operations to fill up the cache.
        In each iteration, we visit the next way in the same set. Once all the
        ways in a set are touched, we visit the next set.
        The total number of iterations is parameterized based on YAML input.
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        # We load the memory with data twice the size of our dcache.
        x = self._word_size * self._block_size * self._sets * self._ways * 2
        for i in range(x):
            # We generate random 8 byte numbers.
            asm_data += f"\t.dword 0x{random.randrange(16 ** 16):8x}\n"

        asm_main = f"\tfence\n\tli t0, 69\n\tli t1, {self._sets}\n\tli t5, " \
                   f"{self._ways}\n\t"
        asm_main += "li t6, {0}\n\tla t2, rvtest_data\n\tli a1, {1}\n".format(
            self._word_size * self._block_size,
            self._sets * self._word_size * self._block_size)
        asm_lab1 = "lab1:\n\tlw t0, 0(t2)\n\tadd t2, t2, a1\n\taddi t4, t4, 1"
        asm_lab1 += "\n\tblt t4, t5, lab1\n\tla t2, rvtest_data\n\t" \
                    "mv t4, x0\n\t"
        asm_lab1 += f"add t2, t2, t6\n\taddi t6, t6, " \
                    f"{self._block_size * self._word_size}"
        asm_lab1 += "\n\taddi a2, a2, 1\n\t"
        asm_lab1 += "blt a2, t1, lab1\n"
        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of asm.
        asm = asm_main + asm_lab1 + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
