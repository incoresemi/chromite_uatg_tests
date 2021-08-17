from yapsy.IPlugin import IPlugin
from ruamel.yaml import YAML
import uarch_test.regex_formats as rf
import re
import os
from uarch_test.uarch_modules.modules.decoder.i_ext_r_type import gen

class decoder_i_ext_r_type(IPlugin):

    def __init__(self):
        pass

    def execute(self, _null):
        return True

    def generate_asm(self):
        """
          Generates the ASM file containing R type instructions present in the I extension
        """
        asm = gen()
        print("asm_gen")
        return(asm)

    def check_log(self, log_file_path, reports_dir):
        return None

    def generate_covergroups(self, config_file):
        sv = ""
        return sv

if __name__=="__main__":
    s = decoder_i_ext_r_type()
    print(s.generate_asm())
