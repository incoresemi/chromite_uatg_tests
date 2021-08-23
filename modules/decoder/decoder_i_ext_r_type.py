from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os

#TO-DO inst_list and reg_vals will come from instrcutions constants file
global inst_list, reg_vals

inst_list = [
    'add', 'and', 'or', 'sll', 'slt', 'sltu', 'sra', 'srl', 'sub', 'xor',
    'addw', 'sllw', 'sraw', 'srlw', 'subw'
    ]

reg_vals = ['x' + str(s) for s in range(32)]
 
class decoder_i_ext_r_type(IPlugin):

    def __init__(self):
        pass

    def execute(self, _null):
        return True

    def generate_asm(self):
        """
          Generates the ASM file containing R type instructions present in the I extension"""        
        asm = ''
        for inst in inst_list:
            for reg1 in reg_vals:
                for reg2 in reg_vals:
                    for reg3 in reg_vals:
                        asm = asm + f'{inst} {reg1}, {reg2}, {reg3}\n'
        
        return (asm)

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv
