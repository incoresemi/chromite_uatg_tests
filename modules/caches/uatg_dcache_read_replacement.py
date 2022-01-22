# See LICENSE.incore for details

from yapsy.IPlugin import IPlugin

from typing import Dict, Union, Any, List
import random


class uatg_dcache_read_replacement(IPlugin):

    def __init__(self):
        super().__init__()
        self._replacement = None
        self._fb_size = None
        self._sets = 64
        self._word_size = 8
        self._block_size = 8
        self._ways = 4

    def execute(self, core_yaml, isa_yaml) -> bool:
        _dcache_dict = core_yaml['dcache_configuration']
        _dcache_en = _dcache_dict['instantiate']
        self._sets = _dcache_dict['sets']
        self._word_size = _dcache_dict['word_size']
        self._block_size = _dcache_dict['block_size']
        self._ways = _dcache_dict['ways']
        self._fb_size = _dcache_dict['fb_size']
        self._replacement = _dcache_dict['replacement']
        return _dcache_en

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        # asm_data is the test data that is loaded into memory.
        # We use this to perform load operations.
        data = random.randrange(0, 100)
        asm_data = f"\nrvtest_data:\n\t.align {self._word_size}\n"

        # We load the memory with data twice the size of our dcache.
        asm_data += f"\t.rept " + \
            f"{self._sets * self._word_size * self._block_size}\n" + \
            f"\t.dword 0x{random.randrange(16 ** 16):8x}\n" + f"\t.endr\n"

        asm_main = f"\tfence\n\tli t0, {data}\n" + \
                   f"\tli t3, {self._sets * self._ways}\n" + \
                   "\tla t2, rvtest_data\n\tla a2, rvtest_data\n"
        asm_lab1 = f"lab1:\n\tlw t0, 0(t2)\n" + \
                   f"\taddi t2, t2, {self._word_size * self._block_size}\n" + \
                   "\tbeq t4, t3, asm_nop\n\taddi t4, t4, 1\n\tj lab1\n"
        asm_nop = "asm_nop:\n"
        #initialise all registers to 0
        #assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1,32)]
        # Perform a series of NOPs to empty the fill buffer.
        for i in range(self._fb_size * 2):
            asm_nop += "\tnop\n"

        # Perform a serious of continuous store operations with
        # no window for an opportunistic release.
        asm_lw = "asm_lw:\n"
        for i in range(self._fb_size * 2):
            asm_lw += f"\tlw t0, {self._block_size * self._word_size * (i + 1)}"
            asm_lw += f"(t2)\n"

        asm_repl = f"repl:\n\tfence\n\tla t0, rvtest_data\n\tli t1, {data}\n"
        for i in range(self._ways + 1):
            asm_repl += \
                f"\tli t5, " \
                f"{self._sets * self._word_size * self._block_size * i}\n" \
                f"\tadd s{i}, t0, t5\n\tfence\n"

        if self._replacement == "RR":
            # the caches follow a round robin replacement policy
            for i in range(self._sets):
                asm_repl_mk_thrash = f"thrash_{i}:\n"
                asm_repl_mk_dirty = f"mkdirty_{i}:\n"
                asm_repl_next_set = f"next_set_{i}:\n"
                # increment the 12th bit, keeping all lower bits the same
                j = 0
                for j in range(self._ways):
                    asm_repl_mk_dirty += f"\tsw t1, 0(s{j})\n"
                    asm_repl_mk_thrash += f"\tlw t5, 0(s{j})\n"
                # cause an eviction
                asm_repl_mk_dirty += f"evict_{i}:\n\tsw t1, 0(s{j + 1})\n"
                for j in range(self._ways + 1):
                    # load the lines that are being evicted
                    # while theyre being evicted
                    asm_repl_next_set += f"\taddi s{j}, s{j}, " \
                                         f"{self._word_size * self._block_size}\n"
                asm_repl += asm_repl_mk_dirty + asm_repl_mk_thrash + \
                            asm_repl_next_set
        if self._replacement == "PLRU":
            # the caches are following a pseudo random replacement algorithm
            for i in range(self._sets):
                asm_repl_mk_thrash = f"thrash_{i}:\n"
                asm_repl_mk_dirty = f"mkdirty_{i}:\n"
                asm_repl_next_set = f"next_set_{i}:\n"
                asm_repl_ch_order = f"ch_order_{i}:\n"
                asm_repl_mk_evict = \
                    f"evict_{i}:\n\tsw t1, 0(s{self._ways + 1})\n"
                # cause an eviction
                repl_ch_order = list(range(self._ways))
                random.shuffle(repl_ch_order)
                # change the lru order by performing loads
                for j in range(self._ways):
                    asm_repl_mk_dirty += f"\tsw t1, 0(s{j})\n"
                for k in repl_ch_order:
                    asm_repl_ch_order += f"\tlw t5, 0(s{k})\n"
                for k in repl_ch_order:
                    asm_repl_mk_thrash += f"\tlw t5, 0(s{k})\n"
                for j in range(self._ways + 1):
                    # load the lines that are being evicted
                    # while they're being evicted
                    asm_repl_next_set += \
                        f"\taddi s{j}, s{j}, " \
                        f"{self._word_size * self._block_size}\n"
                asm_repl += asm_repl_mk_dirty + asm_repl_ch_order + \
                            asm_repl_mk_evict + asm_repl_mk_thrash + asm_repl_next_set
        asm_end = "end:\n\tnop\n\tfence.i\n"

        # Concatenate all pieces of ASM.
        asm = "".join(asm_init) + asm_main + asm_lab1 + asm_nop + asm_lw + asm_repl + asm_end
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
