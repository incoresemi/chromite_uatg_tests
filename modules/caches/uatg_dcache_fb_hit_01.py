# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
import random


class uatg_dcache_fb_hit_01(IPlugin):

    def __init__(self):
        super().__init__()
        self._fb_size = None
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
        self._fb_size = _dcache_dict['fb_size']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # asm_data is the test data that is loaded into memory. We use this to
        # perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        data = random.randrange(1, 100)

        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"

        asm_main = f"\tfence\n\tli t0, {data}\n\t"
        asm_main += f"la t2, rvtest_data\n\tli t3, {self._sets * self._ways} \n"

        # vary the base address t2, with a fixed offset 0
        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\t"
        asm_lab1 += f"addi t2, t2, {self._word_size * self._block_size}\n\t"
        asm_lab1 += "beq t4, t3, asm_nop\n\taddi t4, t4, 1\n\tj lab1\n"

        asm_nop = "asm_nop:\n"
        # Perform a series of NOPs to empty the fill buffer.
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"

        asm_fb_miss = "asm_fb_miss:\n"
        asm_fb_hit = "asm_fb_hit:\n"
        # high is the largest legal number that can be used as an offset to
        # load/store instructions
        high = 0
        while high < 2048 - (self._block_size * self._word_size):
            high = high + (self._block_size * self._word_size)

        iter_count = 0
        # number of stores should be exactly equal to the size of fill buffer

        for i in range(0, high, 64):
            iter_count += 1
            if iter_count == self._fb_size:
                break

            asm_fb_miss += f"\tsw t3, {i}(t2)\n"
            asm_fb_hit += f"\tlw a1, {i}(t2)\n"
            # all these loads should lead to a hit in the fill buffer

        asm = "".join(asm_init) + asm_main + asm_lab1 + asm_nop + asm_fb_miss + asm_fb_hit
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
