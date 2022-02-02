# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

from yapsy.IPlugin import IPlugin

from typing import Dict, Union, Any, List
import random


class uatg_dcache_critical_word(IPlugin):

    def __init__(self):
        super().__init__()
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4
        self._fb_size = 9

    def execute(self, core_yaml, isa_yaml) -> bool:
        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        self._fb_size = _dcache_dict['fb_size']
        self._ISA = isa_yaml['hart0']['ISA']
        if '32' in self._ISA:
            self._XLEN = 32
        elif '64' in self._ISA:
            self._XLEN = 64
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        to test critical word first is correctly done,
        - perform load/store to the higest byte of a line followed by the the
          lowest byte.
        - the middle of the line and then the highest byte.
        - the middle of the line followed by the lowest byte
        - highest byte followed by the second highest byte
        - lowest byte followed by the highest byte (and so on)
        - Do the above for loads and stoers separately after fencing the cache
        """

        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        asm_main = "\tfence\n\tli t1, 8000\n\tli t2, 0x9999999999999999\n" \
                   "\tli t4, 0x1111\n"
        asm_fence = "\tfence\n"
        asm_critical1 = "critical1:\n\tla s1, rvtest_data\n" \
                        "\tlb s2, 7(s1)\n\tfence\n\tlb s2, 0(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 7(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 0(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 6(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 1(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 5(s1)\n\tfence\n" \
                        "\tlb s2, 3(s1)\n\tfence\n\tlb s2, 2(s1)\n\tfence\n" \
                        "\tlb s2, 0(s1)\n\tfence\n\tlb s2, 7(s1)\n\tfence\n" \
                        "\tnop\n"
        asm_critical2 = "critical2:\n\tla s1, rvtest_data\n" \
                        "\tlh s2, 6(s1)\n\tfence\n\tlh s2, 0(s1)\n\tfence\n" \
                        "\tlh s2, 4(s1)\n\tfence\n\tlh s2, 2(s1)\n\tfence\n" \
                        "\tnop\n"
        asm_critical3 = "critical3:\n\tla s1, rvtest_data\n" \
                        "\tlw s2, 4(s1)\n\tfence\n\tlw s2, 0(s1)\n\tfence\n" \
                        "\tnop\n"
        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of asm.
        asm = "".join(asm_init) + asm_main + asm_fence + \
            asm_critical1 + asm_critical2 + asm_critical3 + asm_end
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
