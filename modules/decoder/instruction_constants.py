base_reg_file = ['x' + str(s) for s in range(32)]

r_type32 = [
    'add', 'and', 'or', 'sll', 'slt', 'sltu', 'sra', 'srl', 'sub', 'xor'
]

r_type64 = r_type32 + ['addw', 'sllw', 'sraw', 'srlw', 'subw']


# instructions = ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra',
#                 'or', 'and', 'addw', 'subw', 'sllw', 'srlw', 'sraw']