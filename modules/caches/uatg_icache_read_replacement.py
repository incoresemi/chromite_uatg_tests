# See LICENSE.incore for details
import random
from math import log2 as log
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_icache_read_replacement(IPlugin):

    def __init__(self):
        super().__init__()
        self._instructions = None
        self._cache_size = None
        self._sets = 64
        self._word_size = 4
        self._block_size = 16
        self._ways = 4
        self._replacement = 'RR'
        self._ISA = 'RV32I'
        self._XLEN = 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._replacement = _icache_dict['replacement']
        self._cache_size = self._sets * self._word_size * self._block_size
        self._instructions = self._sets * self._block_size
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This function generates asm to test replacement policies
        in the icache. A random replacement policy would result in a single
        NOP being put in the ASM."""

        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]

        if self._replacement == 'RR':
            iter_var = self._ways + 1
            size = self._sets * self._word_size * self._block_size
            ins_list = [[
                f"\tli t0, {iter_var}\n"
                f"\t.align "
                f"{int(log(i * self._word_size))}\n"
                f"ins1:\n\taddi t0, t0, -1\n\tbeqz t0, end\n\tj ins2\n" +
                f"".join([
                    f"\t.align "
                    f"{int(log(size))}\n"
                    f"ins{k}:\n\tj ins{k + 1}\n" for k in range(2, iter_var)
                ]) + f"\t.align "
                     f"{int(log(i * self._word_size))}\n"
                     f"ins{iter_var}:\n\tj ins1\n"
                     f"end:\n\tnop\n"
            ] for i in range(1, self._sets + 1)]

            yield ({
                'asm_code': f'{"".join(asm_init)}\t.option norvc\n{"".join(i)}',
                'asm_sig': '',
                'compile_macros': []
            } for i in ins_list)

        elif self._replacement == 'PLRU':
            iter_var = self._ways + 1
            order = [z for z in range(2, iter_var)]
            random.shuffle(order)
            size = self._sets * self._word_size * self._block_size
            ins_list = [[
                f"\tli t0, {iter_var}\n"
                f"\t.align "
                f"{int(log(i * self._word_size))}\n"
                f"ins1:\n\taddi t0, t0, -1\n\tbeqz t0, end\n"
                f"\tj ins{order[0]}\n".join([
                    f"\t.align "
                    f"{int(log(size))}\n"
                    f"ins{k}:\n\tj ins{k + 1}\n" for k in order
                ]) + f"\t.align "
                     f"{int(log(i * self._word_size))}\n"
                     f"ins{iter_var}:\n\tj ins1\n"
                     f"end:\n\tnop\n"
            ] for i in range(1, self._sets + 1)]

            yield ({
                'asm_code': f'{"".join(asm_init)}\t.option norvc\n{"".join(i)}',
                'asm_sig': '',
                'compile_macros': []
            } for i in ins_list)

        else:
            # if replacement policy is RANDOM or something else
            yield ({
                'asm_code': "\tnop\n",
                'asm_sig': '',
                'compile_macros': []
            })

    def check_log(self, log_file_path, reports_dir):
        """
        
        """

    def generate_covergroups(self, config_file):
        """

        """
