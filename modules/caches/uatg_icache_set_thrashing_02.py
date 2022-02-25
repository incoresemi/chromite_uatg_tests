# See LICENSE.incore for details

import math
from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_icache_set_thrashing_02(IPlugin):

    def __init__(self):
        super().__init__()
        self._instructions = 0
        self._cache_size = 0
        self._sets = 64
        self._word_size = 4
        self._block_size = 16
        self._ways = 4
        self._ISA = 'RV32I'
        self._XLEN = 32

    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._cache_size = self._sets * self._word_size * self._block_size
        self._instructions = self._sets * self._block_size
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Generate asm as a list of strings that have different
        alignments based on which set they're looking to thrash.
        """

        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        _iter = self._word_size * self._block_size
        _var = int(math.log2(self._word_size * self._block_size))

        ins_list = [f'\tli t1, {_iter}\n\t.align {int(math.log2(self._sets))}'
                    f'\nins_j:\n'
                    ''.join([str(e) for e in
                             [f"\tnop\n\t.align {_var}\n" for _ in range(i)]])
                    + f"\taddi t1, t1, -1\n\tbeqz t1, end\n\t"
                      f"j ins_j\nend:\n\tnop"
                    for i in range(self._sets)]
        compile_macros = []
        yield ({
            'asm_code': "".join(asm_init) + "\t.option norvc\n" + i,
            'asm_sig': '',
            'compile_macros': compile_macros
        } for i in ins_list)

    def check_log(self, log_file_path, reports_dir):
        """

        """

    def generate_covergroups(self, config_file):
        """

        """
