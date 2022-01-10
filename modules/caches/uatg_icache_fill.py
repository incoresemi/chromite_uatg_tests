# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_fill(IPlugin):
    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
    
    def execute(self, core_yaml, isa_yaml) -> bool:
        _dcache_dict = core_yaml['icache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        
        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size *
        self._sets * self._ways * 2):
            # We generate random 8 byte numbers.
            asm_data += "\t.dword 0x{0:8x}\n".format(random.randrange(16**16))
        
        nop = "\taddi x0, x0, 0\n"

        asm_1 = "\tj"
        asm = "label0:"
        word = self._word_size
        for i in range(self._sets):
            asm += asm_1+" label"+str(i+1)+"\n"
            for j in range(int(( word * self._block_size - word) / 4)):
                asm += nop
            asm += "label"+str(i+1)+":\n"
        
        asm += '\tfence.i\n'
        
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
