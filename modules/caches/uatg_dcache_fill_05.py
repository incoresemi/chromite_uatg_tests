# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_dcache_fill_05(IPlugin):
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
        """This test fiils the cache from the last set and then performs a
        fence operation to check if there is any race in the bus."""

        asm_data = '\nrvtest_data:\n'
        
        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size *
        self._sets * self._ways * 2):
            # We generate random 4 byte numbers.
            asm_data += "\t.word 0x{0:08x}\n".format(random.randrange(16 ** 8))

        data = random.randrange(0,100)
        # fill up the cache from the last set using store ops
        asm_main = f"\tfence\n\tli t0, {data}\n\tla t1, rvtest_data\n" + \
            f"\tla a1, rvtest_data\n\tli t2, " + \
            f"{self._sets * self._word_size * self._block_size}\n"
        for i in range(self._ways):
            asm_main += "\tadd t1, t1, t2\n\tadd a1, a1, t2\n"
        
        asm_main += f"\tli t3, {self._word_size * self._block_size}\n"

        # now we have the address where we can start decrementing from
        asm_fill = "fill:\n"
        for i in range (self._sets * self._ways):
            asm_fill += "\tsw t0, 0(t1)\n\tsub t1, t2, t3\n"
        
        # now that we have completely filled up the cache, let's fence.
        # after this fence, we immidiately perform a load from the last location
        # to check if there is any race condition in the bus.

        asm_fill += "\tfence\n"
        asm_race = ""
        for i in range (self._sets * self._ways):
            asm_race += "\tlw a2, 0(a1)\n\tsub a1, a2, t3\n"

        asm_end = "\tnop\n\tfence.i\n"

        asm = asm_main + asm_fill + asm_race + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]