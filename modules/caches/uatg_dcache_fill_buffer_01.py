# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

import random
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_dcache_fill_buffer_01(IPlugin):

    def __init__(self):
        """
        This function defines the default values for all the parameters being
        taken as an input from the core and isa yaml files.
        """

        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
        self._fb_size = 9
        self._ISA = 'RV32I'
        self._XLEN = 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        self._fb_size = _dcache_dict['fb_size']
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
        - Load some data into a temporary register and perform `numerous store
        operations` to fill up the cache.
        - Each loop in ASM has an unconditional `jump` back to that label,
        a branch takes us out of the loop.
        - Each iteration, we visit the next `set`.
        - The total number of iterations is parameterized based on YAML input.
        - Once the cache is full, we perform numerous
        `consecutive store operations`.
        - The number of iterations is parameterized based on the YAML input
        such that the fill_buffer is completely full.
        - Post filling the caches, we perform a series of `nop` instructions
        to ensure that the fill buffer is empty.
        """

        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
                    f"{self._sets * self._word_size * self._block_size}\n" \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        asm_main = f"\tfence\n\tli t0, 69\n" + \
                   f"\tli t3, {self._sets * self._ways}\n" + \
                   "\tla t2, rvtest_data\n"
        asm_lab1 = f"lab1:\n\tsw t0, 0(t2)\n" + \
                   f"\taddi t2, t2, {self._word_size * self._block_size}\n" + \
                   "\tbeq t4, t3, asm_nop\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_nop = "asm_nop:\n"

        # Perform a series of NOPs to empty the fill buffer.
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"

        # Perform a serious of continuous store operations with
        # no window for an opportunistic release.
        asm_sw = "asm_sw:\n"
        for i in range(self._fb_size * 2):
            asm_sw += f"\tsw t0, " \
                      f"{self._block_size * self._word_size * (i + 1)}" \
                      f"(t2)\n"
        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of ASM.
        asm = "".join(
            asm_init) + asm_main + asm_lab1 + asm_nop + asm_sw + asm_end

        yield ({
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': []
        })
