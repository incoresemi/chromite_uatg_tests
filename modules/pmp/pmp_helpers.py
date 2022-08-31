import itertools
from riscv_config.warl import warl_class

def get_pmp_reg_index(pmpentry,xlen):
    reg = 'pmpcfg'+str(int((pmpentry/(xlen/8)) * (xlen/32)))
    shamt = int(pmpentry%(xlen/8)) * 8
    return reg, shamt

mode_off = 0
mode_tor = 1
mode_na4 = 2
mode_napot = 3

enc_mode = {"OFF": 0, "TOR": 1, "NA4": 2, "NAPOT": 3}

def get_mode(mode):
    return enc_mode[mode.toupper()]

def get_addr_mask(mode, size):
    if mode == mode_napot:
        mask = size-1
        return f' & ~{size} | {mask}'
    elif mode == mode_tor:
        return f'+ {size}'
    else:
        return ''

def cfg(read, write, execute, lock, mode):
    cfg = mode << 3
    if read:
        cfg |= 1
    if write:
        cfg |= 2
    if execute:
        cfg |= 4
    if lock:
        cfg |= 1<<7
    return cfg

def reset_pmp(entry, treg, xlen):

    reg, shamt = get_pmp_reg_index(entry, xlen)
    cfg_val = 0 << shamt
    mask = ((2**8)-1) << shamt
    addr_reg = 'pmpaddr'+str(entry)
    code = f'\nli {treg}, {mask};\ncsrrc x0, {reg}, {treg};\nli {treg}, 0;\ncsrw {addr_reg}, {treg};\n'
    return code

def config_pmp(entry, treg1, treg2, addr, cfg, xlen, label):

    if label:
        linst = 'la'
        shinst = f'srli {treg1}, {treg1}, 2;\n'
    else:
        linst = 'li'
        shinst = ''
    reg, shamt = get_pmp_reg_index(entry, xlen)
    cfg_val = cfg << shamt
    addr_reg = 'pmpaddr'+str(entry)
    mask = ((2**8)-1) << shamt
    code = f'\n li {treg1}, ~{mask};\ncsrr {treg2}, {reg};\n and {treg2},{treg2},{treg1}\n'\
            f'li {treg1}, {cfg_val};\n or {treg1}, {treg1}, {treg2};\n'\
            f'csrw {reg}, {treg1};\n{linst} {treg1},{addr};\
\n{shinst}csrw {addr_reg}, {treg1};\n'
    return code

def get_xlen(yaml, hart='hart0'):
    return max(yaml[hart]['supported_xlen'])

def is_pmp_present(yaml,hart='hart0'):
    present = False
    return yaml[hart]['pmpaddr0']['rv'+str(get_xlen(yaml))]['accessible']

def get_valid_pmp_entries(yaml,hart='hart0'):
    node = 'rv'+str(get_xlen(yaml,hart))
    legal_list = []
    for i in range(64):
        if yaml[hart]['pmpaddr'+str(i)][node]['accessible']:
            legal_list.append(i)
    return legal_list

def get_legal_modes(yaml,entry,hart='hart0'):
    legal_list = []
    reg,_ = get_pmp_reg_index(entry,get_xlen(yaml,hart))
    node = yaml[hart][reg]['rv'+str(get_xlen(yaml,hart))][f'pmp{entry}cfg']
    depend = { f'pmp{entry}cfg': (yaml[hart][reg]['reset-val']>>node['lsb'])&((2**node['msb'])-1)}
    if 'warl' in node['type']:
        var = list(itertools.product([True,False], [True,False], [True,False], [False]))
        field = warl_class(node['type']['warl'],f'pmp{entry}cfg',node['msb'],node['lsb'])
        for i in range(1,4):
            if any([len(field.islegal(cfg(x[0],x[1],x[2],x[3],i), dependency_vals=depend))==0 for x in var]):
                legal_list.append(i)
    else:
        legal_list.append((node['type']['ro_constant']&(3<<3)) >> 3)
    return legal_list
