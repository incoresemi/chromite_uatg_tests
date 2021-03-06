# See LICENSE.incore for details

import random
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_dcache_ram_hit_01(IPlugin):

    def __init__(self):
        super().__init__()
        self._fb_size = None
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
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
        Checking if ram hit occurs
        """

        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        data = random.randrange(1, 100)
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
                    f"{self._sets * self._word_size * self._block_size}\n" + \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        asm_main = f"\tfence\n\tli t0, {data}\n\tla t2, rvtest_data\n"
        asm_main += f"\tla a2, rvtest_data\n\tli t3, " \
                    f"{self._sets * self._ways}\n"

        # vary the base address t2, with a fixed offset 0, perform stores
        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\taddi t2, t2, {0}\n".format(
            self._word_size * self._block_size)
        asm_lab1 += "\tbeq t4, t3, lab2\n\taddi t4, t4, 1\n\tj lab1\n"

        # vary the base address a2 (same as t2 initially), with a fixed offset
        # 0, and load the values stored in asm_lab1
        asm_lab2 = "lab2:\n\tlw a3, 0(a2)\n\taddi a2, a2, {0} \
            \n\tbeq a4, t3, end\n\taddi a4, a4, 1\n\tj lab2\n".format(
            self._word_size * self._block_size)

        asm_end = "end:\n\tnop\n\tfence.i\n"

        asm = "".join(asm_init) + asm_main + asm_lab1 + asm_lab2 + asm_end
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
