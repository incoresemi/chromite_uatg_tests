# See LICENSE.incore for details

import random
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_dcache_fill_05(IPlugin):

    def __init__(self):
        super().__init__()
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
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This test fiils the cache from the last set and then performs a
        fence operation to check if there is any race in the bus."""

        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
                    f"{self._sets * self._word_size * self._block_size * 8}\n" \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        data = random.randrange(0, 100)
        # fill up the cache from the last set using store ops
        asm_main = f"\tfence\n\tli t0, {data}\n\tla t1, rvtest_data\n" + \
                   f"\tla a1, rvtest_data\n\tli t2, " + \
                   f"{self._sets * self._word_size * self._block_size}\n"
        for i in range(self._ways):
            asm_main += "\tadd t1, t1, t2\n\tadd a1, a1, t2\n"

        asm_main += f"\tli t3, {self._word_size * self._block_size}\n"

        # now we have the address where we can start decrementing from
        asm_fill = "fill:\n"
        for i in range(self._sets * self._ways):
            asm_fill += "\tsw t0, 0(t1)\n\tsub t1, t1, t3\n"

        # now that we have completely filled up the cache, let's fence.
        # after this fence, we immidiately perform a load from the last location
        # to check if there is any race condition in the bus.

        asm_fill += "\tfence\n"
        asm_race = ""
        for i in range(self._sets * self._ways):
            asm_race += "\tlw a2, 0(a1)\n\tsub a1, a1, t3\n"

        asm_end = "\tnop\n\tfence.i\n"

        asm = "".join(asm_init) + asm_main + asm_fill + asm_race + asm_end
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
