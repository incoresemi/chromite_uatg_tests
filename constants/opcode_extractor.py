def fill_tup(tup):
    # helper function to return a binary number of fixed width
    return bin(tup[2])[2:].zfill(tup[1] - tup[0] + 1)


def fill_range(ind_ranges):
    # Function to frame the 32 bit opcode from the range details
    ind_ranges.sort(key=lambda x: x[0])
    op = ['x'] * 32
    for i in ind_ranges:
        op[i[0]:i[1] + 1] = list(fill_tup(i))
    return ''.join(op[::-1])


def main():
    # read the file from riscv-opcodes
    f = open('opcodes-rv32i', 'r')
    lines = f.readlines()
    f.close()

    # open the file to write the instructions
    f = open('rv32i-insts.txt', 'w')
    for line in lines:
        if line[0] == '#' or line[0] == '\n':
            # ignore unnecessary lines
            pass
        else:
            temp = line.split()
            inst = temp.pop(0)  # take out the instruction alone
            temp.sort()
            ranges = []
            for i in temp:
                # extract the constant data fields alone
                if i[0].isnumeric():
                    [end, beg] = i.split('..')
                    [beg, val] = beg.split('=')
                    beg, end, val = int(beg), int(end), int(val, 16)
                    # append the details to a list of tuples.
                    ranges.append((beg, end, val))
                else:
                    break
            f.write("{0:<8} {1}\n".format(inst, fill_range(ranges)))
    f.close()
