from cocotb_coverage.coverage import *
from cocotb_coverage import crv
import cocotb
from utg.uarch_modules.modules.decoder.instruction_constants import r_type32, r_type64, base_reg_file
# from enum import Enum, IntEnum, unique, auto

instructions = r_type64

covered = []  # list to store already covered data
irs1_covered = []
irs2_covered = []
ird_covered = []
log = cocotb.logging.getLogger("cocotb.test")  # logger instance


class cdtg_randomized(crv.Randomized):

    def __init__(self):
        crv.Randomized.__init__(self)
        self.w = 'x0'  # rd
        self.x = 'x0'
        self.y = 'x0'
        self.z = 'add'
        self.add_rand('w', base_reg_file)
        self.add_rand('x', base_reg_file)
        self.add_rand('y', base_reg_file)
        self.add_rand('z', instructions)

        self.rd_not_cov = lambda w, z: (z, w) not in ird_covered
        self.rs1_ne_rs2 = lambda x, y: x != y
        self.rs1_ne_rd = lambda w, x: w != x
        self.rs2_ne_rd = lambda w, y: w != y
        self.rs1_not_cov = lambda x, z: (z, x) not in irs1_covered
        self.rs2_not_cov = lambda y, z: (z, y) not in irs2_covered

        # define hard constraint - do not pick items from the "covered" list
        self.add_constraint(lambda w, x, y, z: (z, w, x, y) not in covered and w
                            != y and x != y and x != w)
        # self.add_constraint(lambda x,z : (z, x) not in irs1_covered)
        # self.add_constraint(lambda y,z : (z.name, y) not in irs2_covered)

def gen():
    my_coverage = coverage_section(
        CoverPoint("top.rs1", xf=lambda obj: obj.x, bins=base_reg_file),
        CoverPoint("top.rs2", xf=lambda obj: obj.y, bins=base_reg_file),
        CoverPoint("top.rd", xf=lambda obj: obj.w, bins=base_reg_file),
        CoverPoint("top.instr", xf=lambda obj: obj.z, bins=instructions),
        CoverCross("top.seq1", items=["top.instr", "top.rs1"]),
        CoverCross("top.seq2", items=["top.instr", "top.rs2"]),
        CoverCross("top.seq3", items=["top.instr", "top.rd"]))

    @my_coverage
    def sample_coverage(obj):
        covered.append(
            (obj.z, obj.w, obj.x, obj.y))  # extend the list with sampled value
        irs1_covered.append(
            (obj.z, obj.x))  # extend the list with sampled value
        irs2_covered.append(
            (obj.z, obj.y))  # extend the list with sampled value
        ird_covered.append((obj.z, obj.w))

    obj = cdtg_randomized()
    cross_size = coverage_db["top.seq1"].size
    cross_coverage = coverage_db["top.seq1"].coverage

    # for _ in range(cross_size):
    while cross_size != cross_coverage:
        obj.randomize_with(obj.rs1_ne_rs2, obj.rs1_not_cov, obj.rs1_ne_rd)
        sample_coverage(obj)
        cross_coverage = coverage_db["top.seq1"].coverage

    #print(len(covered))

    cross_size = coverage_db["top.seq2"].size
    cross_coverage = coverage_db["top.seq2"].coverage
    while cross_size != cross_coverage:
        obj.randomize_with(obj.rs2_not_cov, obj.rs2_ne_rd)
        sample_coverage(obj)
        cross_coverage = coverage_db["top.seq2"].coverage

    #print(len(covered))

    cross_size = coverage_db["top.seq3"].size
    cross_coverage = coverage_db["top.seq3"].coverage

    # for _ in range(cross_size):
    while cross_size != cross_coverage:
        obj.randomize_with(obj.rd_not_cov)
        sample_coverage(obj)
        cross_coverage = coverage_db["top.seq3"].coverage

    #print(len(covered))
    covered.sort(key=lambda tup: tup[0])

    ret_str = ""

    #with open('insts.txt', 'w') as out:
    for i in covered:
        inst = str(i)[1:-1]
    #out.write(f'{i[0]} {i[1]}, {i[2]}, {i[3]}\n')
        ret_str += f'{i[0]} {i[1]}, {i[2]}, {i[3]}\n'

    coverage_db.report_coverage(log.info, bins=True)
    #coverage_db.export_to_yaml(filename="i_ext_r_type.yaml")
    # coverage_db.export_to_xml(filename="coverage.xml")
    return (ret_str)
