# python program to generate an assembly file which checks if mis-predictions
# occur In addition to this, the GHR is also filled with ones (additional
# test case) uses assembly macros

# TODO -> Format the file!
#  Create another function which prints the includes and other
# assembler directives complying to the test format spec

from yapsy.IPlugin import IPlugin
from typing import Dict, List, Union, Any


class uatg_decompressor_02(IPlugin):

    def __init__(self):
        super().__init__()
        self.isa = "RV64I"
        self.split_isa = "RV64I"

    def execute(self, core_yaml, isa_yaml):
        self.isa = isa_yaml['hart0']['ISA']
        self.split_isa = self.isa.split('Z')

        self.modes = ['machine']

        if 'S' in self.isa:
            self.modes.append('supervisor')
        if 'S' in self.isa and 'U' in self.isa:
            self.modes.append('user')

        if 'C' in self.isa:
            return True
        else:
            return False

    def generate_asm(self) -> List[Dict[str, Union[Union[str, list], Any]]]:
        """This function will return all the compressed_RV32 instructions"""
        
        return_list = []

        asm = ""

        for mode in self.modes:
            
            asm = f"LI x2, MSTATUS_FS;\n" \
                  f"csrrs x3, mstatus,x0;\n" \
                  f"or x2, x3, x2;\n" \
                  f"csrrw x0,mstatus,x2;\n"

            asm += f'\n\n## test: decompressor_RV32 ##\n\n'

            if 'RV32' and 'F' in self.split_isa[0]:
                asm += f"###register based load and store###\n" \
                       f"###stack pointer based load and store floating point " \
                       f"instructions(RV32 only)###\n" \
                       f"LA(x2,sample_data)\n" \
                       f"c.fswsp f8,4(x2)\n" \
                       f"c.flwsp f9,4(x2)\n\n" \
                       f"### register based load amd store floating point " \
                       f"instructions (RV32 only) ###\n" \
                       f"LA(x10,sample_data)\n" \
                       f"c.fsw f11,4(x10)\n" \
                       f"LA(x9,sample_data)\n" \
                       f"c.flw f12,4(x9)\n\n"

            if 'RV32' in self.split_isa[0]:
                asm += f"### control transfers instructions(RV32 only) ###\n" \
                       f"LA (x29,entry_jal)\n" \
                       f"c.jal x29\n\n" \
                       f"entry_jal:\n" \
                       f"c.srai x9,5      ## x9=x9>>5\n\n"

            asm += f"### integer register-immediate operations###\n" \
                   f"c.srli x15,1       ## x15=x15>>1\n" \
                   f"c.srai x8,4        ## x8=x8arith>>4\n" \
                   f"c.slli x5,1        ## x5=x5<<1\n" \
                   f"LA (x28,entry_jalr)\n" \
                   f"c.jalr x28\n\n" \
                   f"entry_jalr:\n" \
                   f"c.srli x10,5      ## x10=x10<<5\n\n" \

            if 'F' in self.split_isa[0]:
                asm += f"###stack pointer based load and store instructions" \
                       f"(RV32/RV64)###\n" \
                       f"LA (x2, sample_data)\n" \
                       f"c.fsdsp f8,8(x2)\n" \
                       f"c.fldsp f12,8(x2)\n\n###register based load and " \
                       f"store instructions(RV32/RV64)###" \
                       f"LA (x10,sample_data)\n " \
                       f"c.fsd f11,8(x10)\n" \
                       f"LA (x12,sample_data)\n" \
                       f"c.fld f9,8(x12)\n\n"

            asm += f"###Integer Constant-Generation Instructions###\n" \
                   f"c.li x1,1   ## x1=1\n" \
                   f"c.li x2,2   ## x2=2\n" \

            for loop_var in range(3, 32):
                asm += f"c.lui x{loop_var},{loop_var}  ## x{loop_var}={loop_var}\n"

            asm += f"\n##Integer Register-Register Operations##\n" \
                   f"c.mv x16,x17   ## x16=17\n" \
                   f"c.add x18,x19  ## x18=x18+x19\n" \
                   f"c.and x8,x9    ## x8=x8&x9\n" \
                   f"c.or  x9,x10   ## x9=x9|x10\n" \
                   f"c.xor x10,x11  ## x10=x10^x11\n" \
                   f"c.sub x11,x12  ## x11=x11-x12\n" \
                   f"c.addw x12,x13 ## x12=x12+x13\n" \
                   f"c.subw x13,x14 ## x13=x13+14\n" \
                   f"##control transfer instructions##\n" \
                   f"c.li x15,0             ## x15=0\n" \
                   f"c.beqz x15, entry1 \n" \
                   f"c.bnez x14,entry2 \n" \
                   f"c.j entry3\n\n" \
                   f"entry1: c.li x15,2    ##x15=2\n\n" \
                   f"entry2: c.li x14,0\n\n" \
                   f"entry3:\n" \
                   f"c.add x9,x10    ## x9=x9+x10\n" \
                   f"c.sub x10,x9    ## x10=x10-x9\n\n" \
                   f"LA (x28, entry_jr)\n" \
                   f"c.jr x28\n\n" \
                   f"entry_jr:\n" \
                   f"c.add x9,x10\n" \
                   f"c.nop\n\n" \
            
            # trap signature bytes
            trap_sigbytes = 24
            trap_count = 0

            # initialize the signature region
            sig_code = 'mtrap_count:\n'
            sig_code += ' .fill 1, 8, 0x0\n'
            sig_code += 'mtrap_sigptr:\n'
            sig_code += ' .fill {0},4,0xdeadbeef\n'.format(
                int(trap_sigbytes / 4))

            # compile macros for the test
            if mode != 'machine':
                compile_macros = ['rvtest_mtrap_routine','s_u_mode_test'] 
            else:
                compile_macros = []

            # user can choose to generate supervisor and/or user tests in addition
            # to machine mode tests here.
            privileged_test_enable = True

            privileged_test_dict = {
                'enable': privileged_test_enable,
                'mode': mode,
                'page_size': 4096,
                'paging_mode': 'sv39',
                'll_pages': 64,
            }

            return_list.append({
                'asm_code': asm,
                'asm_sig': sig_code,
                'compile_macros': compile_macros,
                'privileged_test': privileged_test_dict,
                'docstring': 'This test fills ghr register with ones',
                'name_postfix': mode
            })

            if not privileged_test_enable:
                yield return_list

        yield return_list

    def check_log(self):
        return None

    def generate_covergroups(self, config_file):
        """
           returns the covergroups for this test
        """
        config = config_file
        fn_decompress_inst = config['decompressor']['input'][
            'decompressor_input']
        sv = f"""covergroup mkstage1_32_cg @(posedge CLK);\n
                option.per_instance=1;
///coverpoint label can be any name that  relates the signal
  {fn_decompress_inst}_cp : coverpoint {fn_decompress_inst}"""
        sv += "{\n"
        sv = sv + """  wildcard bins ILLEGAL    	       = {16'b0}; \n
  wildcard bins C_ADDI4SPN 	       = {16'b000_xxxxxxxx_xxx_00};//(RES, nzuimm=0) \n
  //wildcard bins C_ADDI4SPN_RESERVED  = {16'b000_00000000_xxx_00};\n
  wildcard bins C_FLD	               = {16'b001_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_LW 	               = {16'b010_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_FSD	               = {16'b101_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_SW	               = {16'b110_xxx_xxx_xx_xxx_00};\n
  //wildcard bins RESERVED             = {16'b100_xxxxxxxx_xxx_00};\n
  `ifdef RV32\n
  wildcard bins C_FSW	               = {16'b111_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_FLW	               = {16'b011_xxx_xxx_xx_xxx_00};\n
  `endif\n
  `ifdef RV64\n
  wildcard bins C_SD	               = {16'b111_xxx_xxx_xx_xxx_00};\n
  wildcard bins C_LD	 	       = {16'b011_xxx_xxx_xx_xxx_00};\n
  `endif\n
  //---RVC, Quadrant 1 instructions----//\n
 
  wildcard bins C_NOP	              = {16'b000_x_00000_xxxxx_01};//(HINT, nzimm! = 0)\n
  wildcard bins C_ADDI	              = {16'b000_x_xxxxx_xxxxx_01} iff (fn_decompress_inst[11:7]!=5'b0);//(HINT, nzimm = 0)\n
  wildcard bins C_LI	              = {16'b010_x_xxxxx_xxxxx_01} iff (fn_decompress_inst[11:7]!=5'b0);//(HINT, rd=0)\n
  wildcard bins C_ADDI16SP            = {16'b011_x_00010_xxxxx_01} ;//(RES, nzimm=0)\n
  //illegal_bins C_ADDI16SP_RESERVED  = {16'b011_0_00010_00000_01} ;//(RES, nzimm=0)\n
  wildcard bins C_LUI                 = {16'b011_x_xxxxx_xxxxx_01} iff (fn_decompress_inst[11:7]!=5'b0 && fn_decompress_inst[11:7]!=5'd2);//(RES, nzimm=0; HINT, rd=0)\n
  //wildcard bins C_LUI_RESERVED      = {16'b011_0_xxxxx_00000_01} iff (fn_decompress_inst[11:7]!=5'b0 && fn_decompress_inst[11:7]!=5'd2);//(RES, nzimm=0; HINT, rd=0)\n
  wildcard bins C_ANDI	      	      = {16'b100_x_10_xxx_xxxxx_01};\n
  wildcard bins C_SUB	 	      = {16'b100_0_11_xxx_00_xxx_01};\n
  wildcard bins C_XOR	              = {16'b100_0_11_xxx_01_xxx_01};\n
  wildcard bins C_OR	              = {16'b100_0_11_xxx_10_xxx_01};\n
  wildcard bins C_AND	              = {16'b100_0_11_xxx_11_xxx_01};\n
  wildcard bins C_J	              = {16'b101_x_xx_xxx_xx_xxx_01};\n
  wildcard bins C_BEQZ                = {16'b110_xxx_xxx_xxxxx_01};\n
  wildcard bins C_BNEZ	              = {16'b111_xxx_xxx_xxxxx_01};\n
  //wildcard bins C_SRLI64	      = {16'b100_0_00_xxx_00000_01};//(RV128; RV32/64 HINT)\n
  //wildcard bins C_SRAI64	      = {16'b100_0_01_xxx_00000_01};//(RV128; RV32/64 HINT)\n
  //wildcard bins RESERVED_1	      = {16'b100_1_11_xxx_10_xxx_01};\n
  //wildcard bins RESERVED_2          = {16'b100_1_11_xxx_11_xxx_01};\n
  `ifdef RV32\n
  wildcard bins C_JAL	              = {16'b001_xxxxxxxxxxx_01};//(RV32)\n
  wildcard bins C_SRLI	              = {16'b100_1_00_xxx_xxxxx_01};//(RV32 Custom, nzuimm[5]=1) //change\n
  //illegal_bins C_SUBW_RESERVED      = {16'b100_1_11_xxx_00_xxx_01};//(RV64/128; RV32 RES)\n
  //illegal_bins C_ADDW_RESERVED      = {16'b100_1_11_xxx_01_xxx_01};//(RV64/128; RV32 RES)\n
  wildcard bins C_SRAI	              = {16'b100_1_01_xxx_xxxxx_01};//(RV32 Custom, nzuimm[5]=1)\n
  `endif\n
  `ifdef RV64\n
  wildcard bins C_ADDIW	              = {16'b001_x_xxxxx_xxxxx_01} iff (fn_decompress_inst[11:7]!=5'b0);//(RV64/128; RES, rd=0)\n
  //wildcard bins C_ADDIW_RESERVED    = {16'b001_x_xxxxx_xxxxx_01} iff (fn_decompress_inst[11:7]==5'b0);//(RV64/128; RES, rd=0)\n
  wildcard bins C_SUBW	              = {16'b100_1_11_xxx_00_xxx_01};//(RV64/128; RV32 RES)\n
  wildcard bins C_ADDW	              = {16'b100_1_11_xxx_01_xxx_01};//(RV64/128; RV32 RES)\n
  `endif\n

  //---RVC, Quadrant 2 instructions---//\n
  //wildcard bins C_SLLI64	      = {16'b000_0_xxxxx_00000_10} iff (fn_decompress_inst[11:7]!=5'b0); //(RV128; RV32/64 HINT; HINT, rd=0)\n
  wildcard bins C_FLDSP	              = {16'b001_x_xxxxx_xxxxx_10}; //( RV32/64)\n
  wildcard bins C_LWSP	              = {16'b010_x_xxxxx_xxxxx_10}  iff (fn_decompress_inst[11:7]!=5'b0); //(RES,rd=0)\n
  //wildcard bins C_LWSP_RESERVED     = {16'b010_x_xxxxx_xxxxx_10}  iff (fn_decompress_inst[11:7]==5'b0); //(RES,rd=0)\n
  wildcard bins C_JR	              = {16'b100_0_xxxxx_00000_10}  iff (fn_decompress_inst[11:7]!=5'b0); //(RES,rs1=0)\n
  //wildcard bins C_JR_RESERVED	      = {16'b100_0_xxxxx_00000_10}  iff (fn_decompress_inst[11:7]==5'b0); //(RES,rs1=0)\n
  wildcard bins C_MV	 	      = {16'b100_0_xxxxx_xxxxx_10}  iff (fn_decompress_inst[11:7]!=5'b0 && (fn_decompress_inst[6:2]!=5'b0) ); //(HINT, rd=0)\n
  wildcard bins C_EBREAK	      = {16'b100_1_00000_00000_10};\n
  wildcard bins C_JALR	              = {16'b100_1_xxxxx_00000_10}  iff (fn_decompress_inst[11:7]!=5'b0);\n
  wildcard bins C_ADD	              = {16'b100_1_xxxxx_xxxxx_10}  iff (fn_decompress_inst[11:7]!=5'b0 && (fn_decompress_inst[6:2]!=5'b0) );//(HINT, rd=0)\n
  wildcard bins C_FSDSP	              = {16'b101_xxxxxx_xxxxx_10};//(RV32/64)\n
  wildcard bins C_SWSP	              = {16'b110_xxxxxx_xxxxx_10};//(RV32/64)\n
  `ifdef RV32	\n

  wildcard bins C_SLLI	              = {16'b000_x_xxxxx_xxxxx_10} iff (fn_decompress_inst[11:7]!=5'b0);//(HINT, rd=0; RV32 Custom, nzuimm[5]=1)\n
  wildcard bins C_FLWSP	              = {16'b011_x_xxxxx_xxxxx_10};//(RV32)\n
  wildcard bins C_FSWSP	              = {16'b11_xxxxxx_xxxxx_10};//(RV32)\n
  `endif\n

   `ifdef RV64	\n
   wildcard bins C_LDSP	              = {16'b011_x_xxxxx_xxxxx_10} iff (fn_decompress_inst[11:7]!=5'b0);//(RV64/128; RES, rd=0)\n
   //wildcard bins C_LDSP_RESERVED    = {16'b011_x_xxxxx_xxxxx_10} iff (fn_decompress_inst[11:7]==5'b0);//(RV64/128; RES, rd=0)\n
   wildcard bins C_SDSP	              = {16'b111_xxxxxx_xxxxx_10};//(RV64/128)\n
   `endif\n}\nendgroup\n\n"""

        return sv
