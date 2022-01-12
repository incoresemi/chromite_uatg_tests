# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_critical_word_first(IPlugin):
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
        
        #0-f-10-1a-2a-20-3a-3f-4f-40-5f-5a
        #0-f-10-1a-20-2a-3a-3f-40-4f-5a-5f
        
        li = []
        for i in range(4032):
            li.append("\tnop\n")

        d = {'0x00':'0x0f',
              '0x0f':'0x10',
              '0x10':'0x17',
              '0x17':'0x27',
              '0x20':'0x37',
              '0x27':'0x20',
              '0x37':'0x3f',
              '0x3f':'0x4f',
              '0x40':'0x5f',
              '0x4f':'0x40',
              '0x57':'0x60',
              '0x5f':'0x57'}
        
        for j in range(0,4032,96):
            di = dict()
            for i in d:
                di[hex(int(i,0)+j)] = hex(int(d[i],0)+j)
            for i in di:
                temp = "label"+str(int(i,0))+":"+"\n\tj label"+str(int(di[i],0))+"\n"
                li[int(i,0)] = temp
        
        asm = ".option norvc\n"
        for i in li:
            asm += i
        
        asm += "label4032:\n\tnop\n"
        
        compile_macros = []
        return [{
            'asm_code': f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
