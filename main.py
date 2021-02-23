#!/usr/bin/env python3 
#coding: utf-8

import serial, json, socket
from time import sleep

# tcp port
HOST = '127.0.0.1' 
PORT = 9090

# serial/com
SERIALPORT = '/dev/ttyACM2'
BAUDRATE = 115200
DELAY = 0.5

# defines
T_PULSE = 1
T_PRESSURE = 2
T_RSSI = 3

def send(jsn):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((HOST, PORT))
        s.sendall(jsn.encode())
    except socket.error:
        print('connection error')
    s.close


with serial.Serial(SERIALPORT, BAUDRATE, timeout=0) as ser:
    while (1):
        sleep(DELAY)
        msg_p = []
        msglen = b''
        msg = []
        while (ser.inWaiting() > 0):
            out = (ser.read(1)).hex()
            if (len(out) and not msglen):
                msglen = out
            msg.append(out)
        if (len(msg)):
            ret = {}
            msg_p = msg[0:int(msg[0])+1]
            #print(msg_p)
            if (int(msg_p[2]) == T_PULSE):
                ret['tag_id'] = int(msg_p[3]+msg_p[4], 16)
                ret['pulse'] = int(msg_p[5], 16)
            elif (int(msg_p[2]) == T_PRESSURE):
                ret['tag_id'] = int(msg_p[3]+msg_p[4], 16)
                ret['pressure_up'] = int(msg_p[5], 16)
                ret['pressure_down'] = int(msg_p[6], 16)
            elif (int(msg_p[2]) == T_RSSI):
                ret['beacon_id'] = int(msg_p[3]+msg_p[4], 16)
                ret['rssi'] = int.from_bytes(bytes.fromhex(msg_p[5]), byteorder='little', signed=True) 
                #ret['rssi'] = int(msg_p[5], 16) 
                ret['tag_id'] = int(msg_p[6]+msg_p[7], 16)
            jsn = json.dumps(ret)
            print(jsn) 
            send(jsn)

