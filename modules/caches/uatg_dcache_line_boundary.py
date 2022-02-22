# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
from uatg.instruction_constants import atomic_mem_ops as inst_dict
import random


class uatg_dcache_line_boundary(IPlugin):

    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4

    def execute(self, core_yaml, isa_yaml):
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
        Used to generate asm files with random atomic operations
        Boundaries are random but compliant to instruction
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"
        
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]

        asm = "".join(asm_init)

        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
    def check_log(self, log_file_path, reports_dir):
        ''
    def generate_covergroups(self, config_file):
        ''
