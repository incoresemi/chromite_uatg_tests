# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uatg.regex_formats as rf
from typing import Dict, Union, Any, List
import random
class uatg_dcache_fill_04(IPlugin):
    def __init__(self):
        """This function defines the default values for all the parameters being taken as an input
        from the core and isa yaml files."""

        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
    
    def execute(self, core_yaml, isa_yaml) -> bool:
        """This function gives us access to the core and isa configurations as a dictionary,
        and is used to parameterize inputs to efficiently generate asm for all configurations
        of the chromite core."""

        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This function leverages string processing capabilities to efficiently generate
        ASM for this test. This function returns a List that consists of the asm code,
        rvtest_data and any signature dump."""

        # asm_data is the test data that is loaded into memory. We use this to perform load operations.
        asm_data = '\nrvtest_data:\n'
        
        # We load the memory with data twice the size of our dcache.
        for i in range(self._word_size * self._block_size * self._sets * self._ways * 2):
            # We generate random 4 byte numbers.
            asm_data += "\t.word 0x{0:08x}\n".format(random.randrange(16 ** 8))
            
        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1\n\tli t3, {0}\n\tla t2, rvtest_data\n".format(self._sets * self._ways)
        asm_lab1 = "lab1:\n\tlw t0, 0(t2)\n\taddi t2, t2, {0}\n\tbeq t4, t3, end\n\taddi t4, t4, 1\n\tj lab1\n".format(self._word_size * self._block_size)
        asm_end = "end:\n\tnop\n\tfence.i\n"
        
        #Concatenate all pieces of asm.
        asm = asm_main + asm_lab1 + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]