# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_set_thrashing(IPlugin):
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
        """All instructions are jumps. The first instruction jumps to a label
        that is atleast 12bits atmost 18bits apart in terms of the address,
        causing the instruction to map to the same set. This is being done
        after filling the cache entirely with NOPs."""

        ins_list = [f"ins{i}:\n\tj ins{self._instructions + i}\n" 
        for i in range(self._instructions * (self._ways * 2))]
        ins_back = [f"ins{self._instructions * (self._ways * 2) + i}:\n\tj ins{i+1}\n"
        for i in range(self._instructions)]
        ins_list.extend(ins_back)
        ins_list[-1] = ((ins_list[-1].split(":"))[0] + ":\n\tnop")
        asm = "".join(ins_list)
        compile_macros = []
        return [{
            'asm_code': f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]