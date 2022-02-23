# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
import random


class uatg_dcache_fill_04(IPlugin):

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
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        - Perform a `fence` operation to clear out the data cache subsystem
        and the fill buffer.
        - Load some data into a temporary register and perform `numerous
        load operations` to fill up the cache.
        - Each loop in ASM has an unconditional `jump` back to that label,
        a branch takes us out of the loop.
        - Each iteration, we visit the next `set`.
        - The total number of iterations is parameterized based on YAML input.
        """
        return_list = []

        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"

        asm_main = f"\tfence\n\tli t0, 69\n\tli t1, 1\n" + \
                   f"\tli t3, {self._sets * self._ways}\n\tla t2, rvtest_data"
        asm_lab1 = f"\nlab1:\n\tlw t0, 0(t2)\n" + \
                   f"\taddi t2, t2, {self._word_size * self._block_size}\n" + \
                   f"\tbeq t4, t3, end\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_end = "end:\n\tnop\n\tfence.i"

        # Concatenate all pieces of asm.
        asm = "".join(asm_init) + asm_main + asm_lab1 + asm_end
        compile_macros = []

        return_list.append({
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        })
        yield return_list

    def check_log(self, log_file_path, reports_dir):
        ''

    def generate_covergroups(self, config_file):
        ''
