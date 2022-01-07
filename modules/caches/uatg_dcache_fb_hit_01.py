# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_dcache_fb_hit_01(IPlugin):
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
        self._fb_size = _dcache_dict['fb_size']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # asm_data is the test data that is loaded into memory. We use this to
        # perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        
        data = random.randrange(1,100)

        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size * self._sets *
            self._ways * 2):
            # We generate random 8 byte numbers.
            asm_data += "\t.dword 0x{0:8x}\n".format(random.randrange(16**16))
        
        asm_main = "\tfence\n\tli t0, {0}\n\t".format(data)
        asm_main += "la t2, rvtest_data\n\tli t3, {0} \n".format(
        	self._sets * self._ways)
        
        # vary the base address t2, with a fixed offset 0
        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\t"
        asm_lab1 += "addi t2, t2, {0}\n\t".format(
        	self._word_size * self._block_size)
        asm_lab1 += "beq t4, t3, asm_nop\n\taddi t4, t4, 1\n\tj lab1\n"

        asm_nop = "asm_nop:\n"
        # Perform a series of NOPs to empty the fill buffer.
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"
        
        asm_fb_miss = "asm_fb_miss:\n"
        asm_fb_hit = "asm_fb_hit:\n"
        # high is the largest legal number that can be used as an offset to
        # load/store instructions
        high = 0
        while(high < 2048 - (self._block_size * self._word_size)):
            high = high + (self._block_size * self._word_size)
        
        iter_count = 0
        #number of stores should be exactly equal to the size of fill buffer
        
        for i in range(0, high, 64):
            iter_count += 1
            if iter_count == self._fb_size:
                break

            asm_fb_miss += "\tsw t3, {0}(t2)\n".format(i)
            asm_fb_hit += "\tlw a1, {0}(t2)\n".format(i)
            # all these loads should lead to a hit in the fill buffer
        
        asm = asm_main + asm_lab1 + asm_nop + asm_fb_miss + asm_fb_hit
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
