# See LICENSE.incore for details

import random
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_dcache_replacement_all(IPlugin):

    def __init__(self):
        """This function defines the default values for all the parameters 
        being taken as an input from the core and isa yaml files."""

        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
        self._ISA = 'RV32I'
        self._XLEN = 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        """This function gives us access to the core and isa configurations
        as a dictionary, and is used to parameterize inputs to efficiently 
        generate asm for all configurations of the chromite core."""

        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Used to observe cache replacement policy by replacing the selected
        blocks of cache three times sequentially.
        Initially, We fill the cache by performing numerous load operations.
        After the cache is filled up we perform loads such that
        the cache is loaded with data two more times.
        Hence the cache is replaced twice.
        """

        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
                    f"{self._sets * self._word_size * self._block_size}\n" + \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        x2 = str(self._word_size * self._block_size)

        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1\n\tli t3, " + str(
            self._sets * self._ways
        ) + "\n\tli x10, 3\n\tli x8, " + x2 + "\n\tla t2, rvtest_data\n"
        asm_lab1 = "lab1:\n\tlw t0, 0(t2)\n\tadd t2, t2, x8\n\t"
        asm_lab1 += "beq t4, t3, lab2\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_lab2 = "lab2:\n\taddi x4, x0, 0\n\taddi x9, x9, 1\n\t"
        asm_lab2 += "beq x9, x10, end\n\tj lab1\n"
        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of ASM.
        asm = "".join(asm_init) + asm_main + asm_lab1 + asm_lab2 + asm_end
        compile_macros = []

        yield ({
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        })

    def check_log(self, log_file_path, reports_dir):
        """
        
        """

    def generate_covergroups(self, config_file):
        """

        """
