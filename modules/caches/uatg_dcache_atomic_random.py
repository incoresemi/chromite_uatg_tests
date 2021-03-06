# See LICENSE.incore for details

import random
from typing import Dict, Union, Any, List

from uatg.instruction_constants import atomic_mem_ops as inst_dict
from yapsy.IPlugin import IPlugin


class uatg_dcache_atomic_random(IPlugin):

    def __init__(self):
        super().__init__()
        self._XLEN = 32
        self._ISA = 'RV32I'
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

        asm_data += f"\t.rept " \
                    f"{self._sets * self._word_size * self._block_size}\n" \
                    f"\t.dword 0x{random.randrange(16 ** 16):8x}\n\t.endr\n"

        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]

        inst_list = inst_dict[
            'rv64-mem-ops'] if self._XLEN == 64 else inst_dict['rv32-mem-ops']

        asm_main = "\tfence\n\tli t0, 69\n\tli t1, 1"
        asm_main += f"\n\tli t3, {self._sets * self._ways}"
        asm_main += "\n\tla t2, rvtest_data\n"
        asm_lab1 = "lab1:\n\tsw t0, 0(t2)\n\t"
        asm_lab1 += f"addi t2, t2, {self._word_size * self._block_size}\n\t"
        asm_lab1 += "beq t4, t3, end\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_lab1 += "end:\n\tla t2, rvtest_data\n\t"
        for i in range(500):
            inst = random.choice(inst_list)
            extension = list(inst[-1])
            offset = random.randint(0, 2000)
            boundary = 0
            if 'w' in extension:
                boundary = 4
            elif 'd' in extension:
                boundary = 8
            asm_lab1 += 'li t1, ' + str(boundary * offset) + '\n\t'
            asm_lab1 += 'li t4, ' + str(random.randint(0, 2000)) + '\n\t'
            asm_lab1 += "add t3, t2, t1\n\t"
            asm_lab1 += inst + " t0, t4, 0(t3)\n\n\t"

        asm = "".join(asm_init) + asm_main + asm_lab1
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
