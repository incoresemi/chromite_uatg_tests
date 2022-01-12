# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random
import math

class uatg_icache_read_replacement(IPlugin):
    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 4
        self._block_size = 16
        self._ways = 4
        self._replacement = 'RR'
    
    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._replacement = _icache_dict['replacement']
        self._cache_size = self._sets * self._word_size * self._block_size
        self._instructions = self._sets * self._block_size
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This function generates asm to test replacement policies
        in the icache. A random replacement policy would result in a single
        NOP being put in the ASM."""

        self._replacement = 'RR'

        if self._replacement == 'RANDOM':
            ""

        if self._replacement == 'RR':
            iter = self._ways + 1
            k = 0
            ins_list = [[
                f"\tli t0, {iter}\n" \
                f"\t.align " \
                f"{int(math.log2(i * self._word_size))}\n" \
                f"ins1:\n\taddi t0, t0, -1\n\tbeqz t0, end\n\tj ins2\n" + \
                f"".join([
                    f"\t.align " \
                    f"{int(math.log2(self._sets * self._word_size * self._block_size))}\n" \
                    f"ins{k}:\n\tj ins{k+1}\n" for k in range(2, iter)
                ]) + \
                
                f"\t.align " \
                f"{int(math.log2(i * self._word_size))}\n" \
                f"ins{iter}:\n\tj ins1\n" \
                f"end:\n\tnop\n"
            ] for i in range(1, self._sets + 1)]
            compile_macros = []
            return [{
                'asm_code': "\t.option norvc\n" + "".join(i),
                'asm_sig': '',
                'compile_macros': compile_macros
            } for i in ins_list]

        if self._replacement == 'PLRU':
            ""

        compile_macros = []
        return [{
            'asm_code': "\tnop\n",
            'asm_sig': '',
            'compile_macros': compile_macros
        }]