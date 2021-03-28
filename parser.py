import json

T_PULSE         = 1
T_PRESSURE      = 2
T_RSSI          = 3
T_SATURATION    = 4
T_ALL           = 5

def make_json(msg: dict) -> str:
        return json.dumps(msg)

def unique_lines(lines: list) -> list:
    return [list(x) for x in set(tuple(x) for x in lines)]

def make_lines(lines: list, unique=True):
    if (lines is None):
        return
    buff = []
    while (len(lines) > 0):
        buff.append(lines[:lines[0] + 1])
        del lines[:lines[0] + 1]
    if (unique):
        # remove same lines
        buff = (unique_lines(buff))
    return buff

def parse(lines: list):
    if (lines is None):
        return
    buff = []
    for line in lines:
        if (len(line) < 6):
            return
        ret = {}
        if (line[2] == T_PULSE and len(line) == 6):
            ret['tag_id']        = (line[3] << 8)+(line[4])
            ret['pulse']         = line[5]
        elif (line[2] == T_PRESSURE and len(line) == 7):
            ret['tag_id']        = (line[3] << 8)+(line[4])
            ret['pressure_up']   = line[5]
            ret['pressure_down'] = line[6]
        elif (line[2] == T_SATURATION and len(line) == 6):
            ret['tag_id']        = (line[3] << 8)+(line[4])
            ret['saturation']         = line[5]
        elif (line[2] == T_ALL and len(line) == 9):
            ret['tag_id']        = (line[3] << 8)+(line[4])
            ret['pulse']         = line[5]
            ret['saturation']    = line[6]
            ret['pressure_up']   = line[7]
            ret['pressure_down'] = line[8]
        elif (line[2] == T_RSSI and len(line) == 8):
            ret['beacon_id']     = (line[3] << 8)+(line[4])
            ret['rssi']          = line[5] - (1 << 8) # if line[5] & (1 << (8-1)):
            ret['tag_id']        = (line[6] << 8)+(line[7])
        if (ret):
            buff.append(ret)
    return buff