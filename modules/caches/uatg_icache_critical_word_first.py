# See LICENSE.incore for details

from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_icache_critical_word_first(IPlugin):

    def __init__(self):
        super().__init__()
        self._instructions = None
        self._cache_size = None
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
        Critical word first test
        Jumps in between lines to check if critical word is brought in first
        first to middle and vice versa
        first to last and vice versa
        middle to last and vice versa
        """

        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        # 0-f-10-1a-2a-20-3a-3f-4f-40-5f-5a
        # 0-f-10-1a-20-2a-3a-3f-40-4f-5a-5f

        li = []
        for i in range(4032):
            li.append("\tnop\n")

        d = {
            '0x00': '0x0f',
            '0x0f': '0x10',
            '0x10': '0x17',
            '0x17': '0x27',
            '0x20': '0x37',
            '0x27': '0x20',
            '0x37': '0x3f',
            '0x3f': '0x4f',
            '0x40': '0x5f',
            '0x4f': '0x40',
            '0x57': '0x60',
            '0x5f': '0x57'
        }

        for j in range(0, 4032, 96):
            di = dict()
            for i in d:
                di[hex(int(i, 0) + j)] = hex(int(d[i], 0) + j)
            for i in di:
                temp = "label" + str(int(i, 0)) + ":" + "\n\tj label" + str(
                    int(di[i], 0)) + "\n"
                li[int(i, 0)] = temp

        asm = "".join(asm_init) + ".option norvc\n"
        for i in li:
            asm += i

        asm += "label4032:\n\tnop\n"

        compile_macros = []
        yield ({
            'asm_code': f"\t.align {self._word_size}\n" + asm,
            'asm_sig': '',
            'compile_macros': compile_macros
        })

    def check_log(self, log_file_path, reports_dir):
        """
        
        """

    def generate_covergroups(self, config_file):
        """

        """
