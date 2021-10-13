# python program to generate an assembly file which checks if mis-predictions
# occur In addition to this, the GHR is also filled with ones (additional
# test case) uses assembly macros

# To-Do -> Create another function which prints the includes and other
# assembler directives complying to the test format spec
from yapsy.IPlugin import IPlugin
from typing import Dict, List


class uatg_decompressor_floating_01(IPlugin):

    def __init__(self):
        super().__init__()
        self.isa = "RV64I"
        self.split_isa = "RV64I"


    def execute(self, _bpu_dict):
        self.isa = (_bpu_dict['isa']).lower()
        # we split the ISA based on Z because, we are checking for 
        # 'C' and 'F' standard extensions. When Zifencei or Zicsr are
        # enabled, the test using 'in' keyword will not return the expected
        # result.
        self.split_isa = self.isa.split('z')
        if 'c' and 'f' in self.split_isa[0]:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, str]]:
        """This function will return all the compressed instructions"""
        asm = """#define RVTEST_FP_ENABLE()
    LI x2, MSTATUS_FS;
    csrrs x3, mstatus,x0;
    or x2, x3, x2;
    csrrw x0,mstatus,x2;"""
        asm += "\n\n## test: floating ##\n\n"
        asm += "###Integer Constant-Generation Instructions###"
        asm += "###Floating Point and Stack Pointer Based Load and Store####"
        asm += """\nLA (x2,sample_data)
c.fsdsp f8,8(x2)
c.fldsp f12,8(x2)
###Floating Point Load and Store####
LA (x10,sample_data)
c.fsd f11,8(x10)
LA (x12,sample_data)
c.fld f9,8(x12)
"""
        return [{'asm_code': asm}]

    def check_log(self):
        return None

    def generate_covergroups(self, config_file):
        """
           returns the covergroups for this test
        """
        config = config_file
        fn_decompress_inst = config['decompressor']['input'][
            'decompressor_input']
        sv = f"""covergroup floating_point_cg @(posedge CLK);\n
                option.per_instance=1;
///coverpoint for floating point instructions
floating_point_cp : coverpoint {fn_decompress_inst}"""
        sv += "{\n"
        sv += """  wildcard bins C_FLDSP 	= {16'b001_x_xxxxx_xxxxx_10};\n
  wildcard bins C_FSDSP	= {16'b101_xxxxxx_xxxxx_10};\n
  wildcard bins C_FLD	= {16'b001_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_FSD	= {16'b101_xxx_xxx_xx_xxx_00};\n
  }  
endgroup\n"""

        return sv
