# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_set_thrashing_02(IPlugin):
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
        """Generate asm as a list of strings that have different
        alignments based on which set they're looking to thrash."""
        iter = self._word_size * self._block_size
        ins_list = [f"\tli t1, {iter}\n\t.align {self._sets}\nins_j:\n" + \
            f"".join(
                [str(elem) for elem in [
                    f"\t.align {self._word_size * self._block_size}\n"
                    for k in range(i)]
                ]) + \
            f"\taddi t1, t1, -1\n\tbeqz t1, end\n\tj ins_j\nend:\n\tnop"
            for i in range(self._sets)]
        compile_macros = []
        return [{
            'asm_code': "\t.option norvc\n" + i,
            'asm_sig': '',
            'compile_macros': compile_macros
        } for i in ins_list]