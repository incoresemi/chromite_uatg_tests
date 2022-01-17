# See LICENSE.incore for details
# Co-authored-by: Vishweswaran K <vishwa.kans07@gmail.com>

from yapsy.IPlugin import IPlugin

from typing import Dict, Union, Any, List
import random


class uatg_dcache_load_store_types(IPlugin):

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
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """
        - Perform a  `fence`  operation to clear out the data cache subsystem
        and the fill buffer.
        - `Store` a single `byte` using `sb` and `load` it back using `lbu`.
        - `Store` a `half word` using `sh` and `load` it back using `lhu`.
        - `Store` a `word` using `sw` and `load` it back using `lwu`
        - For the above three cases, the `load` should be identical to the
        store, as it is unsigned.
        - `Store` a `double word` using `sd` and `load` it back using `ld`
        - The following test cases are storing part of a double word where the
        remaining bits are set.
        - `Load` from the same locations again, but this time allow the data
        to be sign extented.
        - For the sign extended loads, compare with the sign extended versions
        of the test data.
        - Always branch out if the load is not equal.
        - `Store` a `double word` and then modify only half of it using `sw`,
        Then immediately `load` the entire `double word` and check if the
        modification has updated the value from the store buffer.

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
        for i in range(self._word_size * self._block_size * self._sets *
                       self._ways * 2):
            # We generate random 8 byte numbers.
            asm_data += f"\t.dword 0x{random.randrange(16 ** 16):8x}\n"

        asm_main = "\tfence\n\tli t1, 8000\n\tli t2, 0x9999999999999999\n" \
                   "\tli t4, 0x1111\n"
        asm_pass1 = f"pass1:\n\tli a2, 0x99\n" \
                    f"\tsb t2, {self._word_size * self._block_size * 1}(t1)\n" \
                    f"\tlbu t3, {self._word_size * self._block_size * 1}(t1)" \
                    "\n\tbne a2, t3, end\n"
        asm_pass2 = "pass2:\n\tli a2, 0x9999\n" \
                    f"\tsh t2, {self._word_size * self._block_size * 2}(t1)\n" \
                    f"\tlhu t3, {self._word_size * self._block_size * 2}(t1)" \
                    "\n\tbne a2, t3, end\n"
        asm_pass3 = f"pass3:\n\tli a2, 0x99999999\n" \
                    f"\tsw t2, {self._word_size * self._block_size * 3}(t1)\n" \
                    f"\tlwu t3, {self._word_size * self._block_size * 3}(t1)" \
                    f"\n\tbne a2, t3, end\n"
        asm_pass4 = "pass4:\n\tli a2, 0x9999999999999999\n" \
                    f"\tsd t2, {self._word_size * self._block_size * 4}(t1)\n" \
                    f"\tld t3, {self._word_size * self._block_size * 4}(t1)\n" \
                    f"\tbne a2, t3, end\n"
        asm_pass5 = f"pass5:\n\tli a2, 0xFFFFFFFFFFFFFF99\n" \
                    f"\tlb t3, {self._word_size * self._block_size * 1}(t1)\n" \
                    f"\tbne t3, a2, end\n"
        asm_pass6 = "pass6:\n\tli a2, 0xFFFFFFFFFFFF9999\n" \
                    f"\tlh t3, {self._word_size * self._block_size * 2}(t1)\n" \
                    f"\tbne t3, a2, end\n"
        asm_pass7 = "pass7:\n\tli a2, 0xFFFFFFFF99999999\n" \
                    f"\tlw t3, {self._word_size * self._block_size * 3}(t1)\n" \
                    f"\tbne t3, a2, end\n"
        asm_pass8 = "pass8:\n\tli a2, 0x9999999999999999\n\tld t3, {0}(t1)\n\
\tbne t3, a2, end\n".format(self._word_size * self._block_size * 4)
        asm_pass9 = "pass9:\n\tli a2, 0x9999999999999999\n\t"

        for i in range(7):
            asm_pass9 += f"lb s1, " \
                         f"{self._block_size * self._word_size * 4 + (8 * i)}" \
                         f"(t1)\n\tadd s6, s6, s1\n\tslli s6, s6, 8\n\t"
        asm_pass9 += f"lb s1, " \
                     f"{self._word_size * self._block_size * 4 + (8 * 7)}" \
                     f"(t1)\n\tadd s6, s6, s1\n\tbne s6, a2, end\n"

        asm_pass10 = "pass10:\n\tli a2, 0x9999999999999999\n\t"
        for i in range(3):
            asm_pass10 += f"lh s1, " \
                      f"{self._word_size * self._block_size * 4 + (16 * i)}" \
                      f"(t1)\n\tadd s6, s6, s1\n\tslli s6, s6, 16\n\t"
        asm_pass10 += f"lb s1," \
            f"{self._word_size * self._block_size * 4 + 16 * 3}(t1)\n" \
            f"\tadd s6, s6, s1\n\tbne s6, a2, end\n"

        asm_pass11 = f"pass11:\n\tli a2, 0x9999999999999999\n" \
                     f"\tlw s1, " \
                     f"{self._word_size * self._block_size * 4}(t1)\n" \
                     f"\tadd s6, s6, s1\n\tslli s6, s6, 32\n\tlw s1, " \
                     f"{(self._word_size * self._block_size * 4) + 32}(t1)\n" \
                     f"\tadd s6, s6, s1\n\tbne s6, s2, end\n"
        asm_pass12 = f"pass12:\n\tli a2, 0x9999999911119999\n\tsh t4, " \
                     f"{self._word_size * self._block_size + (8 * 4)}(t1)" \
                     f"\n\tld t3, {self._word_size * self._block_size}(t1)" \
                     f"\n\tbne t3, a2, end\n"
        asm_valid = "valid:\n\taddi x31, x0, 1\n"
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
        asm = asm_main + asm_pass1 + asm_pass2 + asm_pass3 + asm_pass4 + \
            asm_pass5 + asm_pass6 + asm_pass7 + asm_pass8 + asm_pass9 + \
            asm_pass10 + asm_pass11 + asm_pass12 + asm_valid + asm_fence + \
            asm_critical1 + asm_critical2 + asm_critical3 + asm_end
        compile_macros = []

        return [{
            'asm_code': asm,
            'asm_data': asm_data,
            'asm_sig': '',
            'compile_macros': compile_macros
        }]
