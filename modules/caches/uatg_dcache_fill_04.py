# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random
class uatg_dcache_fill_04(IPlugin):
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
        """
        - Perform a `fence` operation to clear out the data cache subsystem
        and the fill buffer.
        - Load some data into a temporary register and perform `numerous
        load operations` to fill up the cache.
        - Each loop in ASM has an unconditional `jump` back to that label,
        a branch takes us out of the loop.
        - Each iteration, we visit the next `set`.
        - The total number of iterations is parameterized based on YAML input.
        """

        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = '\nrvtest_data:\n'
        
        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size *
        self._sets * self._ways * 2):
            # We generate random 4 byte numbers.
            asm_data += "\t.word 0x{0:08x}\n".format(random.randrange(16 ** 8))
            
        asm_main = f"\tfence\n\tli t0, 69\n\tli t1, 1\n" + \
            f"\tli t3, {self._sets * self._ways}\n\tla t2, rvtest_data"
        asm_lab1 = f"\nlab1:\n\tlw t0, 0(t2)\n" + \
            f"\taddi t2, t2, {self._word_size * self._block_size}\n" + \
                f"\tbeq t4, t3, end\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_end = "end:\n\tnop\n\tfence.i"
        
        #Concatenate all pieces of asm.
        asm = asm_main + asm_lab1 + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]