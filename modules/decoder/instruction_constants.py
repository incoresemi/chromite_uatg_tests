base_reg_file = ['x' + str(s) for s in range(32)]

r_type32 = [
    'add', 'and', 'or', 'sll', 'slt', 'sltu', 'sra', 'srl', 'sub', 'xor'
]

r_type64 = r_type32 + ['addw', 'sllw', 'sraw', 'srlw', 'subw']

# instructions = ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra',
#                 'or', 'and', 'addw', 'subw', 'sllw', 'srlw', 'sraw']


def bit_walker(bit_width=8, n_ones=1, invert=False):
    """
    Returns a list of binary values each with a width of bit_width that
    walks with n_ones walking from lsb to msb. If invert is True, then list
    contains bits inverted in binary.

    :param bit_width: bit-width of register/value to fill.
    :param n_ones: number of ones to walk.
    :param invert: whether to walk one's or zeros
    :return: list of strings
    """
    if n_ones < 1:
        raise Exception('n_ones can not be less than 1')
    elif n_ones > bit_width:
        raise Exception(f'You cant store {hex((1 << n_ones) - 1)} '
                        f' in {bit_width} bits')
    else:
        walked = []
        temp = (1 << n_ones) - 1
        for i in range(bit_width):
            if temp <= (1 << bit_width) - 1:
                # binary = format(temp, f'0{bit_width}x')
                if not invert:
                    # walked.append(binary)
                    walked.append(hex(temp))
                elif invert:
                    # binary = format((temp ^ ((1 << bit_width)-1)),
                    #                 f'0{bit_width}x')
                    # walked.append(binary)
                    walked.append(hex(temp ^ ((1 << bit_width) - 1)))
                temp = temp << 1
            else:
                break
        return walked
