# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List
from uatg.instruction_constants import load_store_instructions as lsi
import random


class uatg_dcache_fill_random(IPlugin):

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
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Used to generate asm files with random stores/loads
        Boundaries are random but compliant to instruction
        """
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        for i in range(self._block_size * self._sets * self._ways * 2):
            asm_data += f"\t.dword 0x{random.randrange(16 ** 16):8x}\n"
        
        tests = []
        tests.extend(lsi['rv64-loads'])
        tests.extend(lsi['rv64-stores'])

        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1"
        asm_main += f"\n\tli t3, {self._sets * self._ways}"
        asm_main += "\n\tla t2, rvtest_data\n"
        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\t"
        asm_lab1 += f"addi t2, t2, {self._word_size * self._block_size}\n\t"
        asm_lab1 += "beq t4, t3, end\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_lab1 += "end:\n\tla t2, rvtest_data\n\t"
        y = 0
        for i in range(500):
            temp = random.choice(tests)
            x = random.randint(0, 2000)
            if 'b' in temp:
                y = 1
            elif 'h' in temp:
                y = 2
            elif 'w' in temp:
                y = 4
            elif 'd' in temp:
                y = 8
            asm_lab1 += 'li t1, ' + str(y * x) + '\n\t'
            asm_lab1 += "add t3, t2, t1\n\t"
            asm_lab1 += temp + " t0, 0(t3)\n\n\t"

        asm = asm_main + asm_lab1
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