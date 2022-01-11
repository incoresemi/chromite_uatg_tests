# See LICENSE.incore for details

from ruamel.yaml.main import safe_load
from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_icache_self_modifying(IPlugin):
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
        """The code modifies itself to change the first instruction from
        loading data into t0 to fence.i This causes the branch which missed
        the first time to happen and branch to first instruction which failed
        the last time."""
        
        #t0 = starting address
        #t1 = exit address
        #t2 = exit - starting address
        #t3 = jump opcode to be written in t0
        #t4 = temporary values

        asm = ".option norvc\n"
        asm += "begin:\n"
        asm += "\tli t0, 0x80000000\n"
        asm += "\tbeqz t0, begin\n"
        asm += "\tla t1, exit\n"
        asm += "\tsub t2, t1, t0\n"
        asm += "\tli t3, 0x06f\n"
        #20th bit of t2 to 32nd bit of t3
        asm += "\tli t4, 0x100000\n"
        asm += "\tand t4, t4, t2\n"
        asm += "\tslli t4, t4, 11\n"
        asm += "\tor t3, t3, t4\n"
        #10-1 bit of t2 to 31-22 bit of t3
        asm += "\tli t4, 0x7fe\n"
        asm += "\tand t4, t4, t2\n"
        asm += "\tslli t4, t4, 20\n"
        asm += "\tor t3, t3, t4\n"
        #11th bit of t2 to 21th bit of t3
        asm += "\tli t4, 0x800\n"
        asm += "\tand t4, t4, t2\n"
        asm += "\tslli t4, t4, 9\n"
        asm += "\tor t3, t3, t4\n"
        #19-12 bit of t2 to 20-13 bit of t2
        asm += "\tli t4, 0xff000\n"
        asm += "\tand t4, t4, t2\n"
        asm += "\tslli t4, t4, 0\n"
        asm += "\tor t3, t3, t4\n"
        #writing t3 at location t0
        asm += "\tsw t3, 0(t0)\n"
        asm += "\tfence.i\n"
        asm += "\tnop\n\tnop\n\tnop\n\tnop\n\tnop\n"
        asm += "\tj begin\n"
        asm += "exit:\n"
        asm += "\tfence.i\n"
        
        compile_macros = []
        return [{
            'asm_code': asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
