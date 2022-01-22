# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin
from typing import Dict, Union, Any, List


class uatg_icache_fill_02(IPlugin):

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
        Jump from last word of the line to last word of the next line
        """

        # 0-f-10-1a-2a-20-3a-3f-4f-40-5f-5a
        # 0-f-10-1a-20-2a-3a-3f-40-4f-5a-5f
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        li = []
        for i in range(4032):
            li.append("\tnop\n")

        li[0:3] = "\taddi x5,x0,2\n","label1:\n\taddi x3,x0,1\n","\tj label16\n"

        for j in range(15, 4031, 16):
            li[j] = f"label{j+1}:\n\tj label{j+17}\n"

        asm = ".option norvc\n"
        for i in li:
            asm += i

        asm += "label4032:\n\tbeq x3,x5 label1\n"

        compile_macros = []
        return [{
            'asm_code': "".join(asm_init) + f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
    def check_log(self, log_file_path, reports_dir):
        ''
    def generate_covergroups(self, config_file):
        ''
