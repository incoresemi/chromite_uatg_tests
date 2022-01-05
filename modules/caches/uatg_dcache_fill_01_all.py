# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random

class uatg_dcache_fill_01_all(IPlugin):
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
        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = '\nrvtest_data:\n'
        
        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size *
        self._sets * self._ways * 2):
            # We generate random 4 byte numbers.
            asm_data += "\t.word 0x{0:08x}\n".format(random.randrange(16 ** 8))

        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1"
        asm_main += "\n\tli t3, {0}".format(self._sets * self._ways)
        asm_main += "\n\tla t2, rvtest_data\n"
        
        labs = ['lab1','lab2','lab3','lab4','lab5']
        labs.extend(['lab6','lab7','lab8','lab9','lab10','lab11','end'])
        tests = ['lb','lbu','lh','lhu','lw','lwu','ld','sb','sh','sw','sd']
        asm_lab1 = ''
        for i in range(len(labs)-1):
                asm_lab1 += str(labs[i])+":\n\t"+str(tests[i])+" t0, 0(t2)\n\t"
                asm_lab1 += "addi t2, t2, {0}\n\t".format(
			self._word_size * self._block_size)
                asm_lab1 += "beq t4, t3, "+str(labs[i+1])+"\n\taddi t4, t4, 1\n\tj "+str(labs[i])+"\n"
        
        asm_end = "end:\n\tnop\n\tfence.i\n"
        
        # Concatenate all pieces of ASM.
        asm = asm_main + asm_lab1 + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
