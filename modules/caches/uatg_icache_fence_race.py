# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_fence_race(IPlugin):
    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 4
        self._block_size = 16
        self._ways = 4
    
    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._cache_size = self._sets * self._word_size * self._block_size
        self._instructions = self._sets * self._block_size
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Perform a fence.i, and jump to the last instruction, check
        if the instruction still exists, and if there are any races in the bus.
        """
        
        ins_list = ["\taddi t1, x0, 1\n" for i in range(self._instructions * self._ways)]
        ins_list[0] = "\tfence.i\n\tj end\n"
        ins_list[-1] = "end:\n\taddi t3, x0, 3\n"
        asm = "".join(ins_list)
        compile_macros = []
        return [{
            'asm_code': f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]