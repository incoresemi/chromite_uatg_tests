# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List


class uatg_icache_fence_race(IPlugin):

    def __init__(self):
        super().__init__()
        self._instructions = None
        self._cache_size = None
        self._sets = 64
        self._word_size = 4
        self._block_size = 16
        self._ways = 4

    def execute(self, core_yaml, isa_yaml) -> bool:
        _icache_dict = core_yaml['icache_configuration']
        _icache_en = _icache_dict['instantiate']
        self._sets = _icache_dict['sets']
        self._word_size = _icache_dict['word_size']
        self._block_size = _icache_dict['block_size']
        self._cache_size = self._sets * self._word_size * self._block_size
        self._instructions = self._sets * self._block_size
        return _icache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        Perform a fence.i, and jump to the last instruction, check
        if the instruction still exists, and if there are any races in the bus.
        """
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        ins_list = [
            "\taddi t1, x0, 1\n" for _ in range(self._instructions * self._ways)
        ]
        ins_list[0] = "\tfence.i\n\tj end\n"
        ins_list[-1] = "end:\n\taddi t3, x0, 3\n"
        asm = "".join(asm_init) + "".join(ins_list)
        compile_macros = []
        return [{
            'asm_code': f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
    def check_log(self, log_file_path, reports_dir):
        ''
    def generate_covergroups(self, config_file):
        ''
