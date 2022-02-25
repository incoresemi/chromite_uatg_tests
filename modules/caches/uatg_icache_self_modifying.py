# See LICENSE.incore for details

from typing import Dict, Union, Any, List

from yapsy.IPlugin import IPlugin


class uatg_icache_self_modifying(IPlugin):

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
        """The code modifies itself to change the first instruction from
        loading data into t0 to fence.i This causes the branch which missed
        the first time to happen and branch to first instruction which failed
        the last time."""

        # t0 = starting address
        # t1 = exit address
        # t2 = exit - starting address
        # t3 = jump opcode to be written in t0
        # t4 = temporary values
        # initialise all registers to 0
        # assumes x0 is zero
        asm_init = [f"\tmv x{i}, x0\n" for i in range(1, 32)]
        asm = ".option norvc\nbegin:\n\tla t0, begin\n\tbeqz t0, begin\n\t" \
              "la t1, exit\n\tsub t2, t1, t0\n\tli t3, 0x06f\n"
        # 20th bit of t2 to 32nd bit of t3
        asm += "\tli t4, 0x100000\n\tand t4, t4, t2\n\tslli t4, t4, 11\n\t" \
               "or t3, t3, t4\n"
        # 10-1 bit of t2 to 31-22 bit of t3
        asm += "\tli t4, 0x7fe\n\tand t4, t4, t2\n\tslli t4, t4, 20\n\t" \
               "or t3, t3, t4\n"
        # 11th bit of t2 to 21th bit of t3
        asm += "\tli t4, 0x800\n\tand t4, t4, t2\n\tslli t4, t4, 9\n\t" \
               "or t3, t3, t4\n"
        # 19-12 bit of t2 to 20-13 bit of t2
        asm += "\tli t4, 0xff000\n\tand t4, t4, t2\n\tslli t4, t4, 0\n\t" \
               "or t3, t3, t4\n"
        # writing t3 at location t0
        asm += "\tsw t3, 0(t0)\n\tfence.i\n\tnop\n\tnop\n\tnop\n\tnop\n\tnop" \
               "\n\tj begin\nexit:\n\tfence.i\n"

        yield ({
            'asm_code': "".join(asm_init) + asm,
            'asm_sig': '',
            'compile_macros': []
        })

    def check_log(self, log_file_path, reports_dir):
        """
        
        """

    def generate_covergroups(self, config_file):
        """

        """
