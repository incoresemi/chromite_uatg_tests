# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

import math
import random
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_dcache_set_thrashing(IPlugin):

    def __init__(self):
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
        - Perform a  `fence`  operation to clear out the data cache
        subsystem and the fill buffer.
        - First the cache is filled up using the following logic. All the
        ways of a set should either be  *dirty or clean*.
        - This is followed by a large series of back to back `store operations`
        with an address that maps to a single set in the cache. This ensures
        that the fillbuffer gets filled and the set thrashing process begins.
        - Now after the fill buffer is full, with each store operation a cache
        miss is encountered.
        - This process is iterated to test each cache set.
        """
        '''This test aims to perform a series of store operations to perform
        line thrashing. The sw instruction only takes a 12 bit signed offset
        (11-bit number) and thus we determine a high number such that we are
        able to change the base address of the destination register
        upon exhausting the limit in the destination address' offset.'''

        high = 0
        while high < 2048 - (self._block_size * self._word_size):
            high = high + (self._block_size * self._word_size)
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        asm_data += f"\t.rept " + \
                    f"{self._sets * self._word_size * self._block_size}\n" + \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        asm_main = f"\n\tfence\n\tli t0, 69\n\tli t1, 1\n" + \
                   f"\tli t3, {self._sets * self._ways}\n\tla t2, rvtest_data"

        # We use the high number determined by YAML imputs to pass
        # legal operands to load/store.
        for i in range(int(math.ceil((self._ways * self._sets * 2 *
                           (self._word_size * self._block_size)) / high))):
            _var = ((high + (self._word_size * self._block_size)) * (i + 1))
            asm_main += f"\n\tli x{27 - i}, " + \
                        f"{_var}"
        del _var
        # Initialize base address registers.
        for i in range(
                int(
                    math.ceil((self._ways * self._sets * 2 *
                               (self._word_size * self._block_size)) / high))):
            asm_main += f"\n\tadd x{27 - i}, x{27 - i}, t2 "

        asm_main += "\n"

        asm_lab1 = f"\nlab1:\n\tsw t0, 0(t2)\n\taddi t2, t2," + \
                   f"{self._block_size * self._word_size}\n" + \
                   f"\tbeq t4, t3, asm_nop\n\taddi t4, t4, 1\n\tj lab1"
        asm_nop = "\nasm_nop:\n\tmv t4, x0\n"

        # Empty the fill buffer by performing a series of NOPs
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"

        # Perform set thrashing
        asm_st = "asm_st:\n"
        for j in range(
                int(
                    math.ceil((self._ways * self._sets * 2 *
                               (self._word_size * self._block_size)) / high))):
            for i in range(
                    int(1 + self._ways * self._sets * 2 / math.ceil(
                        (self._ways * self._sets * 2 *
                         (self._word_size * self._block_size) / high)))):
                asm_st += f"\tlw t0, " + \
                          f"{self._block_size * self._word_size * (i + 1)}" \
                          f"(x{27 - j})\n"
        asm_end = "\nend:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of asm.
        asm = "".join(
            asm_init) + asm_main + asm_lab1 + asm_nop + asm_st + asm_end
        compile_macros = []

        yield ({
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        })

    def check_log(self, log_file_path, reports_dir):
        """
        
        """

    def generate_covergroups(self, config_file):
        """

        """
