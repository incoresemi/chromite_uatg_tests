# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin

from typing import Dict, Union, Any, List
import random


class uatg_icache_fill(IPlugin):

    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4

    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._ways = _icache_dict['ways']
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Filling icache by using only jump from one line to another
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        # We load the memory with data twice the size of our icache.
        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"

        nop = "\taddi x0, x0, 0\n"

        asm_1 = "\tj"
        asm = ".option norvc\nlabel0:\n"
        word = self._word_size
        for i in range(self._sets):
            asm += asm_1 + " label" + str(i + 1) + "\n"
            for j in range(int((word * self._block_size - word) / 4)):
                asm += nop
            asm += "label" + str(i + 1) + ":\n"

        asm += '\tfence.i\n'

        compile_macros = []

        return [{
            'asm_code': "".join(asm_init) + asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
    def check_log(self, log_file_path, reports_dir):
        ''
    def generate_covergroups(self, config_file):
        ''
