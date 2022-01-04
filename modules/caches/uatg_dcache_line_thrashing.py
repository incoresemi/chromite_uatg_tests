# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random
import math

class uatg_dcache_line_thrashing(IPlugin):
    def __init__(self):
        """This function defines the default values for all the parameters being taken as an input
        from the core and isa yaml files."""

        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
        self._fb_size = 9
    
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

        '''This test aims to perform a series of store operations to
        perform line thrashing. The sw instruction only takes a 12 bit signed
        offset (11-bit number) and thus we determine a high number such that
        we are able to change the base address of the destination register
        upon exhausting the limit in the destination address' offset.'''
        high = 0
        while(high < 2048 - (self._block_size * self._word_size)):
            high = high + (self._block_size * self._word_size)
        
        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = '\nrvtest_data:\n'

        for i in range(self._word_size * self._block_size * self._sets *
        self._ways * 2):
            # We generate random 4 byte numbers.
            asm_data += "\t.word 0x{0:08x}\n".format(random.randrange(16**8))

        asm_main = "\tfence\n\tli t0, 69\n\tli t3, {0}\n\tli t1, 1\n\t\
li t5, {1}\n\tla t2, rvtest_data\n\tli a1, {2}".format(self._sets,
            self._ways - 1, self._block_size * self._word_size * self._sets)

        # We use the high number determined by YAML imputs to pass legal
        # operands to load/store.
        for i in range(int(math.ceil((self._ways * self._sets * 2 *
        (self._word_size * self._block_size))/high))):
            asm_main += "\n\tli x{0}, {1}".format(27 - i, ((high +
            (self._word_size * self._block_size)) * (i+1)))

        # Initialize base address registers.
        for i in range(int(math.ceil((self._ways * self._sets * 2 *
        (self._word_size * self._block_size))/high))):
            asm_main += "\n\tadd x{0}, x{0}, t2 ".format(27 - i)
        
        asm_main += "\n"

        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\tadd t2, t2, a1\n\t\
addi t0, t0, 1\n\taddi t4, t4, 1\n\tblt t4, t5, lab1\n"
        asm_lab2 = "lab2:\n\tmv t4, x0\n\tlw t0, 0(t2)\n\taddi t2, t2, {0}\
\n\taddi t0, t0, 1\n\taddi t1, t1, 1\n\tblt t1, t3, lab1\n".format(
                self._block_size * self._word_size)
        asm_nop = "asm_nop:\n"

        # Empty the fill buffer by performing a series of NOPs
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"
        
        asm_lt = "asm_lt:\n"
        
        # Perform line thrashing
        for j in range(int(math.ceil((self._ways * self._sets * 2 * (
            self._word_size * self._block_size))/high))):
            for i in range(int(1 + self._ways * self._sets * 2 /
            math.ceil((self._ways * self._sets * 2 * (self._word_size
            * self._block_size))/high))):
                asm_lt += "\tsw t0, {0}(x{1})\n".format(self._block_size
                * self._word_size * (i + 1),27 - j)

        asm_end = "\nend:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of asm.
        asm = asm_main + asm_lab1 + asm_lab2 + asm_nop + asm_lt + asm_end
        compile_macros = []        
        
        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]